# 🍱 公司員工訂餐系統

支援 LINE 點餐、本地 LLM OCR、休假表自動解析的公司員工訂餐系統。

## ✨ 核心功能

### 員工端
- ✅ LINE 官方帳號點餐
- ✅ 菜單瀏覽（葷食/素食分類）
- ✅ 線上訂餐、取消、重訂
- ✅ 補助餘額查詢
- ✅ 取餐 QR Code
- ✅ 休假自動跳過

### 管理端
- ✅ 餐廳管理（新增、編輯、開關）
- ✅ 菜單 OCR 建檔（本地 LLM）
- ✅ 每日餐廳選擇
- ✅ 補助額度設定
- ✅ 訂單總覽與匯出
- ✅ 休假表上傳與解析
- ✅ 對帳報表

## 🛠️ 技術架構

- **後端**: FastAPI + Python
- **資料庫**: PostgreSQL
- **前端**: React (管理後台) + LINE Bot
- **OCR**: Ollama + Llama3 (本地 LLM)
- **部署**: Docker + Docker Compose

## 📦 快速開始

### 環境需求
- Docker & Docker Compose
- ASUS GX10 (或具備 GPU 的 Linux 主機)

### 安裝步驟

1. **複製環境變數檔案**
```bash
cp .env.example .env
# 編輯 .env 並填入實際的 LINE Channel 設定
```

2. **啟動系統**
```bash
docker-compose up -d
```

3. **檢查系統狀態**
```bash
docker-compose ps
```

4. **存取管理後台**
- 管理後台：http://localhost
- API 文件：http://localhost/docs
- API 服務：http://localhost:8000

### 首次設定

1. **登入管理後台**（預設帳號：admin / admin123）

2. **設定 LINE Channel**
   - 申請 LINE Official Account
   - 取得 Channel Access Token 和 Secret
   - 填入 .env 並重新啟動

3. **新增餐廳資料**
   - 進入「餐廳管理」
   - 新增合作餐廳

4. **上傳員工資料**
   - 進入「員工管理」
   - 匯入 Excel 員工名單

5. **設定訂餐規則**
   - 進入「每日設定」
   - 選擇開放餐廳、設定補助金額

## 📱 LINE 使用方式

### 員工指令
- `菜單` - 查看今日菜單
- `我的訂單` - 查看已訂餐點
- `訂 [菜色名稱]` - 訂餐
- `/help` - 查看幫助

### 範例對話
```
員工：菜單
系統：🍱 今日菜單
      【葷食】三鮮水餃 - 120 元
      【素食】素三鮮水餃 - 110 元
      
員工：訂 三鮮水餃
系統：✅ 訂餐成功！
      請於 11:30-13:00 取餐
```

## 🔧 進階設定

### Ollama LLM 設定

1. **拉取模型**
```bash
docker exec -it meal-ordering-ollama ollama pull llama3
```

2. **測試 OCR**
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt": "請辨識這張菜單圖片的內容"
}'
```

### 休假表格式

支援 Excel 格式，建議欄位：
- 員工編號
- 姓名
- 各日期欄位（可手動勾選✓）

系統會用 LLM 自動辨識勾選內容。

## 📊 對帳報表

系統自動生成：
- 每日對帳表（總補助、自付總額、各餐廳應付）
- 月結報表（用餐統計、補助總額、餐廳分析）

## 🐛 常見問題

### Q: OCR 辨識不準確？
A: 可調整 LLM Prompt 或更換模型（如 mistral、gemma）

### Q: LINE 通知收不到？
A: 檢查 Channel Access Token 是否正確，Webhook URL 是否設定

### Q: 休假表辨識有誤？
A: 系統提供「需人工確認」介面，可手動修正

## 📄 License

MIT License

## 👥 開發團隊

Bonds Chang & 馬力強 (Hermes Agent)
