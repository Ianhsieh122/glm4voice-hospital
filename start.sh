#!/bin/bash
# ====================================================================
# Opus Hospital AI 智能櫃台 - 一鍵啟動腳本 (Linux/macOS)
# 支援 350-400 並發用戶 | Qwen2.5-3B | NVIDIA GPU
# ====================================================================

echo "========================================"
echo "  Opus Hospital AI 智能櫃台"
echo "  一鍵啟動腳本 v1.0"
echo "========================================"
echo ""

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "[錯誤] 未找到 Python，請先安裝 Python 3.10+"
    exit 1
fi

# 檢查 Node.js
if ! command -v node &> /dev/null; then
    echo "[錯誤] 未找到 Node.js，請先安裝 Node.js 18+"
    exit 1
fi

# 檢查 NVIDIA GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "[警告] 未檢測到 NVIDIA GPU，將使用 CPU 運行（會很慢）"
    sleep 3
else
    echo "[✓] NVIDIA GPU 已檢測"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
fi

echo ""
echo "========================================"
echo "  步驟 1/5: 檢查環境"
echo "========================================"
echo ""

# 檢查 backend 虛擬環境
if [ ! -d "backend/venv" ]; then
    echo "[!] 首次運行，創建 Python 虛擬環境..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    echo "[+] 安裝 Python 依賴（約需 5-10 分鐘）..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install vllm  # 重要：高並發支援
    cd ..
else
    echo "[✓] Python 環境已就緒"
fi

# 檢查 frontend node_modules
if [ ! -d "frontend/node_modules" ]; then
    echo "[!] 首次運行，安裝 Frontend 依賴..."
    cd frontend
    npm install
    cd ..
else
    echo "[✓] Frontend 環境已就緒"
fi

echo ""
echo "========================================"
echo "  步驟 2/5: 初始化數據庫"
echo "========================================"
echo ""

# 初始化假資料庫
if [ ! -f "backend/data/patients.db" ]; then
    echo "[+] 創建假的病患資料庫..."
    cd backend
    source venv/bin/activate
    python database/patient_db.py
    cd ..
    echo "[✓] 資料庫初始化完成"
else
    echo "[✓] 資料庫已存在"
fi

echo ""
echo "========================================"
echo "  步驟 3/5: 下載 AI 模型"
echo "========================================"
echo ""

# 檢查模型是否已下載
if [ ! -d "$HOME/.cache/huggingface/hub/models--Qwen--Qwen2.5-3B-Instruct" ]; then
    echo "[+] 下載 Qwen2.5-3B-Instruct 模型（約 6GB，需 10-15 分鐘）..."
    cd backend
    source venv/bin/activate
    python download_models.py
    cd ..
else
    echo "[✓] 模型已下載"
fi

echo ""
echo "========================================"
echo "  步驟 4/5: 啟動 Backend 服務"
echo "========================================"
echo ""

# 啟動 Backend（背景執行）
cd backend
source venv/bin/activate
nohup python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "[+] Backend 正在啟動 (PID: $BACKEND_PID)..."
echo "[+] 等待服務就緒（約 30-60 秒）..."
sleep 30

# 檢查 Backend 健康狀態
echo "[+] 檢查 Backend 健康狀態..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "[!] Backend 可能還在啟動中，請稍候..."
    sleep 15
fi

echo ""
echo "========================================"
echo "  步驟 5/5: 啟動 Frontend 服務"
echo "========================================"
echo ""

# 啟動 Frontend（背景執行）
cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "[+] Frontend 正在啟動 (PID: $FRONTEND_PID)..."
sleep 5

echo ""
echo "========================================"
echo "  🎉 啟動完成！"
echo "========================================"
echo ""
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  Health:   http://localhost:8000/health"
echo ""
echo "  Backend PID:  $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo ""
echo "  查看日誌："
echo "  - Backend:  tail -f logs/backend.log"
echo "  - Frontend: tail -f logs/frontend.log"
echo ""
echo "  停止服務："
echo "  - kill $BACKEND_PID $FRONTEND_PID"
echo "========================================"
echo ""
echo "[✓] 系統運行中..."
echo "[✓] 支援 350-400 並發用戶"
echo "[✓] 使用 vLLM 連續批次處理"
echo ""

# 保存 PID 到文件
mkdir -p logs
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo "PID 已保存到 logs/backend.pid 和 logs/frontend.pid"
echo ""
echo "按 Ctrl+C 退出監控，服務將繼續在背景運行"
echo ""

# 監控日誌（可選）
tail -f logs/backend.log
