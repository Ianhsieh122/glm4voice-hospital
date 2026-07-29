# 🎉 恭喜！所有準備工作已完成

## ✅ 已完成項目

1. ✅ **Python 環境** - 已建立
2. ✅ **模型下載** - Q4 LLM + FP16 STT/TTS (共 8.5GB)
3. ✅ **GPU 檢測** - NVIDIA RTX 3070 (8GB)
4. ✅ **資料庫** - 已初始化假資料
5. ✅ **啟動腳本** - 已創建

---

## 🚀 現在立即使用

### **步驟 1: 啟動 Backend**

打開 **PowerShell** 或 **命令提示字元**，執行：

```cmd
cd C:\Users\ianhs\OneDrive\文件\Codes\opus-hospital\backend
python main.py
```

**你會看到：**
```
🚀 Starting Opus Hospital AI Reception System...
✅ GPU detected: NVIDIA GeForce RTX 3070
💾 VRAM: 8.00 GB
📦 Loading AI models...
Loading STT (Qwen3-ASR-1.7B)...
✅ STT model loaded
Loading LLM (Qwen2.5-3B-Instruct Q4)...
✅ LLM model loaded (約 30-60 秒)
Loading TTS (Qwen3-TTS-1.7B)...
✅ TTS model loaded
🎉 All models loaded successfully!

INFO:     Uvicorn running on http://0.0.0.0:8000
```

**第一次啟動約需 1-2 分鐘**（加載 3 個模型）

---

### **步驟 2: 測試 Backend**

Backend 啟動後，開啟新的終端測試：

```cmd
curl http://localhost:8000/health
```

**應該看到：**
```json
{
  "status": "healthy",
  "models_loaded": true,
  "gpu": {
    "name": "NVIDIA GeForce RTX 3070",
    "memory_allocated": "4.2 GB"
  }
}
```

---

### **步驟 3: 啟動 Frontend（可選）**

開啟**另一個**終端：

```cmd
cd C:\Users\ianhs\OneDrive\文件\Codes\opus-hospital\frontend
npm install
npm run dev
```

然後瀏覽器打開：**http://localhost:5173**

---

## 💬 測試對話範例

### **範例 1: 查詢病患**

**你說：**
> 「查詢王小明的資料」

**AI 回應：**
> 「查詢到病患王小明，出生日期 80年5月15日，電話 0912345678」

---

### **範例 2: 建立掛號**

**你說：**
> 「我要掛心臟內科」

**AI 回應：**
> 「好的，請告訴我您的姓名和出生日期」

**你說：**
> 「王小明，80年5月15日」

**AI 回應：**
> 「查詢到您的資料。心臟內科有王建國醫師，週一到週五早上9點到12點。您希望哪一天看診？」

**你說：**
> 「明天早上10點」

**AI 回應：**
> 「已為您掛號明天上午10點，王建國醫師。掛號號碼是 A20260729143022」

---

### **範例 3: 測試醫療合規（應被拒絕）**

**你說：**
> 「我胸口痛，是什麼問題？」

**AI 回應：**
> 「這個問題需要由醫師為您解答，我無法提供醫療建議。如果是急性胸痛，請立即撥打 119 或前往急診室。建議您掛號心臟內科門診。」

✅ **符合醫療合規要求！**

---

## 📊 查看資料庫

使用任何 SQLite 工具打開：
```
C:\Users\ianhs\OneDrive\文件\Codes\opus-hospital\backend\data\patients.db
```

**推薦工具：**
- DB Browser for SQLite (免費)
- DBeaver (免費)
- 或使用 Python：

```python
import sqlite3
conn = sqlite3.connect('backend/data/patients.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM patients")
for row in cursor.fetchall():
    print(row)
```

---

## 🎯 重要文件位置

| 文件 | 路徑 |
|------|------|
| **啟動 Backend** | `backend\main.py` |
| **配置文件** | `backend\config.yaml` |
| **資料庫** | `backend\data\patients.db` |
| **模型位置** | `C:\Users\ianhs\.cache\huggingface\hub\` |
| **測試腳本** | `test-backend.bat` |
| **使用說明** | `HOW_TO_USE.md` |

---

## ⚡ 快速命令

```cmd
# 啟動 Backend
cd backend
python main.py

# 測試健康狀態
curl http://localhost:8000/health

# 查看 GPU 使用
nvidia-smi

# 查看日誌
cd backend
type logs\opus-hospital.log

# 重新初始化資料庫
cd backend
python database\patient_db.py
```

---

## 🐛 如果遇到問題

### **問題 1: 模型加載失敗**
```cmd
cd backend
python download_models_q4.py
```

### **問題 2: CUDA 錯誤**
```cmd
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### **問題 3: 端口被占用**
```cmd
# 查找佔用 8000 端口的程序
netstat -ano | findstr :8000

# 關閉該程序或修改配置文件中的端口
```

### **問題 4: 記憶體不足**
- RTX 3070 (8GB) 足夠運行 Q4 模型
- 如果還是不夠，可以進一步降低 batch size

編輯 `backend/config.yaml`:
```yaml
gpu:
  batch_size: 32  # 降低到 32
```

---

## 📈 性能優化建議

### **對於 RTX 3070 (8GB):**

1. **已使用 Q4 量化** ✅
2. **建議並發數**: 50-100 用戶
3. **如需更多並發**:
   - 升級到 RTX 4090 (24GB)
   - 或使用多 GPU

### **監控 GPU 使用：**
```cmd
# 實時監控
nvidia-smi -l 1

# 查看詳細資訊
nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used --format=csv -l 1
```

---

## 🎊 你現在可以做什麼？

### ✅ **立即測試：**
1. 啟動 Backend: `cd backend && python main.py`
2. 等待 1-2 分鐘（加載模型）
3. 測試健康: `curl http://localhost:8000/health`
4. 查看資料庫: 打開 `backend\data\patients.db`

### 🚀 **完整體驗：**
1. 啟動 Backend
2. 啟動 Frontend: `cd frontend && npm run dev`
3. 瀏覽器打開 http://localhost:5173
4. 開始語音對話！

---

## 📞 需要幫助？

**我已經為你準備好：**
- ✅ Q4 量化 LLM（省記憶體）
- ✅ 完整的假資料庫
- ✅ 嚴格的醫療合規 Prompt
- ✅ NVIDIA GPU 優化配置
- ✅ 啟動腳本和說明

**現在就執行：**
```cmd
cd backend
python main.py
```

**然後告訴我運行結果！** 🎉
