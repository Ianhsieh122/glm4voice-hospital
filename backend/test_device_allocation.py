"""
測試腳本：驗證模型設備分配
檢查 STT, LLM, TTS 是否正確加載到指定設備
"""

import asyncio
import torch
from loguru import logger
from utils.config import load_config
from models.stt_model import STTModel
from models.llm_model import LLMModel
from models.tts_model import TTSModel


async def test_device_allocation():
    """測試設備分配"""
    
    # 載入配置
    logger.info("=" * 60)
    logger.info("🔍 測試模型設備分配")
    logger.info("=" * 60)
    
    config = load_config()
    
    # 顯示配置
    logger.info("\n📋 配置信息：")
    logger.info(f"  STT 設備: {getattr(config.gpu, 'stt_device', config.gpu.device)}")
    logger.info(f"  LLM 設備: {getattr(config.gpu, 'llm_device', config.gpu.device)}")
    logger.info(f"  TTS 設備: {getattr(config.gpu, 'tts_device', config.gpu.device)}")
    logger.info(f"  vLLM 啟用: {config.vllm.enabled if hasattr(config, 'vllm') else False}")
    
    # 檢查 GPU 可用性
    logger.info("\n🖥️ 硬體信息：")
    if torch.cuda.is_available():
        logger.info(f"  ✅ GPU 可用: {torch.cuda.get_device_name(0)}")
        logger.info(f"  💾 VRAM 總量: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        logger.info(f"  💾 VRAM 已用: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
    else:
        logger.warning("  ⚠️ GPU 不可用，將使用 CPU")
    
    # 初始化模型
    logger.info("\n" + "=" * 60)
    logger.info("開始加載模型...")
    logger.info("=" * 60)
    
    stt_model = None
    llm_model = None
    tts_model = None
    
    try:
        # 1. 加載 STT 模型
        logger.info("\n1️⃣ 加載 STT 模型...")
        stt_model = STTModel(config)
        logger.info(f"  預期設備: {stt_model.device}")
        await stt_model.load()
        
        # 顯示 STT 信息
        stt_info = stt_model.get_model_info()
        logger.info(f"  ✅ STT 模型已加載")
        logger.info(f"  📊 模型: {stt_info['model_name']}")
        logger.info(f"  🖥️ 設備: {stt_info['device']}")
        logger.info(f"  🔧 後端: {stt_info['backend']}")
        
        if torch.cuda.is_available():
            logger.info(f"  💾 VRAM 已用: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
        
        # 2. 加載 LLM 模型
        logger.info("\n2️⃣ 加載 LLM 模型...")
        llm_model = LLMModel(config)
        logger.info(f"  預期設備: {llm_model.device}")
        await llm_model.load()
        
        # 顯示 LLM 信息
        llm_info = llm_model.get_model_info()
        logger.info(f"  ✅ LLM 模型已加載")
        logger.info(f"  📊 模型: {llm_info['model_name']}")
        logger.info(f"  🖥️ 設備: {llm_info['device']}")
        logger.info(f"  🚀 vLLM: {llm_info['use_vllm']}")
        logger.info(f"  🔢 精度: {llm_info['precision']}")
        
        if torch.cuda.is_available():
            logger.info(f"  💾 VRAM 已用: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
        
        # 3. 加載 TTS 模型
        logger.info("\n3️⃣ 加載 TTS 模型...")
        tts_model = TTSModel(config)
        logger.info(f"  預期設備: {tts_model.device}")
        await tts_model.load()
        
        # 顯示 TTS 信息
        tts_info = tts_model.get_model_info()
        logger.info(f"  ✅ TTS 模型已加載")
        logger.info(f"  📊 模型: {tts_info['model_name']}")
        logger.info(f"  🖥️ 設備: {tts_info['device']}")
        logger.info(f"  🔧 後端: {tts_info['backend']}")
        
        if torch.cuda.is_available():
            logger.info(f"  💾 VRAM 已用: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
        
        # 總結
        logger.info("\n" + "=" * 60)
        logger.info("✅ 所有模型加載成功！")
        logger.info("=" * 60)
        
        logger.info("\n📊 設備分配總結：")
        logger.info(f"  STT: {stt_info['device']} ({stt_info['backend']})")
        logger.info(f"  LLM: {llm_info['device']} ({'vLLM' if llm_info['use_vllm'] else 'Standard'})")
        logger.info(f"  TTS: {tts_info['device']} ({tts_info['backend']})")
        
        if torch.cuda.is_available():
            total_vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
            used_vram = torch.cuda.memory_allocated(0) / 1024**3
            logger.info(f"\n💾 GPU 記憶體使用：")
            logger.info(f"  已用: {used_vram:.2f} GB / {total_vram:.2f} GB")
            logger.info(f"  可用: {total_vram - used_vram:.2f} GB")
            logger.info(f"  使用率: {(used_vram / total_vram) * 100:.1f}%")
        
        # 驗證設備分配是否正確
        logger.info("\n🔍 驗證設備分配：")
        
        expected_stt = getattr(config.gpu, 'stt_device', config.gpu.device)
        expected_llm = getattr(config.gpu, 'llm_device', config.gpu.device)
        expected_tts = getattr(config.gpu, 'tts_device', config.gpu.device)
        
        stt_correct = stt_info['device'] == expected_stt
        llm_correct = llm_info['device'] == expected_llm
        tts_correct = tts_info['device'] == expected_tts
        
        logger.info(f"  STT: {'✅' if stt_correct else '❌'} (預期: {expected_stt}, 實際: {stt_info['device']})")
        logger.info(f"  LLM: {'✅' if llm_correct else '❌'} (預期: {expected_llm}, 實際: {llm_info['device']})")
        logger.info(f"  TTS: {'✅' if tts_correct else '❌'} (預期: {expected_tts}, 實際: {tts_info['device']})")
        
        if stt_correct and llm_correct and tts_correct:
            logger.info("\n🎉 設備分配完全正確！")
        else:
            logger.warning("\n⚠️ 某些模型的設備分配不符合預期")
        
    except Exception as e:
        logger.error(f"\n❌ 模型加載失敗: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
    finally:
        # 清理資源
        logger.info("\n🧹 清理資源...")
        
        if stt_model and stt_model.is_loaded:
            await stt_model.unload()
            logger.info("  ✅ STT 模型已卸載")
        
        if llm_model and llm_model.is_loaded:
            await llm_model.unload()
            logger.info("  ✅ LLM 模型已卸載")
        
        if tts_model and tts_model.is_loaded:
            await tts_model.unload()
            logger.info("  ✅ TTS 模型已卸載")
        
        if torch.cuda.is_available():
            logger.info(f"  💾 VRAM 剩餘: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
        
        logger.info("\n測試完成！")


if __name__ == "__main__":
    asyncio.run(test_device_allocation())
