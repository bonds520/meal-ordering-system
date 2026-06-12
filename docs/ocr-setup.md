# OCR 功能設定指南

## 📸 功能概述

訂餐系統整合了 **Ollama LLM** 進行圖片文字辨識，支援以下功能：

- ✅ **菜單圖片辨識** - 上傳菜單照片，自動解析菜名與價格
- ✅ **休假表勾選辨識** - 上傳休假表，自動識別勾選日期
- ✅ **通用 OCR** - 任意圖片文字辨識

## 🚀 快速開始

### 1. 啟動 Ollama 服務

```bash
# 啟動 Docker 服務 (包含 Ollama)
cd /home/bonds/meal-ordering-system
docker-compose up -d ollama

# 檢查 Ollama 是否運行正常
docker logs meal-ordering-ollama
```

### 2. 拉取 LLM 模型

```bash
# 進入 Ollama 容器
docker exec -it meal-ordering-ollama sh

# 拉取 llama3 模型 (約 4.7GB)
ollama pull llama3

# 或拉取更輕量的模型 (約 2.3GB)
ollama pull llama3:8b

# 退出容器
exit
```

**推薦模型：**
- `llama3` (8B) - 平衡性能與準確度
- `llama3:8b` - 輕量版，適合低規格硬體
- `llama3.1` - 最新版本，更好的 OCR 表現

### 3. 測試 OCR 服務

```bash
# 檢查 OCR 服務狀態
curl http://localhost:8000/api/ocr/health

# 列出已安裝的模型
curl http://localhost:8000/api/ocr/models
```

## 📋 API 使用說明

### 1. 上傳菜單圖片

```bash
# 上傳菜單照片並自動解析
curl -X POST http://localhost:8000/api/ocr/upload \
  -F "file=@menu.jpg" \
  -F "restaurant_id=1"
```

**回應範例：**
```json
{
  "success": true,
  "message": "成功辨識並建立 5 個菜單項目",
  "file_url": "/uploads/menus/abc123.jpg",
  "items": [
    {
      "id": 1,
      "name": "三鮮水餃",
      "price": 150,
      "food_type": "meat"
    },
    {
      "id": 2,
      "name": "素炒青菜",
      "price": 80,
      "food_type": "vegetarian"
    }
  ],
  "processing_time": 3.5
}
```

### 2. 通用文字辨識

```bash
# 辨識圖片中的文字
curl -X POST http://localhost:8000/api/ocr/recognize \
  -F "file=@image.jpg" \
  -F "prompt=請辨識這張圖片中的所有文字"
```

**回應範例：**
```json
{
  "success": true,
  "text": "辨識到的文字內容...",
  "confidence": 0.9,
  "processing_time": 2.1
}
```

### 3. 休假表辨識

```bash
# 辨識休假表勾選
curl -X POST http://localhost:8000/api/ocr/leave-form \
  -F "file=@leave_form.jpg" \
  -F "employee_id=E12345"
```

**回應範例：**
```json
{
  "success": true,
  "leave_dates": ["2026-06-15", "2026-06-16"],
  "leave_type": "年假",
  "notes": "",
  "file_url": "/uploads/leave_abc123.jpg",
  "processing_time": 4.2
}
```

### 4. 下載模型

```bash
# 遠端觸發模型下載
curl -X POST http://localhost:8000/api/ocr/models/pull \
  -F "model_name=llama3.1"
```

## 🔧 管理員後台整合

### 菜單管理頁面

```html
<!-- 在前端管理頁面加入上傳功能 -->
<form id="menu-upload-form">
  <input type="number" name="restaurant_id" placeholder="餐廳 ID" required>
  <input type="file" name="file" accept="image/*" required>
  <button type="submit">上傳並解析</button>
</form>

<script>
document.getElementById('menu-upload-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);
  
  const response = await fetch('http://localhost:8000/api/ocr/upload', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  
  if (result.success) {
    alert(`成功建立 ${result.items.length} 個菜單項目`);
    // 重新整理菜單列表
    location.reload();
  } else {
    alert('辨識失敗：' + result.error);
    // 顯示原始文字供手動輸入
    console.log('原始文字:', result.raw_text);
  }
});
</script>
```

## 📊 效能優化

### 1. 硬體需求

| 配置 | 最低需求 | 推薦配置 |
|------|---------|---------|
| **CPU** | 4 核心 | 8 核心以上 |
| **RAM** | 8GB | 16GB 以上 |
| **GPU** | 不需要 | NVIDIA GPU (VRAM 8GB+) |
| **儲存** | 10GB | 20GB (含模型) |

### 2. 辨識速度

| 模型 | 圖片大小 | 平均時間 |
|------|---------|---------|
| llama3:8b | 500KB | 2-3 秒 |
| llama3 | 500KB | 3-5 秒 |
| llama3.1 | 500KB | 4-6 秒 |

### 3. 準確度提升技巧

- ✅ **圖片解析度** - 建議 800x600 以上
- ✅ **圖片品質** - 清晰、無模糊
- ✅ **光照充足** - 避免陰影
- ✅ **正面拍攝** - 避免角度過大
- ✅ **單一頁面** - 一次只上傳一頁

## 🐛 常見問題

### Q1: Ollama 服務無法連線

**症狀：** `Connection refused` 或 `500 Internal Server Error`

**解決方案：**
```bash
# 檢查 Ollama 容器狀態
docker-compose ps ollama

# 查看 Ollama 日誌
docker logs meal-ordering-ollama

# 重啟 Ollama 服務
docker-compose restart ollama
```

### Q2: 模型尚未下載

**症狀：** `model not found` 錯誤

**解決方案：**
```bash
# 方法 1: 在容器內下載
docker exec -it meal-ordering-ollama ollama pull llama3

# 方法 2: 使用 API 下載
curl -X POST http://localhost:8000/api/ocr/models/pull \
  -F "model_name=llama3"
```

### Q3: OCR 辨識準確度低

**可能原因：**
- 圖片模糊或解析度太低
- 光照不足或有陰影
- 文字太小或字體特殊

**改善方法：**
- 重新拍攝清晰圖片
- 使用更高的解析度
- 確保光照均勻
- 嘗試不同的模型 (llama3.1 通常表現更好)

### Q4: 辨識速度太慢

**解決方案：**
- 使用更輕量的模型 (llama3:8b)
- 降低圖片解析度 (800x600 通常足夠)
- 使用 GPU 加速 (已在 docker-compose 中配置)
- 關閉其他占用資源的程序

### Q5: JSON 解析失敗

**症狀：** 返回 `success: false` 和原始文字

**原因：** LLM 輸出的格式不符合預期

**解決方案：**
- 管理員手動輸入菜單資料
- 使用更明確的提示詞
- 更新到更新的模型版本

## 🔗 進階使用

### 自訂提示詞

```bash
# 使用自訂提示詞進行辨識
curl -X POST http://localhost:8000/api/ocr/recognize \
  -F "file=@image.jpg" \
  -F "prompt=請提取這張發票上的日期、金額和商家名稱，以 JSON 格式輸出"
```

### 批量處理

```python
# Python 範例：批量上傳菜單圖片
import requests
import os

api_url = "http://localhost:8000/api/ocr/upload"
restaurant_id = 1

# 圖片目錄
image_dir = "/path/to/menu/images"

for filename in os.listdir(image_dir):
    if filename.endswith(('.jpg', '.jpeg', '.png')):
        print(f"處理 {filename}...")
        
        with open(os.path.join(image_dir, filename), 'rb') as f:
            response = requests.post(
                api_url,
                files={'file': f},
                data={'restaurant_id': restaurant_id}
            )
        
        result = response.json()
        print(f"結果：{result.get('message', '未知錯誤')}")
```

## 📝 日誌與除錯

### 查看 OCR 處理日誌

```bash
# 查看 API 容器日誌
docker logs meal-ordering-api | grep OCR

# 查看 Ollama 容器日誌
docker logs meal-ordering-ollama

# 即時監控
docker logs -f meal-ordering-api
```

### 日誌範例

```
[INFO] OCR 辨識開始：menu_123.jpg
[INFO] 使用模型：llama3
[INFO] 辨識完成，耗時 3.5 秒
[INFO] 成功解析 5 個菜單項目
[INFO] 已建立資料庫記錄
```

## 🎯 下一步

- [ ] **整合到 LINE Bot** - 支援 LINE 上傳圖片
- [ ] **自動排程** - 每日自動下載新菜單
- [ ] **圖片優化** - 自動調整解析度與壓縮
- [ ] **多語言支援** - 支援繁體、簡體、英文菜單
- [ ] **機器學習** - 根據歷史資料優化辨識準確度

---

**最後更新：** 2026-06-12  
**版本：** 1.0.0
