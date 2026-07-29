"""
Download and cache AI models for Opus Hospital (Updated for NVIDIA + Qwen2.5-3B)
"""

import os
from pathlib import Path
from loguru import logger
from huggingface_hub import snapshot_download
import torch


def check_gpu():
    """Check GPU availability"""
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
        logger.info(f"✅ GPU detected: {gpu_name}")
        logger.info(f"💾 VRAM: {vram_gb:.2f} GB")
        
        # Check compute capability
        compute_capability = torch.cuda.get_device_capability(0)
        logger.info(f"🔧 Compute Capability: {compute_capability[0]}.{compute_capability[1]}")
        
        return True
    else:
        logger.warning("⚠️ No GPU detected, models will run on CPU (very slow)")
        logger.warning("⚠️ For 350-400 concurrent users, NVIDIA GPU is REQUIRED")
        return False


def download_model(model_id: str, model_type: str):
    """Download model from Hugging Face"""
    logger.info(f"📥 Downloading {model_type}: {model_id}")
    
    try:
        # Create cache directory
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Download model
        local_path = snapshot_download(
            repo_id=model_id,
            cache_dir=cache_dir,
            resume_download=True,
            local_files_only=False,
        )
        
        logger.info(f"✅ {model_type} downloaded to: {local_path}")
        return local_path
    
    except Exception as e:
        logger.error(f"❌ Failed to download {model_type}: {e}")
        raise


def main():
    """Main function to download all models"""
    logger.info("🚀 Downloading Opus Hospital AI Models (NVIDIA Optimized)")
    logger.info("=" * 60)
    
    # Check GPU
    has_gpu = check_gpu()
    
    if not has_gpu:
        logger.warning("⚠️ WARNING: Running without GPU will NOT support 350-400 concurrent users!")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            logger.info("Aborted.")
            return
    
    # Models to download (Updated for Qwen2.5-3B)
    models = {
        "STT (Whisper Turbo)": "openai/whisper-large-v3-turbo",
        "LLM (Qwen2.5-3B)": "Qwen/Qwen2.5-3B-Instruct",
        "TTS (Qwen3-TTS)": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    }
    
    logger.info("\n📦 Models to Download:")
    total_size_gb = 0
    model_sizes = {
        "openai/whisper-large-v3-turbo": 3.1,
        "Qwen/Qwen2.5-3B-Instruct": 6.2,
        "Qwen/Qwen3-TTS-12Hz-1.7B-Base": 3.4,
    }
    
    for name, model_id in models.items():
        size = model_sizes.get(model_id, 0)
        total_size_gb += size
        logger.info(f"  - {name}: {model_id} (~{size:.1f}GB)")
    
    logger.info(f"\n📊 Total Download Size: ~{total_size_gb:.1f}GB")
    logger.info(f"⏱️ Estimated Time: ~{int(total_size_gb * 1.5)} minutes (depends on internet speed)")
    logger.info("\n" + "=" * 60)
    
    # Confirm download
    response = input("\nStart download? (Y/n): ")
    if response.lower() == 'n':
        logger.info("Aborted.")
        return
    
    # Download models
    downloaded = {}
    for model_type, model_id in models.items():
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"Downloading {model_type}...")
            logger.info(f"{'='*60}")
            
            path = download_model(model_id, model_type)
            downloaded[model_type] = path
            
        except Exception as e:
            logger.error(f"❌ Failed to download {model_type}: {e}")
            logger.warning(f"⚠️ You can try downloading manually later")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Download Summary:")
    logger.info(f"  ✅ Successfully downloaded: {len(downloaded)}/{len(models)} models")
    
    for model_type in downloaded.keys():
        logger.info(f"  - {model_type}: ✓")
    
    failed = set(models.keys()) - set(downloaded.keys())
    if failed:
        logger.warning(f"  ❌ Failed: {len(failed)} models")
        for model_type in failed:
            logger.warning(f"  - {model_type}: ✗")
    
    logger.info("\n" + "=" * 60)
    
    if len(downloaded) == len(models):
        logger.info("🎉 All models downloaded successfully!")
        logger.info("\n🚀 Next Steps:")
        logger.info("  1. Run: python main.py")
        logger.info("  2. Or use the one-click startup script:")
        logger.info("     - Windows: start.bat")
        logger.info("     - Linux/Mac: ./start.sh")
        logger.info("\n💡 System Requirements for 350-400 Concurrent Users:")
        logger.info("  - NVIDIA GPU with 12GB+ VRAM (RTX 3060 12GB or better)")
        logger.info("  - 16GB+ System RAM")
        logger.info("  - vLLM with continuous batching enabled")
        logger.info("  - Recommended: RTX 4090 24GB or A100 40GB")
    else:
        logger.error("❌ Some models failed to download. Please check the errors above.")
        logger.info("You can try running this script again to resume downloads.")


if __name__ == "__main__":
    main()
