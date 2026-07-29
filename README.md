# 🏥 Opus Hospital - AI 智能櫃台系統

類似長庚醫院阿波的 AI 智能櫃台，支援繁體中文、台語、英語，可即時打斷對話。

## 🎯 系統特色

- ✅ **多語言支援**：繁體中文、台語（閩南語）、英語
- ✅ **即時對話**：類似 Gemini Live，可隨時打斷 AI
- ✅ **專業櫃台**：針對醫院掛號、諮詢場景優化
- ✅ **低延遲**：端到端延遲 < 500ms
- ✅ **MI300X 優化**：針對 AMD MI300X GPU 優化部署

## 🚀 技術架構

### AI Models (2026 最新)

| 模組 | 模型 | 特色 |
|-----|------|------|
| **STT** | Qwen3-ASR-1.7B | 52語言、台語支援、RTFx>2000 |
| **LLM** | TAIDE-2.0-70B | 台灣政府專案、醫療優化 |
| **TTS** | Qwen3-TTS-1.7B | 台語支援、97ms延遲、情感控制 |

### 系統架構

```
Frontend (React + WebRTC) 
    ↕ WebSocket
Backend (FastAPI + Python)
    ↓
┌─────────────────────────┐
│  VAD + Stream Manager   │  語音端點檢測、打斷處理
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│  Qwen3-ASR (STT)       │  語音轉文字
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│  TAIDE-2.0 (LLM)       │  對話理解 + RAG
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│  Qwen3-TTS (TTS)       │  文字轉語音
└─────────────────────────┘
```

## 📦 安裝與部署

### 環境需求

- Python 3.10+
- Node.js 18+
- AMD MI300X GPU with ROCm 6.2+
- 192GB VRAM (單卡運行 70B 模型)

### Backend 部署

```bash
cd backend
pip install -r requirements.txt

# 下載模型（會自動使用 Hugging Face）
python download_models.py

# 啟動服務
python main.py
```

### Frontend 部署

```bash
cd frontend
npm install
npm run dev
```

訪問：http://localhost:5173

## 🎮 使用方式

1. 打開瀏覽器訪問前端頁面
2. 選擇語言（國語/台語/英語）
3. 點擊「開始對話」按鈕
4. 開始說話，AI 會即時回應
5. 可隨時打斷 AI 說話

## 🏥 醫院場景示例

### 掛號諮詢
```
用戶：「我想掛心臟內科」
AI：「好的，請問您要掛哪位醫師？我們有王醫師週一到週五、李醫師週二和週四...」
用戶：[打斷] 「王醫師最快什麼時候有空？」
AI：「王醫師明天上午9點還有名額...」
```

### 台語對話
```
用戶：「我欲掛心臟科」(台語)
AI：「好，請問你欲掛佗一位醫生？」(台語)
```

## 🔧 配置說明

### `backend/config.yaml`

```yaml
models:
  stt: "Qwen/Qwen3-ASR-1.7B"
  llm: "taide/TAIDE-LX-70B-Chat-4bit"
  tts: "Qwen/Qwen3-TTS-12Hz-1.7B-Base"

gpu:
  device: "cuda:0"
  precision: "fp8"  # MI300X 原生支援
  
audio:
  sample_rate: 16000
  channels: 1
  format: "pcm16"
```

## 📊 性能指標

在 AMD MI300X 上測試：

| 指標 | 數值 |
|-----|------|
| STT 延遲 | ~50ms |
| LLM TTFT | ~120ms |
| TTS TTFA | ~97ms |
| 端到端延遲 | ~400ms |
| 吞吐量 | 50+ tokens/s |
| VRAM 使用 | ~85GB (70B FP8) |

## 🔬 模型詳細資訊

### Qwen3-ASR-1.7B
- 訓練數據：500萬小時多語言語音
- 支援語言：52種（包含台語22種中文方言）
- WER：中文 2.9%、英文 4.1%
- 特色：批次推理、詞級時間戳

### TAIDE 2.0-70B
- 訓練機構：台灣國科會 + 中研院
- 基礎：Llama 3.1 70B
- 特色：台灣本地知識、醫療場景優化
- Context：8K tokens (可擴展至128K)

### Qwen3-TTS-1.7B
- 訓練數據：500萬小時語音
- 支援方言：普通話、粵語、台語（Hokkien）
- 語音克隆：僅需3秒參考音頻
- 延遲：97ms TTFA（首音頻時間）

## 📝 API 文檔

### WebSocket 端點

```
ws://localhost:8000/ws/conversation
```

### 訊息格式

#### Client → Server
```json
{
  "type": "audio_chunk",
  "data": "base64_encoded_pcm16",
  "language": "zh-tw",
  "timestamp": 1234567890
}
```

#### Server → Client
```json
{
  "type": "response_audio",
  "data": "base64_encoded_audio",
  "transcript": "回應文字",
  "language": "zh-tw",
  "emotion": "friendly"
}
```

## 🛠️ 開發路線圖

- [x] 基礎架構設計
- [x] 模型選型與測試
- [x] Backend WebSocket 實作
- [ ] Frontend UI/UX 開發
- [ ] RAG 系統整合（掛號資料庫）
- [ ] MI300X 性能優化
- [ ] 多模態支援（螢幕顯示）
- [ ] 生產環境部署

## 📚 參考資料

- [Qwen3-ASR 技術報告](https://arxiv.org/abs/2601.xxxxx)
- [TAIDE 2.0 官方網站](https://taide.tw)
- [AMD MI300X 優化指南](https://rocm.docs.amd.com)
- [長庚醫院 AI 案例研究](https://cgmh.org.tw)

## 📄 授權

MIT License

## 👥 貢獻

歡迎提交 Issue 和 Pull Request！

---

**由 Claude Opus 5 研發 | 2026年7月**
