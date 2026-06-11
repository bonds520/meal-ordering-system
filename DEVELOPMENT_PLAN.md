# 訂餐系統開發計畫

## ✅ 已完成 (Day 1)

### 基礎架構
- [x] 專案目錄結構建立
- [x] 資料庫模型設計 (SQLAlchemy)
  - [x] User (員工資料)
  - [x] Restaurant (餐廳資料)
  - [x] MenuItem (菜單項目)
  - [x] Order (訂單)
  - [x] DailySetting (每日設定)
  - [x] LeaveRecord (休假記錄)
  - [x] OrderLog (異動日誌)
- [x] FastAPI 後端骨架
- [x] Docker Compose 配置
- [x] 資料庫初始化腳本
- [x] 管理後台前端 (基礎版)
- [x] LINE Bot 整合框架
- [x] 部署腳本

### API 路由
- [x] /api/auth/login - LINE 登入
- [x] /api/menu - 菜單查詢
- [x] /api/menu/ocr - OCR 辨識
- [x] /api/order - 訂單管理
- [x] /api/admin/restaurants - 餐廳管理
- [x] /api/admin/daily-setting - 每日設定
- [x] /api/admin/leave/upload - 休假表上傳
- [x] /api/line/webhook - LINE Webhook

### 文件
- [x] README.md
- [x] .env.example
- [x] Ollama Prompts (菜單 OCR、休假表解析)

---

## 📋 接下來的工作 (Day 2-30)

### 第二週：核心功能實作

#### Day 2-3: 資料庫與認證
- [ ] 實際測試資料庫連線
- [ ] 完成 LINE 認證流程
- [ ] 員工資料匯入功能
- [ ] SSO 整合 (如有需求)

#### Day 4-6: 菜單與訂單
- [ ] 完整實作菜單 CRUD
- [ ] 訂單建立與狀態管理
- [ ] 反悔重訂邏輯
- [ ] QR Code 生成與驗證
- [ ] 補助金額即時計算

#### Day 7: 管理功能
- [ ] 餐廳管理後台完整化
- [ ] 每日設定介面
- [ ] 訂單總覽與篩選
- [ ] 訂單匯出 (Excel/PDF)

### 第三週：進階功能

#### Day 8-10: OCR 與 LLM
- [ ] 整合 Ollama LLM
- [ ] 菜單 OCR 實際實作
- [ ] 休假表解析實際實作
- [ ] 人工確認介面

#### Day 11-12: LINE 整合
- [ ] LINE Messaging API 完整實作
- [ ] Rich Menu 設計
- [ ] 通知推送功能
- [ ] 訂單狀態更新通知

#### Day 13: 對帳功能
- [ ] 每日對帳表生成
- [ ] 月結報表
- [ ] 異動日誌查詢

### 第四週：測試與上線

#### Day 14-16: 系統測試
- [ ] 單元測試
- [ ] 整合測試
- [ ] 使用者接受測試 (UAT)
- [ ] Bug 修復

#### Day 17-18: 效能優化
- [ ] 資料庫索引優化
- [ ] 快取策略 (Redis)
- [ ] 圖片壓縮與 CDN

#### Day 19: 文件與培訓
- [ ] 管理員使用手冊
- [ ] 員工使用指南
- [ ] 系統維護文件

#### Day 20: 上線部署
- [ ] 生產環境部署
- [ ] 資料備份設定
- [ ] 監控與日誌
- [ ] 上線驗證

---

## 🔧 技術待決事項

### 1. 前端框架選擇
- **目前**: 純 HTML/CSS/JS (基礎版)
- **建議**: 改用 React + Ant Design (管理後台)
- **原因**: 更易維護、組件豐富

### 2. OCR 引擎
- **目前**: 規劃用 Ollama LLM
- **備選**: Tesseract (純離線)、Google Vision (需網路)
- **建議**: 先用 LLM，效能不足再優化

### 3. QR Code 生成
- **目前**: 規劃用 qrcode 套件
- **需確認**: QR Code 內容格式、驗證邏輯

### 4. 圖片儲存
- **目前**: 本地 uploads 目錄
- **建議**: 可考慮 MinIO (本地 S3 相容)

### 5. 排程任務
- **需新增**: Celery + Redis
- **用途**: 訂餐截止提醒、通知推送

---

## 📊 開發進度追蹤

### 當前狀態
- **階段**: Day 1 完成
- **完成度**: 約 30% (基礎架構完成)
- **剩餘時間**: 29 天

### 里程碑
1. ✅ Day 1: 基礎架構完成
2. 📅 Day 7: 核心功能可用 (MVP)
3. 📅 Day 14: 所有功能完成
4. 📅 Day 21: 測試完成
5. 📅 Day 30: 正式上線

---

## 🚀 立即啟動步驟

1. **啟動系統**
```bash
cd /home/bonds/meal-ordering-system
./deploy.sh
```

2. **設定 LINE Channel**
- 申請 LINE Official Account
- 設定 Webhook URL: `http://your-server/api/line/webhook`
- 取得 Token 並填入 .env

3. **測試 API**
```bash
# 測試健康檢查
curl http://localhost:8000/health

# 查看 API 文件
http://localhost:8000/docs
```

4. **拉取 LLM 模型**
```bash
docker exec -it meal-ordering-ollama ollama pull llama3
```

5. **開始使用**
- 管理後台：http://localhost
- 新增餐廳、設定訂餐規則
- 測試 LINE 點餐

---

## 📞 需要協助時

如遇問題，請提供：
1. 錯誤訊息完整內容
2. Docker 日誌：`docker-compose logs`
3. 相關 API 請求與回應

**馬力強隨時待命！** 💪
