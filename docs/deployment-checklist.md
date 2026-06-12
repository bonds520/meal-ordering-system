# 部署檢查清單

## 📋 概覽

**專案**: 員工訂餐系統 (LINE OA 整合版)  
**部署日期**: 2026-06-13 (明天)  
**部署地點**: 公司 ASUS GX10 伺服器  
**負責人**: Bonds Chang

---

## ✅ 已完成項目

### **1. 程式碼開發**
- [x] FastAPI 後端核心
- [x] PostgreSQL 資料庫模型 (7 個)
- [x] LINE OA Webhook 整合
- [x] OCR 辨識服務 (Ollama + Llama3)
- [x] 訂單管理邏輯
- [x] 用戶管理邏輯
- [x] 菜單管理邏輯
- [x] 資料庫初始化腳本
- [x] Docker Compose 配置

### **2. 文件準備**
- [x] 部署指南 (`docs/deployment-guide.md`)
- [x] LINE OA 設定指南 (`docs/line-setup.md`)
- [x] OCR 設定指南 (`docs/ocr-setup.md`)
- [x] 部署檢查清單 (本文件)
- [x] README.md

### **3. Git 版本控制**
- [x] GitHub 倉庫建立 (`bonds520/meal-ordering-system`)
- [x] 程式碼推送完成
- [x] 最新 Commit: "📸 實作 OCR 辨識功能"

---

## 📝 部署前準備 (在家完成)

### **A. 環境變數設定**

#### **1. LINE OA 設定**
- [ ] 建立 LINE Developer 帳號
- [ ] 建立 Messaging API 應用
- [ ] 取得 **Channel Access Token**
- [ ] 取得 **Channel Secret**
- [ ] 記錄到 `.env` 檔案

#### **2. 域名設定**
- [ ] 購買域名 (或確認現有域名)
- [ ] 設定 DNS A 記錄指向公司 IP
- [ ] 等待 DNS 解析生效 (通常 1-24 小時)

#### **3. 環境變數範本**
```bash
# 準備 .env 檔案，明天帶到公司
cp .env.example .env.deployment

# 填入以下變數:
LINE_CHANNEL_ACCESS_TOKEN=???
LINE_CHANNEL_SECRET=???
LINE_WEBHOOK_URL=https://your-domain.com/api/line/webhook
DB_PASSWORD=???  # 設定強密碼
SECRET_KEY=???   # 產生隨機金鑰
```

#### **4. 產生隨機金鑰**
```bash
# 產生 SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 產生 DB_PASSWORD
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

---

## 🚀 部署日步驟 (在公司執行)

### **步驟 1: 環境檢查** (10 分鐘)

```bash
# 1.1 檢查 Docker 版本
docker --version          # 應 >= 24.0
docker compose version    # 應 >= 2.0

# 1.2 檢查 NVIDIA 驅動 (GPU 加速)
nvidia-smi               # 應顯示 GPU 資訊
docker info | grep nvidia # 應有 NVIDIA 相關設定

# 1.3 檢查系統資源
free -h                  # RAM 應 >= 16GB
df -h                    # 磁碟應 >= 50GB 可用
nproc                    # CPU 核心應 >= 8
```

**預期結果**:
- ✅ Docker 正常運行
- ✅ NVIDIA 驅動已安裝
- ✅ 系統資源充足

### **步驟 2: 安裝必要軟體** (15 分鐘)

```bash
# 2.1 更新系統
sudo apt-get update && sudo apt-get upgrade -y

# 2.2 安裝 Docker (如果尚未安裝)
# 參考：https://docs.docker.com/engine/install/ubuntu/

# 2.3 安裝 NVIDIA Container Toolkit
curl -s https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y libnvidia-container-tools
sudo systemctl restart docker

# 2.4 安裝 Nginx
sudo apt-get install -y nginx

# 2.5 安裝 Certbot (SSL 憑證)
sudo apt-get install -y certbot python3-certbot-nginx
```

### **步驟 3: 下載專案** (5 分鐘)

```bash
# 3.1 進入部署目錄
cd /home/bonds

# 3.2 克隆專案
git clone https://github.com/bonds520/meal-ordering-system.git
cd meal-ordering-system

# 3.3 檢查檔案完整性
ls -la
# 應看到: backend/, ollama/, docs/, docker-compose.yml, .env.example 等
```

### **步驟 4: 設定環境變數** (10 分鐘)

```bash
# 4.1 複製範本
cp .env.example .env

# 4.2 編輯環境變數
nano .env

# 4.3 填入以下變數 (從在家準備的 .env.deployment 複製)
# - LINE_CHANNEL_ACCESS_TOKEN
# - LINE_CHANNEL_SECRET
# - LINE_WEBHOOK_URL
# - DB_PASSWORD
# - SECRET_KEY
```

**注意**: 確保 `DATABASE_URL` 中的 host 是 `postgres` (Docker 服務名稱)，不是 `localhost`

### **步驟 5: 啟動服務** (10 分鐘)

```bash
# 5.1 啟動 Docker Compose
docker-compose up -d

# 5.2 等待服務啟動 (約 1-2 分鐘)
docker-compose ps

# 預期輸出:
# NAME                      STATUS
# meal-ordering-backend     Up (healthy)
# meal-ordering-postgres    Up
# meal-ordering-ollama      Up

# 5.3 查看日誌確認無誤
docker-compose logs --tail 50 backend
docker-compose logs --tail 50 postgres
docker-compose logs --tail 50 ollama
```

### **步驟 6: 初始化資料庫** (5 分鐘)

```bash
# 6.1 執行初始化腳本
docker-compose exec backend python backend/app/scripts/init_db.py

# 預期輸出:
# ✅ 資料庫初始化完成！
# 📊 已建立 5 家餐廳
# 📊 已建立 10 道菜單
# 📊 今日設定：補助 150 元，截止 11:30

# 6.2 驗證資料庫
docker-compose exec backend python -c "
from backend.app.database import get_db
from backend.app.models.restaurant import Restaurant
db = next(get_db())
restaurants = db.query(Restaurant).all()
print(f'✅ 餐廳數量：{len(restaurants)}')
"
```

### **步驟 7: 下載 Ollama 模型** (20-30 分鐘)

```bash
# 7.1 下載 llama3 模型
docker exec -it meal-ordering-ollama ollama pull llama3

# 這需要一些時間 (約 4GB 下載 + 解壓縮)
# 預期輸出:
# pulling manifest...
# pulling 8.07 MiB ... 100%
# ...
# success!

# 7.2 驗證模型
docker exec -it meal-ordering-ollama ollama list
# 應看到: llama3:latest
```

**注意**: 如果網路不穩，可以:
1. 在 Windows 上先下載模型
2. 使用 `docker save` 和 `docker load` 轉移
3. 或使用國內鏡像

### **步驟 8: 設定 Nginx 反向代理** (15 分鐘)

```bash
# 8.1 建立 Nginx 配置
sudo nano /etc/nginx/sites-available/meal-ordering

# 貼上 deployment-guide.md 中的配置內容
# 記得替換 'your-domain.com' 為實際域名

# 8.2 啟用配置
sudo ln -s /etc/nginx/sites-available/meal-ordering /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # 移除預設配置

# 8.3 測試配置
sudo nginx -t

# 8.4 重新載入 Nginx
sudo systemctl reload nginx

# 8.5 檢查狀態
sudo systemctl status nginx
```

### **步驟 9: 申請 SSL 憑證** (10 分鐘)

```bash
# 9.1 申請 Let's Encrypt 憑證
sudo certbot --nginx -d your-domain.com

# 9.2 按提示操作:
# - 輸入 Email
# - 同意服務條款
# - 選擇是否發送電子報 (建議 No)
# - 選擇重定向 (選擇 2: HTTPS only)

# 9.3 測試自動更新
sudo certbot renew --dry-run

# 預期輸出:
# Simulating renewal...
# ✅ Success!
```

### **步驟 10: 設定 LINE Webhook** (10 分鐘)

```bash
# 10.1 更新 .env 中的 Webhook URL
nano .env
# LINE_WEBHOOK_URL=https://your-domain.com/api/line/webhook

# 10.2 重啟後端容器以載入新設定
docker-compose restart backend

# 10.3 在 LINE Developers 控制台設定 Webhook
# 1. 進入應用設定
# 2. 找到 Webhook 區塊
# 3. 勾選 "Enable webhook"
# 4. 輸入 URL: https://your-domain.com/api/line/webhook
# 5. 點擊 "Test" 按鈕
# 6. 應看到 "Test successful"

# 10.4 查看測試日誌
docker-compose logs --tail 20 backend | grep webhook
```

### **步驟 11: 功能測試** (20 分鐘)

#### **11.1 健康檢查**
```bash
# 後端服務
curl http://localhost:8000/health

# 資料庫
curl http://localhost:8000/health/db

# OCR 服務
curl http://localhost:8000/api/ocr/health
```

**預期輸出**:
```json
{
  "status": "healthy",
  "database": "connected",
  "ollama": "connected",
  "models": ["llama3"]
}
```

#### **11.2 OCR 測試**
```bash
# 準備一張菜單圖片 (可以用手機拍)
# 上傳測試
curl -X POST https://your-domain.com/api/ocr/upload \
  -F "file=@menu.jpg" \
  -F "restaurant_id=1" \
  -F "date=2026-06-13"
```

**預期**: 1-2 分鐘內回應，包含辨識出的菜單項目

#### **11.3 LINE 測試**
```bash
# 11.3.1 用 LINE 追蹤官方帳號
# 11.3.2 輸入測試指令:
菜單          # 應回應今日菜單卡片
我的訂單      # 應回應「尚未有訂單」
訂 三鮮水餃   # 應建立訂單並確認
取消訂單      # 應取消訂單
```

#### **11.4 管理員測試**
```bash
# 訪問管理員後台 (如果有設定)
# https://your-domain.com/admin

# 或透過 API 測試:
curl http://localhost:8000/api/ocr/models
curl http://localhost:8000/api/restaurants
```

---

## 🔧 問題排除

### **如果步驟 5 失敗**
```bash
# 檢查 Docker 日誌
sudo journalctl -u docker --tail 50

# 重試啟動
docker-compose down
docker-compose up -d
```

### **如果步驟 7 失敗 (模型下載)**
```bash
# 方法 1: 多次重試
docker exec -it meal-ordering-ollama ollama pull llama3

# 方法 2: 使用較小的模型
docker exec -it meal-ordering-ollama ollama pull llama3:8b

# 方法 3: 從 Windows 轉移
# 在 Windows PowerShell:
docker save ollama/llama3:latest | compress -z > llama3.tar.gz
# 複製到 WSL:
cp /c/Users/YourName/Downloads/llama3.tar.gz /home/bonds/
# 在 WSL:
docker load < /home/bonds/llama3.tar.gz
```

### **如果步驟 9 失敗 (SSL 憑證)**
```bash
# 檢查 DNS 解析
nslookup your-domain.com

# 檢查端口開放
sudo netstat -tlnp | grep 443

# 手動測試
curl -I https://your-domain.com
```

### **如果步驟 10 失敗 (LINE Webhook)**
```bash
# 檢查 Nginx 日誌
sudo tail -f /var/log/nginx/error.log

# 檢查後端日誌
docker-compose logs -f backend | grep webhook

# 測試端點可達性
curl -X POST https://your-domain.com/api/line/webhook \
  -H "Content-Type: application/json" \
  -d '{"type": "ping"}'
```

---

## 📊 部署後設定

### **1. 設定自動備份**
```bash
# 建立備份腳本
cat > /home/bonds/meal-ordering-system/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cd /home/bonds/meal-ordering-system
docker-compose exec postgres pg_dump -U mealuser meal_db > /home/bonds/backups/meal_db_${DATE}.sql
# 保留最近 30 天的備份
find /home/bonds/backups -name "meal_db_*.sql" -mtime +30 -delete
EOF

chmod +x /home/bonds/meal-ordering-system/backup.sh

# 設定 Cron
(crontab -l 2>/dev/null; echo "0 2 * * * /home/bonds/meal-ordering-system/backup.sh") | crontab -
```

### **2. 設定監控警報**
```bash
# 安裝簡單監控
sudo apt-get install -y monitorix

# 或設定 Prometheus + Grafana (見 deployment-guide.md)
```

### **3. 設定日誌輪替**
```bash
# 編輯 /etc/logrotate.d/meal-ordering
sudo nano /etc/logrotate.d/meal-ordering

# 內容:
/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        systemctl reload nginx > /dev/null
    endscript
}
```

---

## 📱 員工使用指南

### **追蹤 LINE OA**
1. 開啟 LINE
2. 搜尋官方帳號 ID: `@your-restaurant-oa`
3. 點擊「追蹤」

### **訂餐流程**
1. 開啟與官方帳號的對話
2. 輸入「菜單」查看今日菜單
3. 輸入「訂 [菜色]」建立訂單
   - 範例: `訂 三鮮水餃`
4. 系統會確認訂單並顯示自付金額
5. 如需取消，輸入「取消訂單」

### **常見問題**
- **Q: 可以訂多道菜嗎？**
  - A: 目前每人每天限訂 1 道 (可調整設定)
  
- **Q: 訂餐截止時間？**
  - A: 每天 11:30 截止
  
- **Q: 如何查詢訂單？**
  - A: 輸入「我的訂單」
  
- **Q: 素食者怎麼辦？**
  - A: 菜單會標註「葷/素」，請選擇素食選項

---

## 📞 緊急聯絡

### **部署問題**
- **Hermes Agent**: 隨時詢問 (透過 Telegram)
- **GitHub Issues**: https://github.com/bonds520/meal-ordering-system/issues

### **系統異常處理**
```bash
# 快速重啟所有服務
cd /home/bonds/meal-ordering-system
docker-compose down
docker-compose up -d

# 查看錯誤日誌
docker-compose logs --tail 100

# 緊急停用服務
sudo systemctl stop nginx
docker-compose down
```

---

## ✅ 部署完成確認

部署完成後，請確認以下項目:

- [ ] 所有 Docker 容器狀態為 `Up`
- [ ] 資料庫初始化成功
- [ ] Ollama 模型下載完成
- [ ] Nginx 正常運行
- [ ] SSL 憑證已申請
- [ ] LINE Webhook 測試成功
- [ ] OCR 測試成功
- [ ] LINE 指令測試成功
- [ ] 實際菜單上傳測試成功
- [ ] 訂單建立測試成功
- [ ] 備份腳本已設定

**全部確認後，即可通知員工開始使用！** 🎉

---

*文件版本：1.0*  
*最後更新：2026-06-12*  
*部署日期：2026-06-13*
