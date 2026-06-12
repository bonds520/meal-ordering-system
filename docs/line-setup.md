# 🍱 公司員工訂餐系統 - LINE OA 整合指南

## ✅ 已完成的功能

### 1. LINE Bot 核心功能
- ✅ Webhook 處理
- ✅ 文字訊息解析
- ✅ Postback 事件處理 (Rich Menu)
- ✅ 圖片上傳處理
- ✅ 回覆與推送訊息

### 2. 用戶指令系統
- ✅ `菜單` - 查看今日菜單 (Carousel 卡片)
- ✅ `我的訂單` - 查詢個人訂單
- ✅ `訂 [菜色]` - 快速訂餐
- ✅ `取消訂單` - 取消今日訂單
- ✅ `截止時間` - 查看訂餐截止
- ✅ `/help` - 使用說明

### 3. Rich Menu 主選單
- ✅ 5 個功能按鈕 (菜單、訂餐、訂單、幫助、設定)
- ✅ Postback 事件處理
- ✅ JSON 配置完成

### 4. 管理員功能
- ✅ 圖片上傳與 OCR (框架)
- ✅ 菜單管理指令
- ✅ 截止時間設定
- ✅ 訂單查詢與匯出

---

## 📋 下一步設定步驟

### 步驟 1: 建立 LINE Developer 帳號

1. 前往 https://developers.line.biz
2. 用 Google/Gmail 帳號登入
3. 點擊 "Console" 進入 LINE Developers Console

### 步驟 2: 建立 Provider (若還沒有)

1. 在 Console 首頁點擊 "Add provider"
2. 填寫：
   - Provider name: `你的公司名稱`
   - Description: `公司訂餐系統`
   - 勾選服務條款
3. 點擊 "Create"

### 步驟 3: 建立 Messaging API Channel

1. 在 Provider 頁面，點擊 "Add channel"
2. 選擇 "LINE Official Account"
3. 填寫：
   - Use case: `Business`
   - Business type: `Other`
   - Account type: 選擇你的 LINE OA (或建立新的)
   - Channel name: `訂餐系統`
4. 勾選條款，點擊 "Create"

### 步驟 4: 設定 Messaging API

1. 在 Channel 管理頁面，左側選單點擊 "Messaging API"
2. 勾選 "Allow webhooks"
3. 點擊 "Configure"
4. 複製以下資訊 (之後要用)：
   - **Channel Access Token**
   - **Channel Secret**

### 步驟 5: 設定 Webhook URL

1. 在 Messaging API 設定頁面
2. Webhook URL 填入：
   ```
   https://你的域名/api/line/webhook
   ```
   - 若用本地測試：`http://你的 IP:8000/api/line/webhook`
   - **注意**: 正式環境必須用 HTTPS
3. 勾選 "Enable webhook"
4. 點擊 "Save"

### 步驟 6: 設定環境變數

1. 複製環境變數範本：
   ```bash
   cd /home/bonds/meal-ordering-system
   cp .env.example .env
   ```

2. 編輯 `.env` 檔案，填入 LINE 設定：
   ```env
   LINE_CHANNEL_ACCESS_TOKEN=複製你的 Channel Access Token
   LINE_CHANNEL_SECRET=複製你的 Channel Secret
   ```

3. 設定管理員 ID (可選)：
   ```env
   ADMIN_USER_IDS=你的 LINE User ID
   ```
   - 取得方式：用管理員帳號傳送訊息給自己的 OA，從 Webhook 的 `source.userId` 複製

### 步驟 7: 設定反向代理 (Nginx)

若要用 HTTPS，需要設定 Nginx：

```bash
# 安裝 Nginx
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx

# 建立 Nginx 配置
sudo nano /etc/nginx/sites-available/meal-ordering
```

Nginx 配置範本：
```nginx
server {
    listen 80;
    server_name 你的域名;
    
    location /api/line/webhook {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

啟用配置：
```bash
sudo ln -s /etc/nginx/sites-available/meal-ordering /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 取得 SSL 憑證
sudo certbot --nginx -d 你的域名
```

### 步驟 8: 啟動服務

```bash
cd /home/bonds/meal-ordering-system

# 啟動 Docker 容器
./deploy.sh

# 查看日誌
docker logs meal-ordering-backend
```

### 步驟 9: 測試 Webhook

1. 在 LINE Developer Console 的 Messaging API 頁面
2. 向下捲到 "Message proxy" 區域
3. 傳送測試訊息給你的 LINE OA
4. 檢查是否收到 Webhook 請求
5. 查看後端日誌確認處理成功

---

## 🎨 Rich Menu 圖片製作

### 方法 1: 使用 Canva (推薦)

1. 前往 https://www.canva.com
2. 建立自訂尺寸：**2500 x 1686 px**
3. 依照以下設計：
   ```
   ┌─────────┬─────────┬─────────┐
   │  🍱     │  ✍️     │  📋     │
   │  菜單   │  訂餐   │  訂單   │
   ├─────────┼─────────┴─────────┤
   │  ❓     │  ⚙️              │
   │  幫助   │  設定            │
   └─────────┴─────────┴─────────┘
   ```
4. 下載為 PNG 格式
5. 上傳到 LINE Developer Console 的 "Rich menu" 頁面

### 方法 2: 使用提供的 JSON 配置

1. 在 LINE Developer Console，點擊 "Rich menu"
2. 點擊 "Create rich menu"
3. 貼上 `backend/app/config/rich_menu.py` 中的 JSON
4. 上傳自訂圖片
5. 設定 Rich Menu ID 為 `order-system-menu`

### 方法 3: 先使用預設圖片

若暫時沒有自訂圖片，可以先用纯色方塊測試功能，之後再替換。

---

## 🧪 測試清單

### 用戶端測試
- [ ] 追蹤 LINE OA 後收到歡迎訊息
- [ ] 點擊「選單」按鈕有反應
- [ ] 輸入「菜單」收到 Carousel 卡片
- [ ] 點擊卡片上的「我要訂」有確認對話
- [ ] 輸入「訂 三鮮水餃」成功訂餐
- [ ] 輸入「我的訂單」看到已訂餐點
- [ ] 輸入「取消訂單」成功取消

### 管理員測試
- [ ] 上傳菜單圖片成功
- [ ] 設定截止時間成功
- [ ] 查詢所有訂單成功
- [ ] 匯出 Excel 成功

---

## 🐛 常見問題

### Q1: Webhook 收不到訊息
- 檢查 Webhook URL 是否正確
- 確認 Nginx 反向代理設定
- 查看後端日誌：`docker logs meal-ordering-backend`
- 確認 LINE Developer Console 的 Webhook 狀態

### Q2: 認證失敗
- 確認 `LINE_CHANNEL_ACCESS_TOKEN` 和 `LINE_CHANNEL_SECRET` 正確
- 檢查 `.env` 檔案是否正確載入
- 重新啟動 Docker 容器

### Q3: Rich Menu 不顯示
- 確認 Rich Menu 已上傳並設定
- 檢查 Rich Menu ID 是否為 `order-system-menu`
- 確認用戶追蹤後已執行 `link_rich_menu`

### Q4: 卡片訊息顯示異常
- 檢查 Flex Message 的 JSON 結構
- 確認圖片 URL 可公開存取
- 測試時先用 placeholder 圖片

---

## 📞 需要協助？

完成設定後，若遇到任何問題：
1. 提供錯誤訊息
2. 提供 Docker 日誌
3. 我可以立即協助除錯！

---

**準備好了嗎？開始設定 LINE OA，然後告訴我進度！** 🚀
