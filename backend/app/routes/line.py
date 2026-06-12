from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import hashlib
import hmac
import base64
import json
import os
from datetime import datetime

from linepy import LineBot
from linepy.models import (
    TextMessage,
    PostbackEvent,
    FlexMessage,
    BubbleTemplate,
    CarouselTemplate,
    FlexComponent,
    BoxComponent,
    TextComponent,
    ImageComponent,
    ButtonComponent,
    IconComponent,
    SpanComponent
)

router = APIRouter()

# 初始化 LINE Bot (實際使用時從環境變數讀取)
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

try:
    line_bot = LineBot(
        channel_access_token=LINE_CHANNEL_ACCESS_TOKEN,
        channel_secret=LINE_CHANNEL_SECRET
    )
except Exception as e:
    print(f"LINE Bot 初始化失敗：{e}")
    line_bot = None

# ============ 資料模型 ============

class LineVerifyRequest(BaseModel):
    mode: str
    timestamp: str
    channelAccessToken: str
    signature: str

class LineVerifyResponse(BaseModel):
    validity: bool

class LineMessage(BaseModel):
    type: str
    text: Optional[str] = None
    id: Optional[str] = None

class LineEvent(BaseModel):
    type: str
    mode: str
    timestamp: int
    source: dict
    href: Optional[str] = None
    replyToken: Optional[str] = None
    message: Optional[LineMessage] = None
    postback: Optional[dict] = None
    message_id: Optional[int] = None

class LineWebhookEvent(BaseModel):
    destination: Optional[str] = None
    events: List[LineEvent]

# ============ Webhook 處理 ============

@router.post("/verify")
async def verify_line(request: LineVerifyRequest):
    """LINE 官方帳號驗證"""
    channel_secret = LINE_CHANNEL_SECRET
    
    signing_key = f"{request.mode}\n{request.timestamp}\n{request.channelAccessToken}"
    signing_key_bytes = signing_key.encode("utf-8")
    
    secret_bytes = channel_secret.encode("utf-8")
    signature = hmac.new(secret_bytes, signing_key_bytes, hashlib.sha256).digest()
    encoded_signature = base64.b64encode(signature).decode("utf-8")
    
    if encoded_signature == request.signature:
        return LineVerifyResponse(validity=True)
    else:
        raise HTTPException(status_code=400, detail="Invalid signature")

@router.post("/webhook")
async def handle_line_webhook(request: Request):
    """處理 LINE Webhook 事件"""
    body = await request.json()
    event_data = LineWebhookEvent(**body)
    
    # 處理驗證訊息
    if len(event_data.events) == 1:
        event = event_data.events[0]
        if event.type == "unfollow":
            return JSONResponse({"status": "ok"})
        
        # 驗證模式
        if event.mode == "active" and not event.message and not event.postback:
            # 可能是驗證請求
            return JSONResponse({"status": "ok"})
    
    # 處理每個事件
    results = []
    for event in event_data.events:
        result = await process_event(event)
        if result:
            results.append(result)
    
    if results:
        return JSONResponse(results)
    
    return JSONResponse({"status": "ok"})

async def process_event(event: LineEvent) -> dict:
    """處理單一事件"""
    if not line_bot:
        print("LINE Bot 未初始化")
        return {"status": "ok"}
    
    try:
        # 處理追蹤事件
        if event.type == "follow":
            await line_bot.push_message(
                to=event.source.userId,
                messages=[TextMessage(text="👋 歡迎使用訂餐系統！\n\n請輸入 /help 查看可用指令")]
            )
            # 設定 Rich Menu
            await line_bot.link_rich_menu_menu_id(
                user_id=event.source.userId,
                rich_menu_id="order-system-menu"
            )
            return {"status": "ok"}
        
        # 處理訊息事件
        elif event.type == "message":
            if event.message and event.message.type == "text":
                user_message = event.message.text
                response = await process_user_command(user_message, event.source, event.replyToken)
                return response
            
            elif event.message and event.message.type == "image":
                # 處理圖片上傳 (管理員用)
                return await handle_image_upload(event.source, event.replyToken, event.message.id)
        
        # 處理 Postback 事件 (Rich Menu 按鈕點擊)
        elif event.type == "postback":
            if event.postback:
                action_data = event.postback.data
                response = await handle_postback(action_data, event.source, event.replyToken)
                return response
        
        return {"status": "ok"}
    
    except Exception as e:
        print(f"處理事件錯誤：{e}")
        return {"status": "error", "message": str(e)}

# ============ 指令處理 ============

async def process_user_command(message: str, source: dict, reply_token: str) -> dict:
    """處理用戶指令"""
    user_id = source.get("userId")
    
    # 指令解析
    if message.startswith("/"):
        response_text = await handle_command(message, user_id)
    elif message in ["菜單", "看菜單", "今日菜單", "今天菜單"]:
        response = await show_menu_carousel(user_id, reply_token)
        return response
    elif message in ["我的訂單", "訂單"]:
        response_text = await show_my_orders(user_id)
    elif message.startswith("訂") or message.startswith("我要訂"):
        response_text = await handle_order(message, user_id)
    elif message in ["取消訂單", "取消"]:
        response_text = await cancel_order(user_id)
    elif message in ["截止時間", "訂餐截止"]:
        response_text = await show_deadline()
    elif message in ["1", "2", "3", "4", "5"]:
        # 確認選擇
        response = await confirm_menu_selection(message, user_id, reply_token)
        return response
    else:
        response_text = get_welcome_message()
    
    # 傳送文字訊息
    if line_bot:
        await line_bot.reply_message(
            reply_token=reply_token,
            messages=[TextMessage(text=response_text)]
        )
    
    return {"status": "ok"}

async def handle_postback(action_data: str, source: dict, reply_token: str) -> dict:
    """處理 Rich Menu Postback"""
    user_id = source.get("userId")
    
    # 解析 action 和 data
    if "=" in action_data:
        parts = action_data.split("=", 1)
        action = parts[0]
        value = parts[1] if len(parts) > 1 else ""
    else:
        action = action_data
        value = ""
    
    # 根據 action 處理
    if action == "menu":
        response = await show_menu_carousel(user_id, reply_token)
        return response
    
    elif action == "order":
        response_text = "📝 要訂餐請輸入：訂 [菜色名稱]\n例如：訂 三鮮水餃"
        if line_bot:
            await line_bot.reply_message(reply_token=reply_token, messages=[TextMessage(text=response_text)])
    
    elif action == "myorder":
        response_text = await show_my_orders(user_id)
        if line_bot:
            await line_bot.reply_message(reply_token=reply_token, messages=[TextMessage(text=response_text)])
    
    elif action == "help":
        response_text = get_help_message()
        if line_bot:
            await line_bot.reply_message(reply_token=reply_token, messages=[TextMessage(text=response_text)])
    
    elif action == "settings":
        response_text = "⚙️ 設定\n\n• 通知設定\n• 取餐地點\n\n需要更多設定請聯繫管理員"
        if line_bot:
            await line_bot.reply_message(reply_token=reply_token, messages=[TextMessage(text=response_text)])
    
    elif action == "confirm_order":
        # 確認訂餐
        menu_id = value
        response = await confirm_order_from_menu(menu_id, user_id, reply_token)
        return response
    
    return {"status": "ok"}

# ============ 指令函數 ============

async def handle_command(command: str, user_id: str) -> str:
    """處理系統指令"""
    if command == "/help":
        return get_help_message()
    
    elif command == "/menu":
        return await show_menu(user_id)
    
    elif command == "/order":
        return await show_my_orders(user_id)
    
    elif command == "/cancel":
        return await cancel_order(user_id)
    
    elif command.startswith("/admin"):
        # 管理員指令
        return await handle_admin_command(command[6:], user_id)
    
    else:
        return "❌ 未知指令，請使用 /help 查看可用指令"

def get_welcome_message() -> str:
    """歡迎訊息"""
    return """👋 歡迎使用訂餐系統！

可使用的指令：
• 菜單 - 查看今日菜單
• 我的訂單 - 查看已訂餐點
• 訂 [菜色名稱] - 訂餐
• 取消訂單 - 取消今日訂單
• /help - 查看幫助

💡 小技巧：點擊下方的「選單」按鈕快速操作"""

def get_help_message() -> str:
    """幫助訊息"""
    return """📱 訂餐系統使用說明

🔍 查詢指令：
• 菜單 - 查看今日菜單
• 我的訂單 - 查看已訂餐點
• 截止時間 - 查看訂餐截止時間

📝 訂餐指令：
• 訂 [菜色名稱] - 例如：訂 三鮮水餃
• 取消訂單 - 取消今日訂單

⚙️ 其他指令：
• /help - 查看幫助
• /menu - 快速查看菜單
• /order - 快速查看訂單

💡 使用 Rich Menu：
點擊下方「選單」按鈕可快速操作"""

async def show_menu(user_id: str) -> str:
    """顯示今日菜單 (文字版)"""
    # TODO: 實際實作時從資料庫讀取
    return """🍱 今日菜單 (2026/06/12)

【葷食】
• A 餐 - 三鮮水餃 - 120 元
• B 餐 - 宮保雞丁飯 - 150 元
• C 餐 - 紅燒牛肉麵 - 180 元

【素食】
• D 餐 - 素三鮮水餃 - 110 元
• E 餐 - 麻婆豆腐飯 (素) - 130 元
• F 餐 - 素蔬食麵 - 100 元

💰 今日補助：150 元
⏰ 訂餐截止：今日 11:30
📍 取餐時間：11:30-13:00

要訂餐請輸入：訂 [菜色名稱]
或直接點擊菜單按鈕選擇"""

async def show_menu_carousel(user_id: str, reply_token: str) -> dict:
    """顯示今日菜單 (Carousel 卡片版)"""
    if not line_bot:
        return {"status": "ok"}
    
    # 建立菜單卡片
    menu_items = [
        {"id": "A", "name": "三鮮水餃", "price": 120, "type": "葷食", "image": "https://via.placeholder.com/250x150?text=A 餐"},
        {"id": "B", "name": "宮保雞丁飯", "price": 150, "type": "葷食", "image": "https://via.placeholder.com/250x150?text=B 餐"},
        {"id": "C", "name": "紅燒牛肉麵", "price": 180, "type": "葷食", "image": "https://via.placeholder.com/250x150?text=C 餐"},
        {"id": "D", "name": "素三鮮水餃", "price": 110, "type": "素食", "image": "https://via.placeholder.com/250x150?text=D 餐"},
        {"id": "E", "name": "麻婆豆腐飯 (素)", "price": 130, "type": "素食", "image": "https://via.placeholder.com/250x150?text=E 餐"},
        {"id": "F", "name": "素蔬食麵", "price": 100, "type": "素食", "image": "https://via.placeholder.com/250x150?text=F 餐"},
    ]
    
    # 建立 Carousel
    carousel_contents = []
    for item in menu_items:
        bubble = BubbleTemplate(
            hero_image=ImageComponent(url=item["image"], size="full"),
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(text=f"{item['type']}", size="xs", color="#666666"),
                    TextComponent(text=item["name"], size="md", weight="bold"),
                    TextComponent(text=f"💰 {item['price']} 元", size="sm"),
                ]
            ),
            action=ButtonComponent(
                label="🛒 我要訂",
                action_type="postback",
                data=f"confirm_order={item['id']}"
            )
        )
        carousel_contents.append(bubble)
    
    carousel = CarouselTemplate(contents=carousel_contents)
    flex_message = FlexMessage(alt_text="今日菜單", content=carousel)
    
    # 先傳送文字說明
    await line_bot.reply_message(
        reply_token=reply_token,
        messages=[
            TextMessage(text="🍱 今日菜單 (2026/06/12)\n\n請滑動選擇要訂的餐點"),
            flex_message
        ]
    )
    
    return {"status": "ok"}

async def confirm_menu_selection(selection: str, user_id: str, reply_token: str) -> dict:
    """確認菜單選擇"""
    # TODO: 從 session 或資料庫讀取用戶選擇
    return {"status": "ok"}

async def confirm_order_from_menu(menu_id: str, user_id: str, reply_token: str) -> dict:
    """從菜單確認訂餐"""
    if not line_bot:
        return {"status": "ok"}
    
    # 模擬菜單資料
    menu_data = {
        "A": {"name": "三鮮水餃", "price": 120},
        "B": {"name": "宮保雞丁飯", "price": 150},
        "C": {"name": "紅燒牛肉麵", "price": 180},
        "D": {"name": "素三鮮水餃", "price": 110},
        "E": {"name": "麻婆豆腐飯 (素)", "price": 130},
        "F": {"name": "素蔬食麵", "price": 100},
    }
    
    if menu_id not in menu_data:
        await line_bot.reply_message(reply_token=reply_token, messages=[TextMessage(text="❌ 無效的菜單選項")])
        return {"status": "ok"}
    
    item = menu_data[menu_id]
    
    # 建立確認對話
    await line_bot.reply_message(
        reply_token=reply_token,
        messages=[
            TextMessage(text=f"✅ 你要訂 {item['name']} 嗎？\n\n價格：{item['price']} 元\n補助：150 元\n自付：{max(0, item['price'] - 150)} 元\n\n回覆 1 確認，2 重新選擇"),
        ]
    )
    
    # TODO: 儲存用戶選擇到 session
    return {"status": "ok"}

async def show_my_orders(user_id: str) -> str:
    """顯示我的訂單"""
    # TODO: 實際實作時從資料庫讀取
    return """📋 我的訂單

✅ 今日已訂：
• 宮保雞丁飯 - 150 元
  補助：150 元 | 自付：0 元
  餐廳：美味中式料理
  取餐時間：11:30-13:00
  狀態：已確認

📊 本月統計：
• 用餐次數：15 次
• 總補助：2,250 元
• 總自付：450 元"""

async def handle_order(message: str, user_id: str) -> str:
    """處理訂餐指令"""
    # 解析菜色名稱
    menu_name = message[1:].strip()  # 移除"訂"或"我要訂"字
    
    if not menu_name:
        return "❌ 請輸入要訂的菜色名稱\n例如：訂 三鮮水餃"
    
    # TODO: 實際實作時檢查庫存、補助、休假等
    return f"""✅ 訂餐成功！

🍱 {menu_name}
📅 用餐日期：今日
💰 價格：待確認
🏪 餐廳：待確認
⏰ 取餐時間：11:30-13:00

請稍候，管理員確認後會通知您。"""

async def cancel_order(user_id: str) -> str:
    """取消訂單"""
    # TODO: 實際實作時從資料庫讀取並取消
    return """✅ 訂單已取消

你已取消今日的訂單。

若要重新訂餐，請輸入：訂 [菜色名稱]"""

async def show_deadline() -> str:
    """顯示訂餐截止時間"""
    return """⏰ 訂餐截止時間

今日截止：11:30
取餐時間：11:30-13:00

⚠️ 請在截止前完成訂餐，逾期不候！"""

# ============ 管理員功能 ============

async def handle_admin_command(command: str, user_id: str) -> str:
    """處理管理員指令"""
    # TODO: 實際實作時驗證管理員權限
    
    if command.startswith("menu"):
        return "📋 管理員：菜單管理\n• /admin menu set - 設定今日菜單\n• /admin menu upload - 上傳菜單圖片"
    
    elif command.startswith("deadline"):
        return "⏰ 管理員：截止時間管理\n• /admin deadline set 11:30 - 設定截止時間"
    
    elif command.startswith("orders"):
        return "📊 管理員：訂單查詢\n• /admin orders list - 查看所有訂單\n• /admin orders export - 匯出 Excel"
    
    else:
        return "❌ 未知管理員指令\n使用 /admin 查看可用指令"

async def handle_image_upload(source: dict, reply_token: str, image_id: str) -> dict:
    """處理圖片上傳 (管理員用)"""
    if not line_bot:
        return {"status": "ok"}
    
    # TODO: 實際實作時下載圖片並進行 OCR
    await line_bot.reply_message(
        reply_token=reply_token,
        messages=[TextMessage(text="✅ 圖片已接收！\n\n管理員將進行 OCR 辨識菜單內容。")]
    )
    
    return {"status": "ok"}

# ============ Rich Menu 設定 ============

# Rich Menu JSON 配置
RICH_MENU_CONFIG = {
    "size": {"width": 2500, "height": 1686},
    "selected": True,
    "name": "訂餐主選單",
    "chatBarText": "🍱 選單",
    "areas": [
        {"bounds": {"x": 0, "y": 0, "width": 833, "height": 843}, "action": {"type": "postback", "data": "action=menu"}},
        {"bounds": {"x": 833, "y": 0, "width": 834, "height": 843}, "action": {"type": "postback", "data": "action=order"}},
        {"bounds": {"x": 1667, "y": 0, "width": 833, "height": 843}, "action": {"type": "postback", "data": "action=myorder"}},
        {"bounds": {"x": 0, "y": 843, "width": 1250, "height": 843}, "action": {"type": "postback", "data": "action=help"}},
        {"bounds": {"x": 1250, "y": 843, "width": 1250, "height": 843}, "action": {"type": "postback", "data": "action=settings"}}
    ]
}

@router.post("/richmenu/setup")
async def setup_rich_menu():
    """設定 Rich Menu (管理員用)"""
    if not line_bot:
        return JSONResponse({"status": "error", "message": "LINE Bot 未初始化"})
    
    try:
        # 上傳 Rich Menu
        # TODO: 實際需要上傳圖片，這裡先跳過
        # await line_bot.create_rich_menu(rich_menu_id="order-system-menu", rich_menu=RICH_MENU_CONFIG)
        
        return JSONResponse({"status": "ok", "message": "Rich Menu 設定完成"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})
