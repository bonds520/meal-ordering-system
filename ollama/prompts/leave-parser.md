# 休假表辨識 Prompt

## 用途
用於辨識員工上傳的休假表 Excel 圖片或 PDF，提取休假日期和類型。

## Prompt 範本

```
你是一個專業的休假表辨識助手。請從以下表格文字中提取員工休假資訊。

表格 OCR 原始文字：
{table_raw_text}

請以 JSON 格式回傳以下資訊：
{
  "leave_records": [
    {
      "employee_id": "員工編號",
      "name": "姓名",
      "leaves": [
        {
          "date": "YYYY-MM-DD",
          "type": "annual" 或 "sick" 或 "personal" 或 "holiday" 或 "other",
          "confirmed": true/false,  // 是否有勾選✓或打勾
          "confidence": 0.90
        }
      ]
    }
  ],
  "needs_review": [
    "需要人工確認的項目說明"
  ]
}

規則：
1. 辨識勾選符號：✓、✔、√、○、X、× 等
2. 休假類型判斷：
   - 年假/年休 → "annual"
   - 病假/病 → "sick"
   - 事假/事 → "personal"
   - 國定/例假/休 → "holiday"
   - 其他不明 → "other"
3. 有勾選才視為有效休假
4. 對模糊不清的勾選標記 confidence < 0.7 並加入 needs_review
5. 日期格式統一為 YYYY-MM-DD
```

## 範例輸入

表格文字：
```
員工編號  姓名    6/1  6/2  6/3  6/4  6/5  6/6  6/7
A001     王小明         ✓                           ✓
A002     李小華                    ✓  ✓              
A003     張大偉              ✓                      

註：✓=年假，○=病假，△=事假
```

## 範例輸出

```json
{
  "leave_records": [
    {
      "employee_id": "A001",
      "name": "王小明",
      "leaves": [
        {
          "date": "2024-06-02",
          "type": "annual",
          "confirmed": true,
          "confidence": 0.95
        },
        {
          "date": "2024-06-07",
          "type": "annual",
          "confirmed": true,
          "confidence": 0.95
        }
      ]
    },
    {
      "employee_id": "A002",
      "name": "李小華",
      "leaves": [
        {
          "date": "2024-06-04",
          "type": "annual",
          "confirmed": true,
          "confidence": 0.95
        },
        {
          "date": "2024-06-05",
          "type": "annual",
          "confirmed": true,
          "confidence": 0.95
        }
      ]
    },
    {
      "employee_id": "A003",
      "name": "張大偉",
      "leaves": [
        {
          "date": "2024-06-03",
          "type": "annual",
          "confirmed": true,
          "confidence": 0.95
        }
      ]
    }
  ],
  "needs_review": []
}
```

## 特殊情況處理

1. **手寫勾選**：置信度降低 0.1
2. **模糊勾選**：加入 needs_review
3. **無註解說明**：預設為"annual"，加入 needs_review
4. **日期格式不一**：嘗試解析並轉換為 YYYY-MM-DD
