"""
Opus Hospital - 完整啟動腳本
一鍵啟動所有服務（STT, LLM, TTS）和 Web 界面
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from loguru import logger
import torch
from datetime import datetime
import json
import base64
from typing import Optional, Dict, List

# 導入配置和模型
from utils.config import load_config
from models.stt_model import STTModel
from models.llm_model import LLMModel
from database.patient_db import PatientDatabase

# 初始化
app = FastAPI(title="Opus Hospital AI", version="2.0.0")
config = load_config()
db = PatientDatabase(config.database.path if hasattr(config, 'database') else "data/patients.db")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局變量
stt_model: Optional[STTModel] = None
llm_model: Optional[LLMModel] = None
tts_model = None  # 暫時使用簡單的回應
sessions: Dict[str, Dict] = {}

# ==================== Pydantic Models ====================

class AppointmentCreate(BaseModel):
    patient_name: str
    birth_date_roc: str
    id_number: Optional[str] = None
    phone: str
    department: str
    doctor: str
    appointment_date: str
    appointment_time: str
    notes: Optional[str] = None

# ==================== 啟動/關閉 ====================

@app.on_event("startup")
async def startup():
    global stt_model, llm_model
    
    logger.info("=" * 60)
    logger.info("🏥 Opus Hospital AI Reception System")
    logger.info("=" * 60)
    
    env = os.getenv("OPUS_ENV", "development")
    logger.info(f"環境: {env}")
    
    # GPU 檢查
    if torch.cuda.is_available():
        logger.info(f"✅ GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"💾 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    else:
        logger.warning("⚠️ GPU 不可用，使用 CPU")
    
    # 載入模型
    try:
        logger.info("\n📦 載入模型...")
        
        # STT
        logger.info("1/2 載入 STT (Whisper)...")
        stt_model = STTModel(config)
        await stt_model.load()
        logger.info("  ✅ STT 已載入")
        
        # LLM
        logger.info("2/2 載入 LLM (Qwen2.5-3B)...")
        llm_model = LLMModel(config)
        await llm_model.load()
        logger.info("  ✅ LLM 已載入")
        
        # TTS - 暫時跳過，使用文字回應
        logger.info("  ⏭️ TTS 暫時跳過（使用文字回應）")
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 所有服務就緒！")
        logger.info("=" * 60)
        logger.info(f"🌐 Web 界面: http://localhost:{config.server.port}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 啟動失敗: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

@app.on_event("shutdown")
async def shutdown():
    logger.info("🛑 關閉服務...")
    if stt_model:
        await stt_model.unload()
    if llm_model:
        await llm_model.unload()

# ==================== API 端點 ====================

@app.get("/")
async def root():
    """主頁 - 返回 HTML"""
    html_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding='utf-8'))
    return {"message": "Opus Hospital AI", "status": "running"}

@app.get("/health")
async def health():
    """健康檢查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "models": {
            "stt": stt_model.is_loaded if stt_model else False,
            "llm": llm_model.is_loaded if llm_model else False,
            "tts": False  # 暫時禁用
        },
        "sessions": len(sessions)
    }

@app.get("/api/models/status")
async def models_status():
    """模型狀態"""
    return {
        "stt": stt_model.get_model_info() if stt_model else {},
        "llm": llm_model.get_model_info() if llm_model else {},
        "tts": {"status": "disabled"}
    }

# ==================== 掛號 API ====================

@app.post("/api/appointments/create")
async def create_appointment(appointment: AppointmentCreate):
    """創建掛號"""
    try:
        # 先添加病患
        patient = db.add_patient(
            name=appointment.patient_name,
            birth_date_roc=appointment.birth_date_roc,
            id_number=appointment.id_number,
            phone=appointment.phone
        )
        
        if not patient.get("success"):
            return {"success": False, "error": patient.get("error", "建立病患失敗")}
        
        # 創建掛號
        apt_result = db.create_appointment(
            patient_id=patient["patient_id"],
            department=appointment.department,
            doctor=appointment.doctor,
            appointment_date=appointment.appointment_date,
            appointment_time=appointment.appointment_time,
            notes=appointment.notes
        )
        
        return apt_result
        
    except Exception as e:
        logger.error(f"創建掛號失敗: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/appointments/list")
async def list_appointments():
    """獲取所有掛號"""
    try:
        appointments = db.get_all_appointments()
        return appointments
    except Exception as e:
        logger.error(f"獲取掛號列表失敗: {e}")
        return []

@app.post("/api/appointments/cancel/{appointment_id}")
async def cancel_appointment(appointment_id: str):
    """取消掛號"""
    try:
        result = db.cancel_appointment(appointment_id)
        return result
    except Exception as e:
        logger.error(f"取消掛號失敗: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/appointments/update/{appointment_id}")
async def update_appointment(appointment_id: str, appointment: AppointmentCreate):
    """更新掛號"""
    try:
        result = db.update_appointment(
            appointment_id=appointment_id,
            appointment_date=appointment.appointment_date,
            appointment_time=appointment.appointment_time,
            doctor=appointment.doctor,
            notes=appointment.notes
        )
        return result
    except Exception as e:
        logger.error(f"更新掛號失敗: {e}")
        return {"success": False, "error": str(e)}

# ==================== WebSocket 對話 ====================

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket 對話端點"""
    await websocket.accept()
    
    # 初始化 session
    sessions[session_id] = {
        "language": "zh-tw",
        "history": [],
        "created_at": datetime.now()
    }
    
    logger.info(f"🔌 新連線: {session_id}")
    
    try:
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "已連線"
        })
        
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "config":
                # 更新配置
                sessions[session_id]["language"] = data.get("language", "zh-tw")
                logger.info(f"語言設定: {data.get('language')}")
                
            elif msg_type == "audio":
                # 處理音頻
                try:
                    audio_b64 = data.get("audio", "")
                    audio_bytes = base64.b64decode(audio_b64)
                    
                    # STT 轉錄
                    await websocket.send_json({"type": "status", "message": "轉錄中..."})
                    
                    transcript = await stt_model.transcribe(
                        audio_bytes,
                        language=sessions[session_id]["language"]
                    )
                    
                    logger.info(f"用戶: {transcript}")
                    
                    # 發送轉錄文本
                    await websocket.send_json({
                        "type": "transcript",
                        "text": transcript
                    })
                    
                    # LLM 生成回應
                    await websocket.send_json({"type": "status", "message": "思考中..."})
                    
                    # 簡單的 session 對象
                    class SimpleSession:
                        def __init__(self, history):
                            self.conversation_history = history
                        def add_message(self, role, content):
                            self.conversation_history.append({"role": role, "content": content})
                    
                    session_obj = SimpleSession(sessions[session_id]["history"])
                    
                    response = await llm_model.generate_response(
                        user_input=transcript,
                        session=session_obj,
                        language=sessions[session_id]["language"]
                    )
                    
                    logger.info(f"助理: {response}")
                    
                    # 發送回應
                    await websocket.send_json({
                        "type": "response",
                        "text": response
                    })
                    
                    await websocket.send_json({
                        "type": "completed"
                    })
                    
                except Exception as e:
                    logger.error(f"處理音頻失敗: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
    
    except WebSocketDisconnect:
        logger.info(f"🔌 斷線: {session_id}")
        if session_id in sessions:
            del sessions[session_id]

# ==================== 主程序 ====================

if __name__ == "__main__":
    # 確保目錄存在
    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # 啟動服務器
    port = config.server.port if hasattr(config, 'server') else 8000
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
