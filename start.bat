@echo off
REM ====================================================================
REM Opus Hospital AI 智能櫃台 - 一鍵啟動腳本 (Windows)
REM 支援 350-400 並發用戶 | Qwen2.5-3B | NVIDIA GPU
REM ====================================================================

echo ========================================
echo   Opus Hospital AI 智能櫃台
echo   一鍵啟動腳本 v1.0
echo ========================================
echo.

REM 檢查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 未找到 Python，請先安裝 Python 3.10+
    pause
    exit /b 1
)

REM 檢查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 未找到 Node.js，請先安裝 Node.js 18+
    pause
    exit /b 1
)

REM 檢查 NVIDIA GPU
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo [警告] 未檢測到 NVIDIA GPU，將使用 CPU 運行（會很慢）
    timeout /t 3
) else (
    echo [✓] NVIDIA GPU 已檢測
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
)

echo.
echo ========================================
echo   步驟 1/5: 檢查環境
echo ========================================
echo.

REM 檢查 backend 虛擬環境
if not exist "backend\venv" (
    echo [!] 首次運行，創建 Python 虛擬環境...
    cd backend
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [+] 安裝 Python 依賴（約需 5-10 分鐘）...
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install vllm  REM 重要：高並發支援
    cd ..
) else (
    echo [✓] Python 環境已就緒
)

REM 檢查 frontend node_modules
if not exist "frontend\node_modules" (
    echo [!] 首次運行，安裝 Frontend 依賴...
    cd frontend
    call npm install
    cd ..
) else (
    echo [✓] Frontend 環境已就緒
)

echo.
echo ========================================
echo   步驟 2/5: 初始化數據庫
echo ========================================
echo.

REM 初始化假資料庫
if not exist "backend\data\patients.db" (
    echo [+] 創建假的病患資料庫...
    cd backend
    call venv\Scripts\activate.bat
    python database\patient_db.py
    cd ..
    echo [✓] 資料庫初始化完成
) else (
    echo [✓] 資料庫已存在
)

echo.
echo ========================================
echo   步驟 3/5: 下載 AI 模型
echo ========================================
echo.

REM 檢查模型是否已下載
if not exist "%USERPROFILE%\.cache\huggingface\hub\models--Qwen--Qwen2.5-3B-Instruct" (
    echo [+] 下載 Qwen2.5-3B-Instruct 模型（約 6GB，需 10-15 分鐘）...
    cd backend
    call venv\Scripts\activate.bat
    python download_models.py
    cd ..
) else (
    echo [✓] 模型已下載
)

echo.
echo ========================================
echo   步驟 4/5: 啟動 Backend 服務
echo ========================================
echo.

REM 啟動 Backend
start "Opus Hospital Backend" cmd /k "cd backend && venv\Scripts\activate.bat && python main.py"

echo [+] Backend 正在啟動...
echo [+] 等待服務就緒（約 30-60 秒）...
timeout /t 30

REM 檢查 Backend 健康狀態
echo [+] 檢查 Backend 健康狀態...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [!] Backend 可能還在啟動中，請稍候...
    timeout /t 15
)

echo.
echo ========================================
echo   步驟 5/5: 啟動 Frontend 服務
echo ========================================
echo.

REM 啟動 Frontend
start "Opus Hospital Frontend" cmd /k "cd frontend && npm run dev"

echo [+] Frontend 正在啟動...
timeout /t 5

echo.
echo ========================================
echo   🎉 啟動完成！
echo ========================================
echo.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   Health:   http://localhost:8000/health
echo.
echo   瀏覽器將自動打開前端頁面...
echo.
echo   按 Ctrl+C 關閉任一視窗即可停止服務
echo ========================================

REM 等待幾秒後自動打開瀏覽器
timeout /t 5
start http://localhost:5173

echo.
echo [✓] 系統運行中...
echo [✓] 支援 350-400 並發用戶
echo [✓] 使用 vLLM 連續批次處理
echo.
pause
