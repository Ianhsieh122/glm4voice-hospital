"""
Configuration management for Opus Hospital
"""

import os
from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field
from loguru import logger


class GPUConfig(BaseModel):
    """GPU configuration"""
    device: str = "cuda:0"
    precision: str = "fp8"  # fp8, 4bit, bf16, fp16
    
    # Individual device settings for each model
    stt_device: str = "cuda:0"  # STT on GPU
    llm_device: str = "cpu"     # LLM on CPU
    tts_device: str = "cuda:0"  # TTS on GPU


class ModelsConfig(BaseModel):
    """AI models configuration"""
    stt: str = "Qwen/Qwen3-ASR-1.7B"
    llm: str = "taide/TAIDE-LX-70B-Chat-4bit"
    tts: str = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
    tts_model_name: str = "F5-TTS"  # F5-TTS or DiaMoE-TTS


class AudioConfig(BaseModel):
    """Audio processing configuration"""
    sample_rate: int = 16000
    channels: int = 1
    format: str = "pcm16"
    chunk_size: int = 4096
    vad_threshold: float = 0.5
    vad_frame_duration: int = 30  # milliseconds


class ServerConfig(BaseModel):
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    workers: int = 1
    log_level: str = "info"


class SessionConfig(BaseModel):
    """Session management configuration"""
    max_history_length: int = 20
    session_timeout: int = 3600  # seconds
    cleanup_interval: int = 300  # seconds


class Config(BaseModel):
    """Main configuration"""
    gpu: GPUConfig = Field(default_factory=GPUConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Config":
        """Load configuration from YAML file"""
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return cls(**data)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {yaml_path}, using defaults")
            return cls()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return cls()
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        config = cls()
        
        # GPU config
        if os.getenv("GPU_DEVICE"):
            config.gpu.device = os.getenv("GPU_DEVICE")
        if os.getenv("GPU_PRECISION"):
            config.gpu.precision = os.getenv("GPU_PRECISION")
        
        # Models config
        if os.getenv("STT_MODEL"):
            config.models.stt = os.getenv("STT_MODEL")
        if os.getenv("LLM_MODEL"):
            config.models.llm = os.getenv("LLM_MODEL")
        if os.getenv("TTS_MODEL"):
            config.models.tts = os.getenv("TTS_MODEL")
        
        # Server config
        if os.getenv("SERVER_HOST"):
            config.server.host = os.getenv("SERVER_HOST")
        if os.getenv("SERVER_PORT"):
            config.server.port = int(os.getenv("SERVER_PORT"))
        
        return config
    
    def to_yaml(self, yaml_path: str):
        """Save configuration to YAML file"""
        try:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.dict(), f, default_flow_style=False, allow_unicode=True)
            logger.info(f"Config saved to: {yaml_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")


def load_config() -> Config:
    """Load configuration from file or environment"""
    # Check for environment variable to select config
    env = os.getenv("OPUS_ENV", "development")  # default to development
    
    if env == "production":
        config_path = os.getenv("CONFIG_PATH", "config.production.yaml")
    elif env == "development":
        config_path = os.getenv("CONFIG_PATH", "config.development.yaml")
    else:
        config_path = os.getenv("CONFIG_PATH", "config.yaml")
    
    if os.path.exists(config_path):
        logger.info(f"Loading config from: {config_path} (environment: {env})")
        return Config.from_yaml(config_path)
    else:
        logger.warning(f"Config file not found: {config_path}, trying default config.yaml")
        if os.path.exists("config.yaml"):
            return Config.from_yaml("config.yaml")
        else:
            logger.warning("No config file found, loading from environment variables")
            return Config.from_env()


# Create default config file if it doesn't exist
def create_default_config(output_path: str = "config.yaml"):
    """Create default configuration file"""
    config = Config()
    config.to_yaml(output_path)
    logger.info(f"Default config created: {output_path}")


if __name__ == "__main__":
    # Generate default config
    create_default_config("config.yaml")
