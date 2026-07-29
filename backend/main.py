"""
Opus Hospital - AI 智能櫃台系統 Backend
支援繁體中文、台語、英語的即時對話系統
"""

import asyncio
import base64
import json
import uuid
import sys
from typing import Dict, Optional, List
from datetime import datetime

# Fix Unicode encoding for Windows with CJK paths
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import torch

from models.stt_model import STTModel
from models.llm_model import LLMModel
from models.tts_model_bluemagpie import TTSModelBlueMagpie as TTSModel
from utils.audio_processor import AudioProcessor
from utils.vad import VoiceActivityDetector
from utils.config import load_config
from utils.session_manager import SessionManager

# Initialize FastAPI app
app = FastAPI(
    title="Opus Hospital AI Reception",
    description="AI-powered hospital reception system with real-time voice interaction",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
config = load_config()
session_manager = SessionManager()
audio_processor = AudioProcessor(config)
vad = VoiceActivityDetector(config)

# Model instances (lazy loaded)
stt_model: Optional[STTModel] = None
llm_model: Optional[LLMModel] = None
tts_model: Optional[TTSModel] = None


@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    global stt_model, llm_model, tts_model
    
    logger.info("🚀 Starting Opus Hospital AI Reception System...")
    
    # Log environment
    import os
    env = os.getenv("OPUS_ENV", "development")
    logger.info(f"Environment: {env}")
    
    # Check GPU availability
    if torch.cuda.is_available():
        logger.info(f"✅ GPU detected: {torch.cuda.get_device_name(0)}")
        logger.info(f"💾 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    else:
        logger.warning("⚠️ No GPU detected, running on CPU (will be slow)")
    
    # Load models
    logger.info("📦 Loading AI models...")
    
    try:
        # STT Model
        logger.info("Loading STT (Qwen3-ASR-1.7B)...")
        stt_model = STTModel(config)
        await stt_model.load()
        logger.info("✅ STT model loaded")
        
        # LLM Model
        logger.info("Loading LLM (TAIDE-2.0-70B)...")
        llm_model = LLMModel(config)
        await llm_model.load()
        logger.info("✅ LLM model loaded")
        
        # TTS Model
        logger.info(f"Loading TTS ({config.models.tts})...")
        tts_model = TTSModel(config)
        await tts_model.load()
        logger.info("✅ TTS model loaded")
        
        logger.info("🎉 All models loaded successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to load models: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down Opus Hospital AI Reception System...")
    
    # Cleanup sessions
    await session_manager.cleanup_all()
    
    # Unload models
    if stt_model:
        await stt_model.unload()
    if llm_model:
        await llm_model.unload()
    if tts_model:
        await tts_model.unload()
    
    logger.info("👋 Shutdown complete")


from fastapi.responses import JSONResponse, HTMLResponse

@app.get("/")
async def root():
    """Root endpoint - redirect to frontend"""
    html_content = """
    <html>
        <head>
            <title>Opus Hospital AI</title>
            <meta http-equiv="refresh" content="0; url=http://localhost:5173" />
            <style>
                body { font-family: system-ui, -apple-system, sans-serif; text-align: center; padding-top: 100px; background-color: #f3f4f6; color: #1f2937; }
                .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                a { display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; }
                a:hover { background-color: #2563eb; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Opus Hospital AI Backend</h1>
                <p>The backend API service is running successfully.</p>
                <p>You are looking at the API server port (8000). The user interface is running on a different port (5173).</p>
                <a href="http://localhost:5173">Go to Frontend Web UI</a>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health_check():
    """Detailed health check"""
    gpu_info = {}
    if torch.cuda.is_available():
        gpu_info = {
            "name": torch.cuda.get_device_name(0),
            "memory_allocated": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f} GB",
            "memory_reserved": f"{torch.cuda.memory_reserved(0) / 1024**3:.2f} GB",
            "memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB",
        }
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "models_loaded": all([
            stt_model and stt_model.is_loaded,
            llm_model and llm_model.is_loaded,
            tts_model and tts_model.is_loaded,
        ]),
        "active_sessions": session_manager.get_active_session_count(),
        "gpu": gpu_info,
    }


@app.websocket("/ws/conversation")
async def websocket_conversation(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time voice conversation
    
    Message format:
    Client -> Server:
    {
        "type": "audio_chunk" | "interrupt" | "config",
        "data": "base64_audio",  # for audio_chunk
        "language": "zh-tw" | "nan" | "en",  # 繁中 | 台語 | 英語
        "timestamp": 1234567890
    }
    
    Server -> Client:
    {
        "type": "transcript" | "response_audio" | "status" | "error",
        "data": "base64_audio",  # for response_audio
        "text": "transcribed/generated text",
        "language": "zh-tw",
        "emotion": "friendly",
        "timestamp": 1234567890
    }
    """
    
    session_id = str(uuid.uuid4())
    await websocket.accept()
    
    logger.info(f"🔌 New WebSocket connection: {session_id}")
    
    # Create session
    session = await session_manager.create_session(session_id)
    
    # Audio buffers
    audio_buffer = bytearray()
    is_speaking = False
    language = "zh-tw"  # Default language
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "status",
            "message": "connected",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Main conversation loop
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            timestamp = message.get("timestamp", datetime.now().timestamp())
            
            # Handle different message types
            if msg_type == "audio_chunk":
                # Receive audio chunk from client
                audio_data = base64.b64decode(message.get("data", ""))
                language = message.get("language", "zh-tw")
                
                # Add to buffer
                audio_buffer.extend(audio_data)
                
                # VAD: Check if speech is detected
                if vad.is_speech(audio_data):
                    if not is_speaking:
                        logger.debug(f"🎤 Speech started - Session: {session_id}")
                        is_speaking = True
                        await websocket.send_json({
                            "type": "status",
                            "message": "listening",
                            "timestamp": datetime.now().isoformat()
                        })
                else:
                    if is_speaking and len(audio_buffer) > 0:
                        # End of speech detected, process the audio
                        logger.debug(f"✋ Speech ended - Session: {session_id}")
                        is_speaking = False
                        
                        # Process the complete utterance
                        await process_utterance(
                            websocket, 
                            session, 
                            bytes(audio_buffer), 
                            language
                        )
                        
                        # Clear buffer
                        audio_buffer.clear()
            
            elif msg_type == "interrupt":
                # User interrupted AI response
                logger.info(f"🛑 Interrupt signal received - Session: {session_id}")
                
                # Stop current TTS generation
                if tts_model:
                    await tts_model.stop_generation(session_id)
                
                # Clear audio buffer
                audio_buffer.clear()
                is_speaking = False
                
                # Acknowledge interrupt
                await websocket.send_json({
                    "type": "status",
                    "message": "interrupted",
                    "timestamp": datetime.now().isoformat()
                })
            
            elif msg_type == "config":
                # Update session configuration
                language = message.get("language", language)
                session.language = language
                
                logger.info(f"⚙️ Config updated - Session: {session_id}, Language: {language}")
                
                await websocket.send_json({
                    "type": "status",
                    "message": "config_updated",
                    "language": language,
                    "timestamp": datetime.now().isoformat()
                })
            
            elif msg_type == "ping":
                # Heartbeat
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {session_id}")
    
    except Exception as e:
        logger.error(f"❌ Error in WebSocket conversation: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            })
        except:
            pass
    
    finally:
        # Cleanup session
        await session_manager.remove_session(session_id)
        logger.info(f"🗑️ Session cleaned up: {session_id}")


async def process_utterance(
    websocket: WebSocket,
    session,
    audio_data: bytes,
    language: str
):
    """
    Process a complete utterance through the STT -> LLM -> TTS pipeline
    """
    session_id = session.session_id
    
    try:
        # Step 1: STT - Speech to Text
        logger.debug(f"🎙️ [STT] Processing audio - Session: {session_id}")
        
        start_time = datetime.now()
        transcript = await stt_model.transcribe(audio_data, language=language)
        stt_latency = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(f"📝 [STT] Transcript: '{transcript}' ({stt_latency:.0f}ms)")
        
        # Send transcript to client
        await websocket.send_json({
            "type": "transcript",
            "text": transcript,
            "language": language,
            "latency_ms": stt_latency,
            "timestamp": datetime.now().isoformat()
        })
        
        if not transcript.strip():
            logger.warning(f"⚠️ Empty transcript - Session: {session_id}")
            return
        
        # Step 2: LLM & TTS Pipeline (Streaming)
        logger.debug(f"🤖 [LLM] Generating response stream - Session: {session_id}")
        
        await websocket.send_json({
            "type": "response_text_start",
            "language": language,
            "timestamp": datetime.now().isoformat()
        })
        
        tts_queue = asyncio.Queue()
        
        # Background task for TTS
        async def tts_worker():
            try:
                first_chunk = True
                tts_start_time = datetime.now()
                while True:
                    sentence = await tts_queue.get()
                    if sentence is None:  # Sentinel to stop
                        tts_queue.task_done()
                        break
                    
                    logger.debug(f"🔊 [TTS] Synthesizing sentence: '{sentence}'")
                    # Synthesize this sentence
                    async for audio_chunk in tts_model.synthesize_streaming(
                        sentence,
                        language=language,
                        session_id=session_id
                    ):
                        if first_chunk:
                            ttfa = (datetime.now() - tts_start_time).total_seconds() * 1000
                            logger.info(f"🎵 [TTS] First audio chunk ({ttfa:.0f}ms)")
                            first_chunk = False
                        
                        audio_b64 = base64.b64encode(audio_chunk).decode('utf-8')
                        await websocket.send_json({
                            "type": "response_audio",
                            "data": audio_b64,
                            "sample_rate": getattr(tts_model, "sample_rate", 48000),
                            "timestamp": datetime.now().isoformat()
                        })
                    tts_queue.task_done()
            except Exception as e:
                logger.error(f"TTS Worker Error: {e}", exc_info=True)

        tts_task = asyncio.create_task(tts_worker())
        
        current_sentence = ""
        full_response = ""
        import re
        sentence_end_pattern = re.compile(r'[。，！？,\.\!\?\n]')
        
        start_time = datetime.now()
        async for text_chunk in llm_model.generate_response_stream(
            transcript,
            session=session,
            language=language
        ):
            full_response += text_chunk
            current_sentence += text_chunk
            
            await websocket.send_json({
                "type": "response_text_chunk",
                "text": text_chunk,
                "timestamp": datetime.now().isoformat()
            })
            
            # Check for sentence boundary
            if sentence_end_pattern.search(text_chunk):
                if current_sentence.strip():
                    await tts_queue.put(current_sentence.strip())
                current_sentence = ""
                
        # Send remaining text
        if current_sentence.strip():
            await tts_queue.put(current_sentence.strip())
            
        # Tell TTS worker we're done
        await tts_queue.put(None)
        
        llm_latency = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"💬 [LLM] Full Response: '{full_response}' ({llm_latency:.0f}ms)")
        
        # Wait for TTS to finish sending audio
        await tts_task
        
        total_latency = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"✅ [Pipeline] Complete ({stt_latency + total_latency:.0f}ms total)")
        
        # Send completion signal
        await websocket.send_json({
            "type": "response_complete",
            "latency": {
                "stt_ms": stt_latency,
                "total_ms": stt_latency + total_latency
            },
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"❌ Error processing utterance: {e}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "message": f"處理錯誤: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.post("/api/test/stt")
async def test_stt(audio_file: bytes, language: str = "zh-tw"):
    """Test STT endpoint"""
    try:
        transcript = await stt_model.transcribe(audio_file, language=language)
        return {"transcript": transcript, "language": language}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/test/tts")
async def test_tts(text: str, language: str = "zh-tw"):
    """Test TTS endpoint"""
    try:
        audio_chunks = []
        async for chunk in tts_model.synthesize_streaming(text, language=language):
            audio_chunks.append(chunk)
        
        audio_data = b''.join(audio_chunks)
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        return {"audio": audio_b64, "text": text, "language": language}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set True for development
        log_level="info",
        access_log=True,
        ws_ping_interval=20,
        ws_ping_timeout=20,
    )
