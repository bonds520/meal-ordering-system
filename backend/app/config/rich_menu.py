# Rich Menu 配置
# 用於訂餐系統的主選單

RICH_MENU_CONFIG = {
    "size": {"width": 2500, "height": 1686},
    "selected": True,
    "name": "訂餐主選單",
    "chatBarText": "🍱 選單",
    "areas": [
        # 左上：菜單
        {
            "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
            "action": {
                "type": "postback",
                "data": "action=menu"
            }
        },
        # 中上：訂餐
        {
            "bounds": {"x": 833, "y": 0, "width": 834, "height": 843},
            "action": {
                "type": "postback",
                "data": "action=order"
            }
        },
        # 右上：我的訂單
        {
            "bounds": {"x": 1667, "y": 0, "width": 833, "height": 843},
            "action": {
                "type": "postback",
                "data": "action=myorder"
            }
        },
        # 左下：幫助
        {
            "bounds": {"x": 0, "y": 843, "width": 1250, "height": 843},
            "action": {
                "type": "postback",
                "data": "action=help"
            }
        },
        # 右下：設定
        {
            "bounds": {"x": 1250, "y": 843, "width": 1250, "height": 843},
            "action": {
                "type": "postback",
                "data": "action=settings"
            }
        }
    ]
}

# Rich Menu 圖片設計指引
# 尺寸：2500 x 1686 px
# 區域劃分：
# ┌─────────┬─────────┬─────────┐
# │  菜單   │  訂餐   │ 訂單    │  0-843 px
# │  (A)    │  (B)    │  (C)    │
# ├─────────┼─────────┴─────────┤
# │   幫助  │     設定          │  843-1686 px
# │  (D)    │     (E)           │
# └─────────┴─────────┴─────────┘

# 建議圖標設計：
# A (菜單): 🍱 大碗飯圖標，背景色：#4CAF50
# B (訂餐): ✍️ 手寫圖標，背景色：#2196F3
# C (訂單): 📋 清單圖標，背景色：#FFC107
# D (幫助): ❓ 問號圖標，背景色：#9C27B0
# E (設定): ⚙️ 齒輪圖標，背景色：#607D8B

# 可使用工具：
# - Canva (線上設計)
# - Figma (專業設計)
# - Photoshop (進階編輯)
# - GIMP (免費開源)
