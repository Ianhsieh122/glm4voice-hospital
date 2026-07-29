"""
Download Models Script - Q4 Quantized LLM + Full Precision STT/TTS
專門為你的機器下載和配置模型
"""

import os
from pathlib import Path
from loguru import logger
from huggingface_hub import snapshot_download, hf_hub_download
import torch
import sys


def check_gpu():
    """檢查 GPU"""
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
        logger.info(f"✅ GPU: {gpu_name}")
        logger.info(f"💾 VRAM: {vram_gb:.2f} GB")
        return True
    else:
        logger.warning("⚠️ 未檢測到 GPU，將使用 CPU（會很慢）")
        return False


def download_q4_llm():
    """下載 Q4 量化的 LLM 模型"""
    logger.info("=" * 70)
    logger.info("📥 下載 LLM: Qwen2.5-3B-Instruct (Q4 量化版本)")
    logger.info("=" * 70)
    
    # 使用 GGUF Q4 量化版本（最適合 vLLM）
    model_id = "Qwen/Qwen2.5-3B-Instruct-GGUF"
    filename = "qwen2.5-3b-instruct-q4_k_m.gguf"
    
    logger.info(f"模型: {model_id}")
    logger.info(f"文件: {filename}")
    logger.info(f"大小: ~2.0 GB")
    logger.info(f"量化: Q4_K_M (4-bit)")
    
    try:
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        
        # 下載 GGUF 文件
        local_path = hf_hub_download(
            repo_id=model_id,
            filename=filename,
            cache_dir=cache_dir,
            resume_download=True,
        )
        
        logger.info(f"✅ LLM (Q4) 下載完成")
        logger.info(f"路徑: {local_path}")
        return local_path
        
    except Exception as e:
        logger.error(f"❌ 下載失敗: {e}")
        logger.info("嘗試替代方案...")
        
        # 替代方案：使用 4-bit AWQ 量化
        try:
            model_id_awq = "Qwen/Qwen2.5-3B-Instruct-AWQ"
            logger.info(f"使用 AWQ 4-bit: {model_id_awq}")
            
            local_path = snapshot_download(
                repo_id=model_id_awq,
                cache_dir=cache_dir,
                resume_download=True,
            )
            
            logger.info(f"✅ LLM (AWQ 4-bit) 下載完成")
            logger.info(f"路徑: {local_path}")
            return local_path
            
        except Exception as e2:
            logger.error(f"❌ 替代方案也失敗: {e2}")
            raise


def download_stt():
    """下載 STT 模型（Full Precision）"""
    logger.info("=" * 70)
    logger.info("📥 下載 STT: Whisper-Large-v3-Turbo (FP16 完整精度)")
    logger.info("=" * 70)
    
    model_id = "openai/whisper-large-v3-turbo"
    
    logger.info(f"模型: {model_id}")
    logger.info(f"大小: ~3.1 GB")
    logger.info(f"精度: FP16 (無量化)")
    
    try:
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        
        local_path = snapshot_download(
            repo_id=model_id,
            cache_dir=cache_dir,
            resume_download=True,
        )
        
        logger.info(f"✅ STT 下載完成")
        logger.info(f"路徑: {local_path}")
        return local_path
        
    except Exception as e:
        logger.error(f"❌ 下載失敗: {e}")
        raise


def download_tts():
    """下載 TTS 模型（Full Precision）"""
    logger.info("=" * 70)
    logger.info("📥 下載 TTS: Qwen3-TTS (FP16 完整精度)")
    logger.info("=" * 70)
    
    model_id = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
    
    logger.info(f"模型: {model_id}")
    logger.info(f"大小: ~3.4 GB")
    logger.info(f"精度: FP16 (無量化)")
    
    try:
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        
        local_path = snapshot_download(
            repo_id=model_id,
            cache_dir=cache_dir,
            resume_download=True,
        )
        
        logger.info(f"✅ TTS 下載完成")
        logger.info(f"路徑: {local_path}")
        return local_path
        
    except Exception as e:
        logger.error(f"❌ 下載失敗: {e}")
        raise


def main():
    """主函數"""
    logger.info("🚀 開始下載模型...")
    logger.info("=" * 70)
    
    # 檢查 GPU
    has_gpu = check_gpu()
    
    logger.info("")
    logger.info("📋 下載計劃:")
    logger.info("  1. LLM: Qwen2.5-3B-Instruct (Q4 量化) ~2.0GB")
    logger.info("  2. STT: Whisper-v3-Turbo (FP16) ~3.1GB")
    logger.info("  3. TTS: Qwen3-TTS (FP16) ~3.4GB")
    logger.info("  總計: ~8.5GB")
    logger.info("")
    logger.info("⏱️  預計時間: 10-15 分鐘（取決於網速）")
    logger.info("=" * 70)
    
    logger.info("\n開始自動下載...")
    
    results = {}
    
    try:
        # 1. 下載 LLM (Q4)
        logger.info("\n[1/3] 下載 LLM...")
        results['llm'] = download_q4_llm()
        
        # 2. 下載 STT
        logger.info("\n[2/3] 下載 STT...")
        results['stt'] = download_stt()
        
        # 3. 下載 TTS
        logger.info("\n[3/3] 下載 TTS...")
        results['tts'] = download_tts()
        
        # 完成
        logger.info("\n" + "=" * 70)
        logger.info("🎉 所有模型下載完成！")
        logger.info("=" * 70)
        
        logger.info("\n📦 模型位置:")
        for model_type, path in results.items():
            logger.info(f"  {model_type.upper()}: {path}")
        
        logger.info("\n✅ 下一步:")
        logger.info("  執行部署腳本: python deploy_to_machine.py")
        
        return results
        
    except Exception as e:
        logger.error(f"\n❌ 下載過程中發生錯誤: {e}")
        logger.error("請檢查網路連接或稍後重試")
        sys.exit(1)


if __name__ == "__main__":
    main()
