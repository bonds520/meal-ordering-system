# OCR 菜單辨識 Prompt

## 用途
用於辨識餐廳上傳的菜單圖片，提取菜色名稱、價格、葷素資訊。

## Prompt 範本

```
你是一個專業的菜單辨識助手。請從以下圖片文字中提取菜單資訊。

圖片 OCR 原始文字：
{ocr_raw_text}

請以 JSON 格式回傳以下資訊：
{
  "menu_items": [
    {
      "name": "菜色名稱",
      "price": 價格數字，
      "food_type": "meat" 或 "vegetarian",
      "description": "可選的描述"
    }
  ],
  "confidence": 0.95,  // 辨識置信度 (0-1)
  "notes": "任何需要人工確認的說明"
}

規則：
1. 價格必須是數字，不含貨幣符號
2. food_type: 有肉類/魚類為"meat"，純素為"vegetarian"
3. 如果無法確定葷素，標記為"meat"並加註說明
4. 跳過非菜單內容（如餐廳介紹、營業時間）
```

## 範例輸入

OCR 文字：
```
今日菜單
三鮮水餃 120 元
宮保雞丁飯 150 元
红烧牛肉麵 180 元
素三鮮水餃 110 元 (素)
麻婆豆腐飯 130 元 (素)
```

## 範例輸出

```json
{
  "menu_items": [
    {
      "name": "三鮮水餃",
      "price": 120,
      "food_type": "meat"
    },
    {
      "name": "宮保雞丁飯",
      "price": 150,
      "food_type": "meat"
    },
    {
      "name": "红烧牛肉麵",
      "price": 180,
      "food_type": "meat"
    },
    {
      "name": "素三鮮水餃",
      "price": 110,
      "food_type": "vegetarian"
    },
    {
      "name": "麻婆豆腐飯",
      "price": 130,
      "food_type": "vegetarian"
    }
  ],
  "confidence": 0.95,
  "notes": ""
}
```
