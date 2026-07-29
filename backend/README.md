# Opus Hospital AI Reception - Quick Start Guide

## 🚀 快速啟動（開發環境）

### 前置需求

- Python 3.10 或 3.11
- NVIDIA GPU with CUDA 12.1+ (8GB+ VRAM 建議)
- Git

### 1. 克隆倉庫

```bash
git clone https://github.com/your-org/opus-hospital.git
cd opus-hospital/backend
```

### 2. 安裝依賴

**Windows:**
```bash
# 創建虛擬環境
python -m venv venv
venv\Scripts\activate

# 安裝 PyTorch with CUDA
pip install torch==2.3.0+cu121 torchaudio==2.3.0+cu121 --index-url https://download.pytorch.org/whl/cu121

# 安裝其他依賴
pip install -r requirements.txt

# 安裝 F5-TTS
pip install f5-tts
```

**Linux/Mac:**
```bash
# 創建虛擬環境
python3.10 -m venv venv
source venv/bin/activate

# 安裝 PyTorch with CUDA
pip install torch==2.3.0+cu121 torchaudio==2.3.0+cu121 --index-url https://download.pytorch.org/whl/cu121

# 安裝其他依賴
pip install -r requirements.txt

# 安裝 F5-TTS
pip install f5-tts
```

### 3. 配置環境

```bash
# 複製環境變量模板
cp .env.example .env

# 編輯 .env 文件
# 設置 OPUS_ENV=development
```

### 4. 下載模型（可選）

模型會在首次運行時自動下載，但你也可以預先下載：

```bash
python download_models.py
```

### 5. 啟動服務

```bash
# 設置環境為開發模式
export OPUS_ENV=development  # Linux/Mac
set OPUS_ENV=development     # Windows

# 啟動後端
python main.py
```

服務會在 http://localhost:8000 啟動

### 6. 測試

```bash
# 健康檢查
curl http://localhost:8000/health

# 測試設備分配
python test_device_allocation.py
```

---

## 📊 當前配置（開發模式）

根據 `config.development.yaml`:

| 模型 | 設備 | 說明 |
|------|------|------|
| STT (Whisper) | GPU (cuda:0) | 語音識別 - 1.5GB VRAM |
| LLM (Qwen2.5-3B) | CPU | 語言模型 - 在 CPU 上運行以節省 VRAM |
| TTS (F5-TTS) | GPU (cuda:0) | 語音合成 - 支援台語 |

**總 VRAM 使用**: ~2-3 GB（開發模式）
**剩餘 VRAM**: ~5-6 GB（適合 RTX 3070 8GB）

---

## 🏭 生產環境部署

詳見 [DEPLOYMENT.md](DEPLOYMENT.md)

簡要步驟：

```bash
# 1. 設置環境
export OPUS_ENV=production

# 2. 使用生產配置
export CONFIG_PATH=config.production.yaml

# 3. 啟動（所有模型在 GPU）
python main.py
```

或使用 Docker：

```bash
docker-compose up -d
```

---

## 🔧 故障排除

### 問題 1: GPU 記憶體不足

**症狀**: `CUDA out of memory`

**解決方案**:
```yaml
# 編輯 config.development.yaml
gpu:
  llm_device: "cpu"  # LLM 移到 CPU
```

### 問題 2: F5-TTS 安裝失敗

**症狀**: `ModuleNotFoundError: No module named 'f5_tts'`

**解決方案**:
```bash
pip install f5-tts
# 或
pip install git+https://github.com/SWivid/F5-TTS.git
```

### 問題 3: 模型下載緩慢

**解決方案**:
```bash
# 使用 Hugging Face 鏡像（中國地區）
export HF_ENDPOINT=https://hf-mirror.com
python main.py
```

### 問題 4: Whisper 模型加載失敗

**症狀**: `qwen_asr not available, falling back to Whisper`

**說明**: 這是正常的，系統會自動使用 Whisper 替代

---

## 🌐 API 端點

- `GET /health` - 健康檢查
- `GET /api/models/status` - 模型狀態
- `WS /ws/{session_id}` - WebSocket 連接（語音對話）
- `POST /api/appointments/create` - 創建掛號
- `GET /api/appointments/{patient_id}` - 查詢掛號

---

## 🧪 測試台語支援

F5-TTS 原生支援台語（通過 DiaMoE-TTS 架構）：

```python
# 在 WebSocket 連接中
{
  "type": "config",
  "language": "nan",  # 台語
  "session_id": "test-session"
}
```

---

## 📝 開發注意事項

### 設備分配策略

**開發環境** (config.development.yaml):
- STT: GPU → 快速轉錄
- LLM: CPU → 節省 VRAM
- TTS: GPU → 快速合成

**生產環境** (config.production.yaml):
- 所有模型: GPU → 最佳性能
- 啟用 vLLM → 支援 350-400 並發

### 支援的語言

- `zh-tw` - 繁體中文（台灣國語）
- `nan` - 台語/閩南語（Taiwanese Hokkien）
- `en` - 英語

---

## 🛡️ 安全檢查

```bash
# 執行安全掃描
python security_check.py

# 安裝安全工具
pip install pip-audit bandit safety

# 依賴漏洞掃描
pip-audit

# 代碼安全掃描
bandit -r . -ll
```

---

## 📚 更多文檔

- [完整部署指南](DEPLOYMENT.md)
- [API 文檔](API.md) (待創建)
- [架構設計](ARCHITECTURE.md) (待創建)

---

## 🆘 獲取幫助

- GitHub Issues: https://github.com/your-org/opus-hospital/issues
- 文檔: https://docs.yourdomain.com
- Email: support@yourdomain.com

---

## 📄 授權

MIT License (或你的授權)
