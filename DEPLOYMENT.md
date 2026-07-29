# 🚀 部署指南 - Opus Hospital AI 智能櫃台

## 📋 目錄

1. [環境需求](#環境需求)
2. [快速開始](#快速開始)
3. [MI300X GPU 優化部署](#mi300x-gpu-優化部署)
4. [Docker 部署](#docker-部署)
5. [生產環境配置](#生產環境配置)
6. [故障排除](#故障排除)

---

## 環境需求

### 硬體需求

- **GPU**: AMD MI300X (推薦) 或 NVIDIA H100/A100
- **VRAM**: 最少 85GB (70B FP8 模型)
- **RAM**: 最少 32GB
- **儲存**: 最少 500GB (模型快取)

### 軟體需求

- **OS**: Ubuntu 22.04 LTS (推薦) 或 Windows 11
- **Python**: 3.10+
- **Node.js**: 18+
- **CUDA**: 12.0+ (NVIDIA) 或 ROCm 6.2+ (AMD)

---

## 快速開始

### 1. Clone 專案

```bash
git clone https://github.com/your-org/opus-hospital.git
cd opus-hospital
```

### 2. Backend 設置

```bash
cd backend

# 創建虛擬環境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt

# 下載模型（約需 30 分鐘）
python download_models.py

# 配置
cp config.yaml config.local.yaml
# 編輯 config.local.yaml 調整 GPU 設定

# 啟動服務
python main.py
```

### 3. Frontend 設置

```bash
cd ../frontend

# 安裝依賴
npm install

# 配置環境變數
cp .env.example .env
# 編輯 .env 設定 WebSocket URL

# 啟動開發伺服器
npm run dev
```

### 4. 訪問

打開瀏覽器：`http://localhost:5173`

---

## MI300X GPU 優化部署

### ROCm 安裝 (AMD MI300X)

```bash
# 安裝 ROCm 6.2
wget https://repo.radeon.com/amdgpu-install/6.2/ubuntu/jammy/amdgpu-install_6.2.60200-1_all.deb
sudo dpkg -i amdgpu-install_6.2.60200-1_all.deb
sudo amdgpu-install --usecase=rocm

# 驗證安裝
rocm-smi
```

### 優化配置

編輯 `backend/config.yaml`:

```yaml
gpu:
  device: "cuda:0"
  precision: "fp8"  # MI300X 原生 FP8 支援

models:
  llm: "taide/TAIDE-LX-70B-Chat-4bit"  # 70B 模型
```

### 性能驗證

```bash
# 測試 GPU
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"

# 基準測試
cd backend
python -m pytest tests/test_performance.py -v
```

預期指標：
- STT 延遲: < 50ms
- LLM TTFT: < 120ms
- TTS TTFA: < 100ms
- 端到端: < 400ms

---

## Docker 部署

### 使用 Docker Compose

```bash
# 啟動所有服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

### 單獨容器部署

#### Backend

```bash
cd backend
docker build -t opus-hospital-backend .
docker run -d \
  --gpus all \
  -p 8000:8000 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --name opus-backend \
  opus-hospital-backend
```

#### Frontend

```bash
cd frontend
docker build -t opus-hospital-frontend .
docker run -d \
  -p 5173:80 \
  --name opus-frontend \
  opus-hospital-frontend
```

---

## 生產環境配置

### Nginx 反向代理

```nginx
# /etc/nginx/sites-available/opus-hospital

upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:5173;
}

server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

### SSL 配置 (Let's Encrypt)

```bash
# 安裝 Certbot
sudo apt install certbot python3-certbot-nginx

# 獲取證書
sudo certbot --nginx -d your-domain.com

# 自動續期
sudo certbot renew --dry-run
```

### Systemd 服務

#### Backend Service

```ini
# /etc/systemd/system/opus-backend.service

[Unit]
Description=Opus Hospital Backend
After=network.target

[Service]
Type=simple
User=opus
WorkingDirectory=/opt/opus-hospital/backend
Environment="PATH=/opt/opus-hospital/backend/venv/bin"
ExecStart=/opt/opus-hospital/backend/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

啟動服務：

```bash
sudo systemctl enable opus-backend
sudo systemctl start opus-backend
sudo systemctl status opus-backend
```

---

## 監控與日誌

### Prometheus + Grafana

```bash
# 啟動監控棧
docker-compose -f docker-compose.monitoring.yml up -d

# 訪問 Grafana
# http://localhost:3000
# 默認帳號: admin / admin
```

### 日誌收集

```bash
# 查看 Backend 日誌
tail -f backend/logs/opus-hospital.log

# 使用 journalctl (systemd)
sudo journalctl -u opus-backend -f
```

---

## 故障排除

### 問題 1: GPU 不可用

**症狀**: `torch.cuda.is_available()` 返回 `False`

**解決方案**:
```bash
# 檢查 ROCm/CUDA 安裝
rocm-smi  # AMD
nvidia-smi  # NVIDIA

# 重新安裝 PyTorch
pip install torch --index-url https://download.pytorch.org/whl/rocm6.2  # AMD
pip install torch --index-url https://download.pytorch.org/whl/cu121  # NVIDIA
```

### 問題 2: WebSocket 連接失敗

**症狀**: Frontend 顯示「未連線」

**解決方案**:
```bash
# 檢查 Backend 是否運行
curl http://localhost:8000/health

# 檢查防火牆
sudo ufw allow 8000

# 檢查 CORS 設定
# 編輯 backend/main.py 中的 allow_origins
```

### 問題 3: 模型加載失敗

**症狀**: `Failed to load model`

**解決方案**:
```bash
# 清除快取重新下載
rm -rf ~/.cache/huggingface/hub
python download_models.py

# 檢查 VRAM
rocm-smi  # 確保有足夠的 VRAM

# 降低精度
# 編輯 config.yaml: precision: "4bit"
```

### 問題 4: 音頻無法播放

**症狀**: 收到響應但沒有聲音

**解決方案**:
- 檢查瀏覽器麥克風權限
- 打開瀏覽器控制台查看錯誤
- 確認 WebSocket 消息格式正確

### 問題 5: 高延遲

**症狀**: 響應時間 > 1秒

**優化方案**:
```yaml
# config.yaml
gpu:
  precision: "fp8"  # 使用 FP8 (MI300X)

# 啟用批次推理
audio:
  chunk_size: 8192  # 增大 chunk size

# 減少 max_tokens
llm_max_tokens: 150
```

---

## 性能基準

在 AMD MI300X 上的參考性能：

| 指標 | 目標 | 實際 |
|------|------|------|
| STT 延遲 | < 50ms | ~45ms |
| LLM TTFT | < 150ms | ~120ms |
| TTS TTFA | < 100ms | ~97ms |
| 端到端延遲 | < 500ms | ~400ms |
| 吞吐量 | > 40 tok/s | ~52 tok/s |
| 並發用戶 | > 10 | 15+ |
| VRAM 使用 | < 100GB | ~85GB |

---

## 生產環境檢查清單

- [ ] GPU 驅動安裝並驗證
- [ ] 所有模型已下載並測試
- [ ] SSL 證書配置完成
- [ ] 防火牆規則設置正確
- [ ] 日誌輪轉配置
- [ ] 監控告警設置
- [ ] 備份策略就緒
- [ ] 負載測試通過
- [ ] 安全審計完成
- [ ] 文檔更新

---

## 支援

- **GitHub Issues**: https://github.com/your-org/opus-hospital/issues
- **文檔**: https://docs.opus-hospital.ai
- **Discord**: https://discord.gg/opus-hospital

---

**版本**: 1.0.0  
**更新日期**: 2026年7月  
**作者**: Opus Hospital Team
