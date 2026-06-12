# 部署指南

## 📋 專案概述

**專案名稱**: 員工訂餐系統 (LINE OA 整合版)  
**部署環境**: 公司 ASUS GX10 伺服器  
**技術棧**: FastAPI + PostgreSQL + Ollama + LINE Messaging API  
**最後更新**: 2026-06-12

---

## 🎯 專案目標

- ✅ 員工透過 LINE OA 訂餐
- ✅ OCR 自動解析菜單圖片
- ✅ 本地 LLM 處理文字辨識 (零 API 成本)
- ✅ 現金自付，系統僅記錄對帳
- ✅ 每日補助 150 元
- ✅ 訂餐截止 11:30

---

## 📁 專案結構

```
meal-ordering-system/
├── backend/
│   ├── app/
│   │   ├── config/          # 設定檔
│   │   │   ├── database.py  # 資料庫連線
│   │   │   ├── settings.py  # 環境變數
│   │   │   └── rich_menu.py # LINE Rich Menu
│   │   ├── models/          # 資料庫模型
│   │   │   ├── user.py
│   │   │   ├── restaurant.py
│   │   │   ├── menu_item.py
│   │   │   ├── order.py
│   │   │   ├── daily_setting.py
│   │   │   ├── leave_record.py
│   │   │   └── order_log.py
│   │   ├── routes/          # API 路由
│   │   │   ├── main.py      # 健康檢查
│   │   │   ├── line.py      # LINE Webhook
│   │   │   └── ocr.py       # OCR API
│   │   ├── services/        # 業務邏輯
│   │   │   ├── db_service.py    # 資料庫 Service
│   │   │   └── ocr_service.py   # OCR Service
│   │   ├── utils/           # 工具函數
│   │   │   └── line_bot.py  # LINE API 封裝
│   │   ├── scripts/         # 腳本
│   │   │   └── init_db.py   # 資料庫初始化
│   │   └── main.py          # FastAPI 入口
│   ├── requirements.txt     # Python 依賴
│   └── Dockerfile           # Backend 容器
├── ollama/                  # Ollama 設定
│   └── Dockerfile           # Ollama 容器
├── uploads/                 # 上傳檔案目錄
├── docs/                    # 文件
│   ├── line-setup.md        # LINE OA 設定
│   ├── ocr-setup.md         # OCR 設定
│   └── deployment-guide.md  # 本文件
├── docker-compose.yml       # Docker 配置
├── .env.example             # 環境變數範本
├── deploy.sh                # 部署腳本
└── README.md                # 專案說明
```

---

## 🚀 部署步驟

### **步驟 1: 環境準備**

#### **硬體要求**
- CPU: 8 核心以上 (Ryzen 9 5950X 推薦)
- RAM: 16GB 以上 (32GB 推薦)
- GPU: NVIDIA RTX 3060 或更高 (VRAM 12GB+)
- 磁碟: 50GB 以上可用空間

#### **軟體要求**
- Docker Engine 24.0+
- Docker Compose 2.0+
- NVIDIA Container Toolkit (GPU 加速)

#### **安裝 Docker (Windows + WSL)**
```bash
# 在 Windows 上安裝 Docker Desktop
# 1. 下載 https://www.docker.com/products/docker-desktop/
# 2. 安裝時勾選 "Use WSL 2 instead of Hyper-V"
# 3. 啟動 Docker Desktop
# 4. 在 WSL 中執行:
docker --version
docker compose version
```

#### **安裝 NVIDIA Container Toolkit (GPU 加速)**
```bash
# 在 WSL 中執行
curl -s https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y libnvidia-container-tools
sudo systemctl restart docker
```

---

### **步驟 2: 下載專案**

```bash
# 進入部署目錄
cd /home/bonds

# 克隆專案 (已建立 GitHub 倉庫)
git clone https://github.com/bonds520/meal-ordering-system.git
cd meal-ordering-system
```

---

### **步驟 3: 設定環境變數**

#### **3.1 複製範本**
```bash
cp .env.example .env
```

#### **3.2 填寫必要變數**
```bash
# 編輯 .env 檔案
nano .env
```

**必須填寫的變數：**

| 變數 | 說明 | 範例 |
|------|------|------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Channel Access Token | `1234567890abcdef...` |
| `LINE_CHANNEL_SECRET` | LINE Channel Secret | `abcdef1234567890...` |
| `LINE_WEBHOOK_URL` | LINE Webhook URL | `https://your-domain.com/api/line/webhook` |
| `DATABASE_URL` | PostgreSQL 連線字串 | `postgresql://mealuser:mealpass@localhost:5432/meal_db` |
| `OLLAMA_BASE_URL` | Ollama API URL | `http://ollama:11434` |

**完整範例：**
```env
# LINE OA 設定
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here
LINE_CHANNEL_SECRET=your_channel_secret_here
LINE_WEBHOOK_URL=https://your-domain.com/api/line/webhook

# 資料庫設定
DATABASE_URL=postgresql://mealuser:mealpass@localhost:5432/meal_db
DB_USER=mealuser
DB_PASSWORD=mealpass
DB_NAME=meal_db
DB_HOST=postgres
DB_PORT=5432

# Ollama 設定
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3
OLLAMA_CONTEXT_LENGTH=4096
OLLAMA_TEMPERATURE=0.1

# 應用程式設定
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# 上傳檔案設定
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE_MB=10

# 安全設定
SECRET_KEY=your-secret-key-here-change-this-in-production
```

---

### **步驟 4: 啟動服務**

#### **4.1 啟動 Docker Compose**
```bash
cd /home/bonds/meal-ordering-system
docker-compose up -d
```

#### **4.2 檢查服務狀態**
```bash
# 查看所有容器狀態
docker-compose ps

# 預期的輸出:
# NAME                      STATUS
# meal-ordering-backend     Up (healthy)
# meal-ordering-postgres    Up
# meal-ordering-ollama      Up
```

#### **4.3 查看日誌**
```bash
# 查看後端日誌
docker-compose logs -f backend

# 查看資料庫日誌
docker-compose logs -f postgres

# 查看 Ollama 日誌
docker-compose logs -f ollama
```

---

### **步驟 5: 初始化資料庫**

#### **5.1 執行初始化腳本**
```bash
docker-compose exec backend python backend/app/scripts/init_db.py
```

**預期輸出：**
```
✅ 資料庫初始化完成！
📊 已建立 5 家餐廳
📊 已建立 10 道菜單
📊 今日設定：補助 150 元，截止 11:30
```

#### **5.2 驗證資料庫**
```bash
docker-compose exec backend python -c "
from backend.app.database import get_db
from backend.app.models.restaurant import Restaurant
db = next(get_db())
restaurants = db.query(Restaurant).all()
print(f'餐廳數量：{len(restaurants)}')
for r in restaurants:
    print(f'  - {r.name}')
"
```

---

### **步驟 6: 設定 LINE OA**

#### **6.1 取得 LINE 開發者帳號**
1. 前往 [LINE Developers](https://developers.line.biz/)
2. 登入並建立「Provider」
3. 建立「Messaging API」應用
4. 取得 **Channel Access Token** 和 **Channel Secret**

#### **6.2 設定 Webhook URL**
在 LINE Developers 控制台：
1. 進入應用設定
2. 找到 **Webhook** 區塊
3. 勾選 **Enable webhook**
4. 輸入 URL: `https://your-domain.com/api/line/webhook`
5. 點擊 **Save**

**注意**: Webhook URL 必須是 HTTPS，見「步驟 7: 設定反向代理」

#### **6.3 設定 Rich Menu**
```bash
# 測試 Rich Menu 上傳
docker-compose exec backend python -c "
from backend.app.config.rich_menu import RICH_MENU_JSON
import json
print(json.dumps(RICH_MENU_JSON, indent=2, ensure_ascii=False))
"
```

---

### **步驟 7: 設定反向代理 (Nginx + SSL)**

#### **7.1 安裝 Nginx**
```bash
# 在 WSL 中執行
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

#### **7.2 建立 Nginx 配置**
```bash
sudo nano /etc/nginx/sites-available/meal-ordering
```

**配置內容：**
```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替換成你的域名
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL 憑證 (由 Certbot 自動管理)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # 安全標頭
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # LINE Webhook
    location /api/line/webhook {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # OCR API
    location /api/ocr/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 10M;  # 允許上傳 10MB 圖片
    }
    
    # 健康檢查
    location /health {
        proxy_pass http://localhost:8000;
    }
    
    # 靜態檔案 (上傳的圖片)
    location /uploads/ {
        alias /home/bonds/meal-ordering-system/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

#### **7.3 啟用配置**
```bash
# 建立軟連結
sudo ln -s /etc/nginx/sites-available/meal-ordering /etc/nginx/sites-enabled/

# 測試配置
sudo nginx -t

# 重新載入 Nginx
sudo systemctl reload nginx
```

#### **7.4 申請 SSL 憑證**
```bash
# 使用 Certbot 申請 Let's Encrypt 憑證
sudo certbot --nginx -d your-domain.com

# 自動更新設定 (每天檢查，30 天更新一次)
sudo crontab -e
# 加入這行:
0 0 * * * certbot renew --quiet
```

#### **7.5 更新 .env 中的 Webhook URL**
```bash
# 編輯 .env
nano .env

# 更新這行:
LINE_WEBHOOK_URL=https://your-domain.com/api/line/webhook
```

---

### **步驟 8: 下載 Ollama 模型**

#### **8.1 下載 llama3 模型**
```bash
# 方法 1: 直接在容器下載
docker exec -it meal-ordering-ollama ollama pull llama3

# 方法 2: 使用 API (背景下載)
curl -X POST http://localhost:8000/api/ocr/models/pull \
  -F "model_name=llama3"
```

**預期輸出：**
```
pulling manifest...
pulling 8.07 MiB ... 100%
pulling 1.23 MiB ... 100%
success!
```

#### **8.2 驗證模型**
```bash
# 列出已安裝模型
docker exec -it meal-ordering-ollama ollama list

# 或透過 API
curl http://localhost:8000/api/ocr/models
```

---

### **步驟 9: 測試功能**

#### **9.1 健康檢查**
```bash
# 後端服務
curl http://localhost:8000/health

# 資料庫連線
curl http://localhost:8000/health/db

# OCR 服務
curl http://localhost:8000/api/ocr/health
```

**預期輸出：**
```json
{
  "status": "healthy",
  "database": "connected",
  "ollama": "connected",
  "models": ["llama3"]
}
```

#### **9.2 測試 OCR 功能**
```bash
# 準備測試圖片
# 你可以用任何菜單圖片測試

# 上傳並解析
curl -X POST http://localhost:8000/api/ocr/upload \
  -F "file=@test_menu.jpg" \
  -F "restaurant_id=1" \
  -F "date=2026-06-12"
```

#### **9.3 測試 LINE 指令**
```bash
# 用 LINE 追蹤官方帳號後，輸入以下指令:

菜單          # 查看今日菜單
我的訂單      # 查看已訂餐點
訂 三鮮水餃   # 建立訂單
取消訂單      # 取消今日訂單
```

---

## 🔧 常見問題排除

### **問題 1: Docker 啟動失敗**

**症狀**: `docker-compose up` 報錯

**解決方案**:
```bash
# 檢查 Docker 是否運行
docker ps

# 重啟 Docker 服務
sudo systemctl restart docker

# 重新建立容器
docker-compose down
docker-compose up -d
```

### **問題 2: 資料庫連線失敗**

**症狀**: `could not connect to server`

**解決方案**:
```bash
# 檢查 PostgreSQL 容器狀態
docker-compose ps postgres

# 查看日誌
docker-compose logs postgres

# 確認 .env 中的 DATABASE_URL 正確
# 應該是：postgresql://mealuser:mealpass@postgres:5432/meal_db
```

### **問題 3: Ollama 模型下載失敗**

**症狀**: `pulling manifest... 100%` 卡住

**解決方案**:
```bash
# 方法 1: 在 Windows 上先下載，再複製到 WSL
docker pull ollama/ollama
docker run -d --name ollama-test ollama/ollama
docker exec -it ollama-test ollama pull llama3

# 方法 2: 使用國內鏡像 (如果網路不穩)
docker exec -it meal-ordering-ollama \
  OLLAMA_HOST=0.0.0.0 ollama pull llama3
```

### **問題 4: LINE Webhook 測試失敗**

**症狀**: LINE 控制台顯示「Webhook 測試失敗」

**解決方案**:
```bash
# 1. 確認 Nginx 正在運行
sudo systemctl status nginx

# 2. 確認端口 443 開放
sudo netstat -tlnp | grep 443

# 3. 測試 Webhook 端點
curl -X POST https://your-domain.com/api/line/webhook \
  -H "Content-Type: application/json" \
  -d '{"type": "ping"}'

# 4. 查看後端日誌
docker-compose logs -f backend | grep webhook
```

### **問題 5: OCR 辨識速度慢**

**症狀**: 上傳圖片後很久才有回應

**解決方案**:
```bash
# 1. 確認 GPU 被使用
docker exec -it meal-ordering-ollama nvidia-smi

# 2. 如果沒有 GPU 加速，檢查 NVIDIA Container Toolkit
# 重新安裝 (見步驟 1)

# 3. 使用較小的模型 (如果 GPU 記憶體不足)
docker exec -it meal-ordering-ollama ollama pull llama3:8b

# 4. 調整 .env 中的 OLLAMA_MODEL
OLLAMA_MODEL=llama3:8b
```

---

## 📊 監控與維護

### **日常監控**

```bash
# 查看系統資源
docker stats

# 查看容器日誌
docker-compose logs --tail 100

# 查看錯誤日誌
docker-compose logs backend | grep ERROR
```

### **定期維護**

```bash
# 每週: 備份資料庫
docker-compose exec postgres pg_dump -U mealuser meal_db > backup_$(date +%Y%m%d).sql

# 每月: 清理舊的日誌
docker-compose logs --tail 0 backend
docker-compose logs --tail 0 postgres
docker-compose logs --tail 0 ollama

# 每季度: 更新 Docker 映像
docker-compose pull
docker-compose up -d
```

### **日誌輪替設定**

```bash
# 編輯 docker-compose.yml，在 services 下加入:
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 🔐 安全建議

### **1. 環境變數保護**
```bash
# 設定檔案權限
chmod 600 .env

# 加入 .gitignore
echo ".env" >> .gitignore
```

### **2. 資料庫密碼**
```bash
# 使用強密碼 (至少 16 字元，包含大小寫、數字、符號)
# 範例: K8s#2026$MealOrdering@SecurePass!
```

### **3. LINE Token 保護**
```bash
# 定期輪替 Channel Access Token
# 在 LINE Developers 控制台 -> 設定 -> Channel Access Token -> 輪替
```

### **4. SSL 憑證更新**
```bash
# Certbot 會自動更新，但可以手動測試
sudo certbot renew --dry-run
```

### **5. 防火牆設定**
```bash
# 只開放必要端口
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

---

## 📈 進階設定

### **1. 負載平衡 (多實例)**

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
    scaling:
      max_replicas: 10
```

### **2. 監控儀表板 (Prometheus + Grafana)**

```yaml
# docker-compose.yml 新增
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### **3. 自動化備份**

```bash
# 建立備份腳本
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec postgres pg_dump -U mealuser meal_db > /home/bonds/backups/meal_db_${DATE}.sql
# 上傳到雲端 (AWS S3, Google Drive, etc.)
# aws s3 cp /home/bonds/backups/meal_db_${DATE}.sql s3://your-bucket/backups/
EOF

chmod +x backup.sh

# 設定 Cron 每天凌晨 2 點備份
(crontab -l 2>/dev/null; echo "0 2 * * * /home/bonds/meal-ordering-system/backup.sh") | crontab -
```

---

## 📞 支援與聯絡

### **技術支援**
- **專案 GitHub**: https://github.com/bonds520/meal-ordering-system
- **Hermes Agent 文件**: https://hermes-agent.nousresearch.com/docs
- **Ollama 文件**: https://github.com/ollama/ollama
- **LINE Developers**: https://developers.line.biz/

### **聯絡方式**
- **Telegram**: @BondsChang (專案負責人)
- **Email**: (請自行設定)

---

## 📝 部署檢查清單

### **部署前**
- [ ] Docker Engine 已安裝
- [ ] Docker Compose 已安裝
- [ ] NVIDIA Container Toolkit 已安裝 (如需 GPU)
- [ ] 專案已從 GitHub 克隆
- [ ] `.env` 檔案已填寫完整
- [ ] LINE OA 已建立並取得 Token
- [ ] 域名已購買並解析到伺服器 IP

### **部署中**
- [ ] `docker-compose up -d` 成功執行
- [ ] 所有容器狀態為 `Up`
- [ ] 資料庫初始化腳本執行成功
- [ ] Ollama 模型下載完成
- [ ] Nginx 配置已設定
- [ ] SSL 憑證已申請
- [ ] LINE Webhook URL 已設定

### **部署後**
- [ ] 健康檢查全部通過
- [ ] OCR 測試成功
- [ ] LINE 指令測試成功
- [ ] 實際菜單上傳測試成功
- [ ] 訂單建立測試成功
- [ ] 日誌監控已設定
- [ ] 備份腳本已設定

---

## 🎉 部署完成！

恭喜！你的員工訂餐系統已經部署完成。

**下一步建議**:
1. 邀請員工追蹤 LINE OA
2. 測試完整訂餐流程
3. 收集反饋並優化
4. 設定自動備份
5. 建立管理員後台

**祝使用愉快！** 🍽️

---

*文件版本：1.0*  
*最後更新：2026-06-12*  
*作者：Bonds Chang*
