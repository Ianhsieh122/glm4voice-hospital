"""
Audio processing utilities
"""

import numpy as np
import io
from typing import Optional
from loguru import logger

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False
    logger.warning("soundfile not available")

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa not available")


class AudioProcessor:
    """Audio processing and conversion utilities"""
    
    def __init__(self, config):
        self.config = config
        self.sample_rate = config.audio.sample_rate
        self.channels = config.audio.channels
    
    def pcm16_to_float32(self, pcm_data: bytes) -> np.ndarray:
        """Convert PCM16 bytes to float32 numpy array"""
        int_array = np.frombuffer(pcm_data, dtype=np.int16)
        float_array = int_array.astype(np.float32) / 32768.0
        return float_array
    
    def float32_to_pcm16(self, float_array: np.ndarray) -> bytes:
        """Convert float32 numpy array to PCM16 bytes"""
        int_array = (float_array * 32767).astype(np.int16)
        return int_array.tobytes()
    
    def resample(
        self,
        audio_data: np.ndarray,
        orig_sr: int,
        target_sr: int
    ) -> np.ndarray:
        """Resample audio to different sample rate"""
        if not LIBROSA_AVAILABLE:
            logger.error("librosa required for resampling")
            return audio_data
        
        if orig_sr == target_sr:
            return audio_data
        
        try:
            resampled = librosa.resample(
                audio_data,
                orig_sr=orig_sr,
                target_sr=target_sr
            )
            return resampled
        except Exception as e:
            logger.error(f"Resampling error: {e}")
            return audio_data
    
    def convert_to_mono(self, audio_data: np.ndarray) -> np.ndarray:
        """Convert stereo to mono"""
        if audio_data.ndim == 1:
            return audio_data
        elif audio_data.ndim == 2:
            # Average channels
            return np.mean(audio_data, axis=1)
        else:
            logger.error(f"Unexpected audio shape: {audio_data.shape}")
            return audio_data
    
    def normalize_audio(
        self,
        audio_data: np.ndarray,
        target_level: float = 0.9
    ) -> np.ndarray:
        """Normalize audio to target level"""
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            normalized = audio_data * (target_level / max_val)
            return normalized
        return audio_data
    
    def apply_gain(
        self,
        audio_data: np.ndarray,
        gain_db: float
    ) -> np.ndarray:
        """Apply gain in decibels"""
        gain_linear = 10 ** (gain_db / 20.0)
        return audio_data * gain_linear
    
    def trim_silence(
        self,
        audio_data: np.ndarray,
        threshold_db: float = -40.0
    ) -> np.ndarray:
        """Trim silence from start and end"""
        if not LIBROSA_AVAILABLE:
            return audio_data
        
        try:
            trimmed, _ = librosa.effects.trim(
                audio_data,
                top_db=-threshold_db
            )
            return trimmed
        except Exception as e:
            logger.error(f"Trim silence error: {e}")
            return audio_data
    
    def load_audio_file(
        self,
        file_path: str,
        target_sr: Optional[int] = None
    ) -> tuple[np.ndarray, int]:
        """Load audio file and return numpy array + sample rate"""
        if not SOUNDFILE_AVAILABLE:
            logger.error("soundfile required for loading audio files")
            return np.array([]), 0
        
        try:
            audio_data, sr = sf.read(file_path)
            
            # Convert to mono if needed
            if audio_data.ndim > 1:
                audio_data = self.convert_to_mono(audio_data)
            
            # Resample if needed
            if target_sr and target_sr != sr:
                audio_data = self.resample(audio_data, sr, target_sr)
                sr = target_sr
            
            return audio_data, sr
        
        except Exception as e:
            logger.error(f"Error loading audio file: {e}")
            return np.array([]), 0
    
    def save_audio_file(
        self,
        audio_data: np.ndarray,
        file_path: str,
        sample_rate: Optional[int] = None
    ):
        """Save numpy array to audio file"""
        if not SOUNDFILE_AVAILABLE:
            logger.error("soundfile required for saving audio files")
            return
        
        try:
            sr = sample_rate or self.sample_rate
            sf.write(file_path, audio_data, sr)
            logger.info(f"Audio saved to: {file_path}")
        except Exception as e:
            logger.error(f"Error saving audio file: {e}")
    
    def convert_format(
        self,
        audio_data: bytes,
        input_format: str,
        output_format: str
    ) -> bytes:
        """Convert between audio formats"""
        # Placeholder for format conversion
        # In production, implement conversions between PCM16, MP3, WAV, etc.
        if input_format == output_format:
            return audio_data
        
        logger.warning(f"Format conversion {input_format}->{output_format} not implemented")
        return audio_data
    
    def get_audio_duration(
        self,
        audio_data: np.ndarray,
        sample_rate: Optional[int] = None
    ) -> float:
        """Get audio duration in seconds"""
        sr = sample_rate or self.sample_rate
        return len(audio_data) / sr
    
    def get_audio_info(self, audio_data: np.ndarray) -> dict:
        """Get audio information"""
        return {
            "samples": len(audio_data),
            "duration_sec": self.get_audio_duration(audio_data),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "max_amplitude": float(np.max(np.abs(audio_data))),
            "rms_energy": float(np.sqrt(np.mean(audio_data ** 2))),
        }
    
    def create_silence(self, duration_sec: float) -> np.ndarray:
        """Create silence audio"""
        samples = int(duration_sec * self.sample_rate)
        return np.zeros(samples, dtype=np.float32)
    
    def concatenate_audio(self, audio_list: list[np.ndarray]) -> np.ndarray:
        """Concatenate multiple audio arrays"""
        return np.concatenate(audio_list)
    
    def mix_audio(
        self,
        audio1: np.ndarray,
        audio2: np.ndarray,
        ratio1: float = 0.5,
        ratio2: float = 0.5
    ) -> np.ndarray:
        """Mix two audio arrays"""
        # Ensure same length
        min_len = min(len(audio1), len(audio2))
        audio1 = audio1[:min_len]
        audio2 = audio2[:min_len]
        
        # Mix with ratios
        mixed = audio1 * ratio1 + audio2 * ratio2
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(mixed))
        if max_val > 1.0:
            mixed = mixed / max_val
        
        return mixed


def calculate_audio_features(audio_data: np.ndarray) -> dict:
    """Calculate various audio features"""
    features = {
        "energy": float(np.sum(audio_data ** 2)),
        "rms": float(np.sqrt(np.mean(audio_data ** 2))),
        "zero_crossing_rate": float(np.mean(np.abs(np.diff(np.sign(audio_data))))),
    }
    
    if LIBROSA_AVAILABLE:
        try:
            # Spectral features
            spectral_centroid = librosa.feature.spectral_centroid(y=audio_data, sr=16000)
            features["spectral_centroid"] = float(np.mean(spectral_centroid))
            
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=16000)
            features["spectral_rolloff"] = float(np.mean(spectral_rolloff))
        except Exception as e:
            logger.debug(f"Error calculating spectral features: {e}")
    
    return features
