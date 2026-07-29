@echo off
chcp 65001 >nul
echo ========================================
echo   Opus Hospital - 快速測試啟動
echo   NVIDIA RTX 3070 (8GB) 已檢測
echo ========================================
echo.
echo ✅ 模型已下載完成:
echo   - LLM: Qwen2.5-3B-Instruct Q4
echo   - STT: Whisper-v3-Turbo FP16
echo   - TTS: Qwen3-TTS FP16
echo.
echo ✅ 資料庫已初始化 (5位假病患)
echo.
echo 正在啟動 Backend...
echo.

cd backend
start "Opus Hospital Backend" cmd /k "python main.py"

echo.
echo ⏳ 等待 Backend 啟動 (約30秒)...
timeout /t 30 /nobreak >nul

echo.
echo 檢查服務狀態...
curl -s http://localhost:8000/health

echo.
echo ========================================
echo   🎉 Backend 已啟動！
echo ========================================
echo.
echo   Backend API: http://localhost:8000
echo   健康檢查:    http://localhost:8000/health
echo.
echo   測試 WebSocket: ws://localhost:8000/ws/conversation
echo.
echo ========================================
echo   如何使用:
echo ========================================
echo.
echo   1. 保持此視窗開啟 (Backend 運行中)
echo   2. 開啟另一個終端啟動 Frontend:
echo      cd frontend
echo      npm install
echo      npm run dev
echo   3. 瀏覽器打開: http://localhost:5173
echo.
echo   或者直接測試 API:
echo   - 健康檢查: curl http://localhost:8000/health
echo   - 查看病患: 使用 SQLite 工具打開 backend\data\patients.db
echo.
pause
