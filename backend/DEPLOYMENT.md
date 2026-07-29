# Production Deployment - Opus Hospital AI Reception

## 系統需求

### 硬體需求
- **CPU**: 8+ cores (Intel Xeon or AMD EPYC)
- **RAM**: 32GB+ 
- **GPU**: NVIDIA GPU with 24GB+ VRAM (建議 RTX 4090, A100, or H100)
- **Storage**: 200GB+ SSD
- **Network**: 1Gbps+ bandwidth for 350-400 concurrent users

### 軟體需求
- **OS**: Ubuntu 22.04 LTS or RHEL 9
- **Python**: 3.10 or 3.11
- **CUDA**: 12.1+
- **Docker**: 24.0+ (optional)
- **Nginx**: 1.18+ (reverse proxy)

---

## 部署步驟

### 1. 環境準備

```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝必要工具
sudo apt install -y git python3.10 python3.10-venv python3-pip \
  nvidia-driver-535 cuda-toolkit-12-1 nginx certbot

# 驗證 GPU
nvidia-smi
```

### 2. 克隆倉庫

```bash
cd /opt
sudo git clone https://github.com/your-org/opus-hospital.git
cd opus-hospital/backend
sudo chown -R $USER:$USER /opt/opus-hospital
```

### 3. 創建虛擬環境

```bash
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### 4. 安裝依賴

```bash
# 安裝 PyTorch with CUDA
pip install torch==2.3.0+cu121 torchaudio==2.3.0+cu121 \
  --index-url https://download.pytorch.org/whl/cu121

# 安裝其他依賴
pip install -r requirements.txt

# 安裝 F5-TTS
pip install f5-tts
```

### 5. 下載模型

```bash
# 創建模型目錄
mkdir -p models

# 下載模型 (自動從 Hugging Face)
python download_models.py

# 或使用預下載的模型
# scp user@server:/path/to/models/* ./models/
```

### 6. 配置環境變量

```bash
# 創建 .env 文件
cat > .env << EOF
OPUS_ENV=production
CONFIG_PATH=config.production.yaml
HF_TOKEN=your_huggingface_token
CUDA_VISIBLE_DEVICES=0
EOF
```

### 7. 配置生產環境

編輯 `config.production.yaml`:

```yaml
gpu:
  stt_device: "cuda:0"
  llm_device: "cuda:0"
  tts_device: "cuda:0"

server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  cors_origins:
    - "https://yourdomain.com"
  
rate_limiting:
  enabled: true
  requests_per_minute: 60
```

### 8. 安全性檢查

```bash
# 安裝安全工具
pip install pip-audit bandit safety

# 執行安全掃描
python security_check.py

# 修復所有發現的問題
```

### 9. 設置 Systemd 服務

```bash
sudo nano /etc/systemd/system/opus-hospital.service
```

```ini
[Unit]
Description=Opus Hospital AI Reception Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/opus-hospital/backend
Environment="PATH=/opt/opus-hospital/backend/venv/bin"
Environment="OPUS_ENV=production"
ExecStart=/opt/opus-hospital/backend/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 啟用並啟動服務
sudo systemctl daemon-reload
sudo systemctl enable opus-hospital
sudo systemctl start opus-hospital
sudo systemctl status opus-hospital
```

### 10. 配置 Nginx 反向代理

```bash
sudo nano /etc/nginx/sites-available/opus-hospital
```

```nginx
upstream opus_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy settings
    location / {
        proxy_pass http://opus_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;
    limit_req zone=api_limit burst=10 nodelay;
}
```

```bash
# 啟用站點
sudo ln -s /etc/nginx/sites-available/opus-hospital /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 11. 設置 SSL 證書

```bash
# 使用 Let's Encrypt
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 自動續期
sudo certbot renew --dry-run
```

### 12. 配置防火牆

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
sudo ufw status
```

---

## 監控與日誌

### 日誌管理

```bash
# 查看服務日誌
sudo journalctl -u opus-hospital -f

# 查看應用日誌
tail -f logs/opus-hospital.log

# 日誌輪轉配置
sudo nano /etc/logrotate.d/opus-hospital
```

```
/opt/opus-hospital/backend/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 ubuntu ubuntu
    sharedscripts
    postrotate
        systemctl reload opus-hospital > /dev/null 2>&1 || true
    endscript
}
```

### Prometheus 監控

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'opus-hospital'
    static_configs:
      - targets: ['localhost:9090']
```

---

## 備份策略

### 數據庫備份

```bash
# 每日備份腳本
cat > /opt/opus-hospital/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/opt/backups/opus-hospital
mkdir -p $BACKUP_DIR

# 備份數據庫
cp /opt/opus-hospital/backend/data/patients.db \
   $BACKUP_DIR/patients_$DATE.db

# 壓縮舊備份
find $BACKUP_DIR -name "*.db" -mtime +7 -exec gzip {} \;

# 刪除 30 天前的備份
find $BACKUP_DIR -name "*.db.gz" -mtime +30 -delete
EOF

chmod +x /opt/opus-hospital/backup.sh

# 添加到 crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/opus-hospital/backup.sh") | crontab -
```

---

## 性能優化

### 1. GPU 記憶體優化

```yaml
# config.production.yaml
vllm:
  gpu_memory_utilization: 0.85
  max_num_seqs: 256
```

### 2. 並發優化

```yaml
server:
  workers: 4  # CPU cores / 2
  max_connections: 500
```

### 3. 系統調優

```bash
# /etc/sysctl.conf
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 8192
net.core.netdev_max_backlog = 5000
fs.file-max = 2097152

sudo sysctl -p
```

---

## 故障排除

### 常見問題

**1. GPU 記憶體不足**
```bash
# 降低 batch size
# 降低 gpu_memory_utilization
# 使用模型量化版本
```

**2. WebSocket 連接斷開**
```bash
# 檢查 Nginx timeout 設置
# 增加 proxy_read_timeout
```

**3. 模型加載失敗**
```bash
# 檢查 CUDA 版本
nvidia-smi

# 檢查磁碟空間
df -h

# 檢查模型文件完整性
python -c "from transformers import AutoModel; AutoModel.from_pretrained('model_name')"
```

### 健康檢查

```bash
# 檢查服務狀態
curl http://localhost:8000/health

# 檢查 GPU 使用率
nvidia-smi -l 1

# 檢查連接數
netstat -an | grep :8000 | wc -l
```

---

## 更新與維護

### 更新代碼

```bash
cd /opt/opus-hospital
git pull origin main
source backend/venv/bin/activate
pip install -r backend/requirements.txt
sudo systemctl restart opus-hospital
```

### 更新模型

```bash
cd /opt/opus-hospital/backend
source venv/bin/activate
python download_models.py --update
sudo systemctl restart opus-hospital
```

---

## 安全最佳實踐

1. **定期更新依賴**: `pip install --upgrade -r requirements.txt`
2. **啟用 HTTPS**: 使用 Let's Encrypt 證書
3. **啟用速率限制**: 防止 DDoS 攻擊
4. **啟用日誌監控**: 及時發現異常
5. **定期備份**: 自動化備份數據庫
6. **最小權限原則**: 使用專用用戶運行服務
7. **防火牆配置**: 只開放必要端口
8. **定期安全掃描**: 使用 `security_check.py`

---

## 擴展與高可用

### 負載均衡 (多實例)

```nginx
upstream opus_backend {
    least_conn;
    server 192.168.1.101:8000;
    server 192.168.1.102:8000;
    server 192.168.1.103:8000;
}
```

### GPU 集群

```yaml
# config.production.yaml
gpu:
  devices: ["cuda:0", "cuda:1", "cuda:2", "cuda:3"]
  load_balancing: "round_robin"
```

---

## 支援

- **文檔**: https://docs.yourdomain.com
- **Issue Tracker**: https://github.com/your-org/opus-hospital/issues
- **Email**: support@yourdomain.com
