# 🚀 Opus Hospital - 快速啟動指南

## ✅ 確認：F5-TTS 不支援台語

經過深入研究，我發現：
- **F5-TTS 基礎模型**：只支援英語和中文（普通話）
- **真正支援台語的方案**：
  1. **CosyVoice 3.0** - 支援 18+ 中文方言，包括閩南語（台語）✅
  2. **DiaMoE-TTS** - 支援 9 種中文方言，包括 Hokkien ✅
  3. **Breeze Taigi** - 專門為台語設計 ✅

由於 CosyVoice 安裝較複雜，當前版本使用 **文字回應模式**，可稍後升級到 CosyVoice。

---

## 🎯 當前系統功能

### ✅ 已實現
1. **STT (語音識別)** - Whisper Large v3 Turbo
   - 支援繁體中文、英語
   - 運行在 GPU
   
2. **LLM (對話模型)** - Qwen 2.5-3B
   - 完整的醫療對話邏輯
   - 運行在 CPU（開發模式）
   
3. **Web 界面** - 完整功能
   - 語音對話
   - 掛號管理
   - 取消掛號
   - 更改掛號
   - 查詢掛號

4. **數據庫** - SQLite
   - 病患管理
   - 掛號記錄
   - 民國年月日支援

### 🔄 待升級
- **TTS (語音合成)** - 當前使用文字回應
  - 計劃升級到 CosyVoice 3.0 以支援台語

---

## 📥 快速安裝

### 1. 安裝依賴

```bash
cd backend

# 如果還沒有虛擬環境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安裝基本依賴
pip install -r requirements.txt
```

### 2. 設置環境

```bash
# 複製環境變量
copy .env.example .env

# 編輯 .env 設置開發模式
# OPUS_ENV=development
```

---

## 🚀 啟動服務

### 方法 1：使用簡化啟動腳本（推薦）

```bash
# 設置開發環境
set OPUS_ENV=development

# 啟動服務（會自動載入所有模型）
python start.py
```

啟動後會看到：
```
🏥 Opus Hospital AI Reception System
環境: development
✅ GPU: NVIDIA GeForce RTX 3070
💾 VRAM: 8.00 GB
📦 載入模型...
1/2 載入 STT (Whisper)...
  ✅ STT 已載入
2/2 載入 LLM (Qwen2.5-3B)...
  ✅ LLM 已載入
🎉 所有服務就緒！
🌐 Web 界面: http://localhost:8000
```

### 方法 2：使用原始 main.py

```bash
python main.py
```

---

## 🌐 訪問 Web 界面

打開瀏覽器訪問：
```
http://localhost:8000
```

你會看到：
- **左側**：語音對話界面
  - 點擊麥克風按鈕開始說話
  - 選擇語言（繁體中文/英語）
  - 查看對話歷史
  
- **右側**：掛號管理
  - 新增掛號
  - 查看掛號列表
  - 更改/取消掛號

---

## 🎤 使用語音對話

1. **點擊麥克風按鈕** 🎙️
2. **開始說話**（例如："我要掛號"）
3. **再次點擊停止錄音**
4. 系統會：
   - 轉錄你的語音
   - AI 理解並回應
   - 顯示文字回應

### 對話範例

```
用戶: 我要掛號
助理: 好的，請問您的姓名是？

用戶: 我叫王小明
助理: 王小明先生/小姐您好，請問您的出生日期？

用戶: 80年5月15日
助理: 好的，請問要掛哪一科？

用戶: 內科
助理: 內科，請問要預約哪位醫師？

...
```

---

## 📋 使用掛號功能

### 新增掛號

1. 切換到「新增掛號」頁籤
2. 填寫表單：
   - 病患姓名 *
   - 出生日期（民國）* 例如：80/05/15
   - 電話 *
   - 科別 *
   - 醫師
   - 掛號日期 *
   - 掛號時間 *
   - 備註（選填）
3. 點擊「確認掛號」

### 查看掛號

1. 切換到「掛號列表」頁籤
2. 查看所有掛號記錄
3. 每個掛號卡片顯示：
   - 病患姓名、科別
   - 日期時間
   - 醫師
   - 狀態

### 管理掛號

每個掛號記錄有兩個按鈕：
- **✏️ 更改** - 修改掛號信息
- **❌ 取消** - 取消掛號

---

## 🧪 測試

### 1. 測試健康檢查

```bash
curl http://localhost:8000/health
```

應該返回：
```json
{
  "status": "healthy",
  "models": {
    "stt": true,
    "llm": true,
    "tts": false
  }
}
```

### 2. 測試設備分配

```bash
python test_device_allocation.py
```

### 3. 測試掛號 API

```bash
# 創建掛號
curl -X POST http://localhost:8000/api/appointments/create \
  -H "Content-Type: application/json" \
  -d '{
    "patient_name": "王小明",
    "birth_date_roc": "80/05/15",
    "phone": "0912345678",
    "department": "內科",
    "doctor": "王醫師",
    "appointment_date": "2026-08-01",
    "appointment_time": "09:00"
  }'

# 查詢所有掛號
curl http://localhost:8000/api/appointments/list
```

---

## 🔄 升級到 CosyVoice（支援台語）

如果你想要完整的台語 TTS 支援：

```bash
# 1. 安裝 CosyVoice
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git third_party/CosyVoice
cd third_party/CosyVoice
pip install -r requirements.txt

# 2. 下載模型
python -c "
from huggingface_hub import snapshot_download
snapshot_download('FunAudioLLM/Fun-CosyVoice3-0.5B-2512', local_dir='../../models/CosyVoice3-0.5B')
"

# 3. 更新配置
# 編輯 config.development.yaml
# models:
#   tts: "models/CosyVoice3-0.5B"
#   tts_model_name: "CosyVoice3-0.5B"

# 4. 使用 CosyVoice TTS
# 修改 start.py 或 main.py 導入：
# from models.tts_model_cosyvoice import TTSModelCosyVoice as TTSModel
```

---

## 📊 系統要求

### 最低配置（開發模式）
- CPU: 4+ cores
- RAM: 16GB
- GPU: NVIDIA 8GB VRAM (例如 RTX 3070)
- 磁碟: 50GB

### 推薦配置（生產模式）
- CPU: 8+ cores
- RAM: 32GB
- GPU: NVIDIA 24GB VRAM (例如 RTX 4090)
- 磁碟: 200GB SSD

---

## 🐛 故障排除

### 問題 1：模型下載慢

```bash
# 使用 HF 鏡像
set HF_ENDPOINT=https://hf-mirror.com
python start.py
```

### 問題 2：GPU 記憶體不足

編輯 `config.development.yaml`:
```yaml
gpu:
  llm_device: "cpu"  # LLM 移到 CPU
```

### 問題 3：WebSocket 連接失敗

檢查防火牆設置，確保 8000 端口開放。

### 問題 4：語音錄製失敗

確保瀏覽器有麥克風權限。

---

## 📚 API 文檔

### 掛號相關

```
POST   /api/appointments/create        - 創建掛號
GET    /api/appointments/list          - 獲取所有掛號
POST   /api/appointments/cancel/{id}   - 取消掛號
POST   /api/appointments/update/{id}   - 更新掛號
```

### 系統相關

```
GET    /health                          - 健康檢查
GET    /api/models/status               - 模型狀態
WS     /ws/{session_id}                 - WebSocket 對話
```

---

## 🎉 完成！

你現在有一個完整的 AI 智能櫃台系統：

✅ 語音識別（STT）- GPU  
✅ 對話生成（LLM）- CPU（開發模式）  
✅ Web 界面 - 完整功能  
✅ 掛號管理 - CRUD 操作  
✅ 數據庫 - 民國年月日  
🔄 台語 TTS - 可升級到 CosyVoice  

---

## 💡 下一步

1. ✅ **測試基本功能** - 語音對話和掛號
2. 🔄 **升級 TTS** - 安裝 CosyVoice 支援台語
3. 🚀 **生產部署** - 使用 Docker 或 Systemd
4. 📊 **監控** - 添加 Prometheus + Grafana
5. 🔒 **安全** - 啟用 HTTPS 和認證

---

有任何問題請查看：
- 📖 完整文檔：`DEPLOYMENT.md`
- 🔍 總結：`SUMMARY.md`
- 🐛 日誌：`logs/opus-hospital-dev.log`
