# 🎉 模型下載完成！立即使用指南

## ✅ 已完成的工作

### 1. **模型已下載** (總計 8.5GB)
- ✅ **LLM**: Qwen2.5-3B-Instruct **Q4 量化版** (~2GB)
- ✅ **STT**: Whisper-Large-v3-Turbo **FP16** (~3.1GB)
- ✅ **TTS**: Qwen3-TTS **FP16** (~3.4GB)

### 2. **GPU 已檢測**
- GPU: **NVIDIA GeForce RTX 3070**
- VRAM: **8GB**
- 狀態: ✅ 就緒

### 3. **資料庫已初始化**
- 5 位假病患資料
- 5 位假醫師資料
- 支援民國年月日

---

## 🚀 三種啟動方式

### **方式 1: 快速測試 Backend（推薦先試這個）**

雙擊執行：
```
test-backend.bat
```

這會：
1. 啟動 Backend API 服務
2. 自動檢查健康狀態
3. 顯示如何測試

**測試 Backend API：**
- 打開瀏覽器訪問：http://localhost:8000/health
- 應該看到 JSON 回應顯示所有模型已加載

---

### **方式 2: 啟動完整系統（Backend + Frontend）**

#### 步驟 1: 啟動 Backend
雙擊執行：
```
test-backend.bat
```

#### 步驟 2: 啟動 Frontend（新開一個終端）
```cmd
cd frontend
npm install
npm run dev
```

#### 步驟 3: 使用
瀏覽器自動打開 http://localhost:5173

---

### **方式 3: 一鍵啟動（如果 Frontend 已安裝）**

雙擊執行：
```
start.bat
```

會自動啟動 Backend + Frontend

---

## 💬 如何測試對話

### **測試 1: 查詢病患**
1. 點擊麥克風
2. 說：「查詢王小明的資料」
3. AI 會回應病患資料

### **測試 2: 建立掛號**
1. 說：「我要掛心臟內科」
2. AI 會詢問姓名和出生日期
3. 說：「王小明，80年5月15日」
4. AI 會查詢並建立掛號

### **測試 3: 新增病患**
1. 說：「新增病患」
2. AI 會引導你提供：姓名、出生日期、電話
3. 完成後會給你病患編號

### **測試 4: 醫療諮詢（應該被拒絕）**
1. 說：「我胸口痛是什麼問題？」
2. AI 會拒絕並告知：「需要由醫師解答，我無法提供醫療建議」

---

## 📊 查看資料庫

使用 SQLite 工具（如 DB Browser for SQLite）打開：
```
backend\data\patients.db
```

**資料表：**
- `patients` - 病患資料
- `appointments` - 掛號紀錄
- `doctors` - 醫師資料

**假病患資料：**
1. 王小明 - 80年05月15日 - 0912345678
2. 李美玲 - 75年12月20日 - 0923456789
3. 張大華 - 65年08月10日 - 0934567890
4. 陳雅婷 - 90年03月25日 - 0945678901
5. 林志明 - 70年11月08日 - 0956789012

---

## ⚙️ 系統配置

### Backend 配置 (backend/config.yaml)
```yaml
gpu:
  device: "cuda:0"  # NVIDIA RTX 3070
  precision: "fp16"  # FP16
  
models:
  llm: "Qwen/Qwen2.5-3B-Instruct-GGUF"  # Q4 量化
  stt: "openai/whisper-large-v3-turbo"  # FP16
  tts: "Qwen/Qwen3-TTS-12Hz-1.7B-Base"  # FP16

vllm:
  enabled: true  # 支援 350-400 並發
  max_num_seqs: 256
```

### 性能預期（RTX 3070）
| 指標 | 預期值 |
|------|--------|
| STT 延遲 | ~80ms |
| LLM TTFT | ~200ms |
| TTS 延遲 | ~120ms |
| 端到端延遲 | ~500ms |
| 並發用戶 | 100-150 |

**注意**: 350-400 並發需要更大的 GPU（RTX 4090 24GB）

---

## 🐛 常見問題

### 問題 1: Backend 啟動失敗
```cmd
cd backend
python main.py
```
查看錯誤訊息，通常是缺少依賴

**解決方案**:
```cmd
cd backend
pip install -r requirements.txt
```

### 問題 2: CUDA 錯誤
**解決方案**:
```cmd
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 問題 3: vLLM 無法安裝
**解決方案**: RTX 3070 可能不需要 vLLM（並發較少）
編輯 `backend/config.yaml`:
```yaml
vllm:
  enabled: false
```

### 問題 4: 模型加載慢
第一次啟動會比較慢（1-2分鐘），因為要加載 3 個模型

---

## 📝 使用技巧

### 1. **語音輸入清晰**
- 靠近麥克風
- 說話清楚
- 避免背景噪音

### 2. **使用關鍵字**
- 「掛號」、「查詢」、「新增」
- 說出科別：「心臟內科」、「骨科」

### 3. **提供完整資訊**
- 姓名 + 出生日期（民國年）
- 例如：「王小明，80年5月15日」

### 4. **打斷 AI**
- 如果 AI 說太久，點擊「打斷」按鈕
- 系統會立即停止

---

## 🎯 下一步

### 現在可以做的：
1. ✅ 測試 Backend API
2. ✅ 啟動 Frontend 對話
3. ✅ 查看資料庫內容
4. ✅ 測試語音對話

### 未來可以添加：
- [ ] 身份驗證
- [ ] 通話錄音
- [ ] 後台管理界面
- [ ] 真實 HIS 系統整合
- [ ] 更多語言（客語、原住民語）

**告訴我你想要添加哪些功能，我立即開發！**

---

## 📞 立即開始

**最簡單的方式：**

1. 雙擊 `test-backend.bat`
2. 等待啟動
3. 瀏覽器打開 http://localhost:8000/health
4. 看到 ✅ 就代表成功了！

**準備好了嗎？開始吧！** 🚀
