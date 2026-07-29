"""
Voice Activity Detection (VAD) for speech endpoint detection
"""

import numpy as np
from typing import Optional
from loguru import logger

try:
    import webrtcvad
    WEBRTC_VAD_AVAILABLE = True
except ImportError:
    WEBRTC_VAD_AVAILABLE = False
    logger.warning("webrtcvad not available, using simple energy-based VAD")


class VoiceActivityDetector:
    """Voice Activity Detector for speech/silence classification"""
    
    def __init__(self, config):
        self.config = config
        self.sample_rate = config.audio.sample_rate
        self.frame_duration = config.audio.vad_frame_duration  # ms
        self.threshold = config.audio.vad_threshold
        
        # WebRTC VAD
        self.vad = None
        if WEBRTC_VAD_AVAILABLE:
            try:
                self.vad = webrtcvad.Vad(mode=2)  # Aggressiveness: 0-3
                logger.info("✅ WebRTC VAD initialized")
            except Exception as e:
                logger.warning(f"Failed to init WebRTC VAD: {e}")
                self.vad = None
        
        # Fallback: energy-based VAD
        self.energy_threshold = 500  # Adjust based on your audio setup
        
        # Smoothing state
        self.speech_frames = 0
        self.silence_frames = 0
        self.min_speech_frames = 3  # Require 3 consecutive speech frames
        self.min_silence_frames = 10  # Require 10 consecutive silence frames
    
    def is_speech(self, audio_data: bytes) -> bool:
        """
        Detect if audio frame contains speech
        
        Args:
            audio_data: Raw PCM16 audio bytes
        
        Returns:
            True if speech detected, False otherwise
        """
        try:
            # Convert to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            if len(audio_array) == 0:
                return False
            
            # Try WebRTC VAD first
            if self.vad and WEBRTC_VAD_AVAILABLE:
                is_speech = self._webrtc_vad(audio_data)
            else:
                # Fallback to energy-based VAD
                is_speech = self._energy_vad(audio_array)
            
            # Smooth the detection with state tracking
            if is_speech:
                self.speech_frames += 1
                self.silence_frames = 0
                # Confirm speech after min_speech_frames
                return self.speech_frames >= self.min_speech_frames
            else:
                self.silence_frames += 1
                self.speech_frames = 0
                # Confirm silence after min_silence_frames
                return self.silence_frames < self.min_silence_frames
        
        except Exception as e:
            logger.error(f"VAD error: {e}")
            return False
    
    def _webrtc_vad(self, audio_data: bytes) -> bool:
        """WebRTC VAD detection"""
        try:
            # WebRTC VAD requires specific frame sizes (10, 20, or 30ms)
            # and sample rates (8000, 16000, 32000, 48000 Hz)
            
            # Calculate required frame size
            frame_size = int(self.sample_rate * self.frame_duration / 1000)
            
            # Ensure audio_data is the right size
            if len(audio_data) < frame_size * 2:  # *2 because int16 = 2 bytes
                # Pad with zeros if too short
                padding = b'\x00' * (frame_size * 2 - len(audio_data))
                audio_data = audio_data + padding
            elif len(audio_data) > frame_size * 2:
                # Truncate if too long
                audio_data = audio_data[:frame_size * 2]
            
            # Run VAD
            is_speech = self.vad.is_speech(audio_data, self.sample_rate)
            return is_speech
        
        except Exception as e:
            logger.debug(f"WebRTC VAD error: {e}")
            # Fallback to energy-based
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            return self._energy_vad(audio_array)
    
    def _energy_vad(self, audio_array: np.ndarray) -> bool:
        """Simple energy-based VAD"""
        # Calculate RMS energy
        energy = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
        
        # Compare to threshold
        is_speech = energy > self.energy_threshold
        
        return is_speech
    
    def reset(self):
        """Reset VAD state"""
        self.speech_frames = 0
        self.silence_frames = 0
    
    def set_aggressiveness(self, mode: int):
        """
        Set VAD aggressiveness (0-3)
        0: Least aggressive (more permissive)
        3: Most aggressive (only very clear speech)
        """
        if self.vad and WEBRTC_VAD_AVAILABLE:
            try:
                self.vad.set_mode(mode)
                logger.info(f"VAD aggressiveness set to: {mode}")
            except Exception as e:
                logger.error(f"Failed to set VAD mode: {e}")
    
    def set_energy_threshold(self, threshold: float):
        """Set energy threshold for fallback VAD"""
        self.energy_threshold = threshold
        logger.info(f"Energy threshold set to: {threshold}")
    
    def calibrate(self, silence_audio: bytes, speech_audio: bytes):
        """
        Calibrate VAD thresholds based on sample audio
        
        Args:
            silence_audio: Audio sample of silence/background noise
            speech_audio: Audio sample of clear speech
        """
        try:
            # Calculate energy levels
            silence_array = np.frombuffer(silence_audio, dtype=np.int16)
            speech_array = np.frombuffer(speech_audio, dtype=np.int16)
            
            silence_energy = np.sqrt(np.mean(silence_array.astype(np.float32) ** 2))
            speech_energy = np.sqrt(np.mean(speech_array.astype(np.float32) ** 2))
            
            # Set threshold between silence and speech
            self.energy_threshold = (silence_energy + speech_energy) / 2
            
            logger.info(f"VAD calibrated: silence={silence_energy:.1f}, "
                       f"speech={speech_energy:.1f}, threshold={self.energy_threshold:.1f}")
        
        except Exception as e:
            logger.error(f"VAD calibration error: {e}")


class EndpointDetector:
    """Detect speech endpoints (start/end of utterance)"""
    
    def __init__(self, vad: VoiceActivityDetector):
        self.vad = vad
        self.is_speaking = False
        self.speech_start_time = None
        self.last_speech_time = None
        
        # Parameters
        self.min_speech_duration = 0.3  # seconds
        self.max_silence_duration = 0.8  # seconds (end of utterance)
        self.max_utterance_duration = 30.0  # seconds (force end)
    
    def process_frame(self, audio_data: bytes, timestamp: float) -> dict:
        """
        Process audio frame and detect endpoints
        
        Returns:
            dict with keys:
                - event: "start", "continue", "end", or None
                - duration: speech duration if ended
        """
        is_speech = self.vad.is_speech(audio_data)
        
        if is_speech:
            if not self.is_speaking:
                # Speech started
                self.is_speaking = True
                self.speech_start_time = timestamp
                self.last_speech_time = timestamp
                
                return {
                    "event": "start",
                    "timestamp": timestamp
                }
            else:
                # Speech continuing
                self.last_speech_time = timestamp
                
                # Check for max duration
                duration = timestamp - self.speech_start_time
                if duration > self.max_utterance_duration:
                    # Force end
                    self.is_speaking = False
                    return {
                        "event": "end",
                        "duration": duration,
                        "reason": "max_duration"
                    }
                
                return {
                    "event": "continue",
                    "duration": duration
                }
        else:
            if self.is_speaking:
                # Check silence duration
                silence_duration = timestamp - self.last_speech_time
                
                if silence_duration > self.max_silence_duration:
                    # Speech ended
                    speech_duration = self.last_speech_time - self.speech_start_time
                    self.is_speaking = False
                    
                    # Only trigger end if speech was long enough
                    if speech_duration >= self.min_speech_duration:
                        return {
                            "event": "end",
                            "duration": speech_duration,
                            "reason": "silence"
                        }
                    else:
                        # Too short, ignore
                        return {
                            "event": "cancelled",
                            "duration": speech_duration
                        }
        
        return {"event": None}
    
    def reset(self):
        """Reset endpoint detector state"""
        self.is_speaking = False
        self.speech_start_time = None
        self.last_speech_time = None
        self.vad.reset()
