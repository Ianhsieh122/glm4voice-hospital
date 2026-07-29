@echo off
cd /d "C:\Users\ianhs\OneDrive\??\Codes\opus-hospital\backend"
set PYTHONIOENCODING=utf-8
set OPUS_ENV=development
"venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info > server_out.log 2> server_err.log
