from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import hashlib
import hmac
import base64
import json
import os
from datetime import datetime, date

from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.menu_item import MenuItem
from backend.app.models.order import Order
from backend.app.models.daily_setting import DailySetting
from backend.app.models.restaurant import Restaurant
from backend.app.services.db_service import (
    UserService,
    MenuItemService,
    OrderService,
    DailySettingService,
    RestaurantService
)

router = APIRouter()

# LINE 驗證
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
    channel_secret = os.getenv("LINE_CHANNEL_SECRET")
    
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
async def handle_line_webhook(request: Request, db: Session = Depends(get_db)):
    """處理 LINE Webhook 事件"""
    body = await request.json()
    event_data = LineWebhookEvent(**body)
    
    # 處理每個事件
    results = []
    for event in event_data.events:
        result = await process_event(event, db)
        if result:
            results.append(result)
    
    if results:
        return JSONResponse(results)
    
    return JSONResponse({"status": "ok"})

async def process_event(event: LineEvent, db: Session) -> dict:
    """處理單一事件"""
    try:
        # 處理追蹤事件
        if event.type == "follow":
            await handle_follow_event(event, db)
            return {"status": "ok"}
        
        # 處理訊息事件
        elif event.type == "message":
            if event.message and event.message.type == "text":
                user_message = event.message.text
                response = await process_user_command(user_message, event.source, event.replyToken, db)
                return response
            
            elif event.message and event.message.type == "image":
                # 處理圖片上傳 (管理員用)
                return await handle_image_upload(event.source, event.replyToken, event.message.id, db)
        
        # 處理 Postback 事件 (Rich Menu 按鈕點擊)
        elif event.type == "postback":
            if event.postback:
                action_data = event.postback.data
                response = await handle_postback(action_data, event.source, event.replyToken, db)
                return response
        
        return {"status": "ok"}
    
    except Exception as e:
        print(f"處理事件錯誤：{e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

# ============ 事件處理 ============

async def handle_follow_event(event: LineEvent, db: Session):
    """處理追蹤事件"""
    user_id = event.source.userId
    
    # 建立或取得用戶
    user = UserService.create_or_get(
        db=db,
        line_user_id=user_id,
        name=f"LINE 用戶 {user_id[:8]}",
        employee_id=None
    )
    
    # 傳送歡迎訊息
    welcome_message = """👋 歡迎使用訂餐系統！

請輸入 /help 查看可用指令

💡 小技巧：點擊下方的「選單」按鈕快速操作"""
    
    # TODO: 實際使用 line_bot.reply_message
    print(f"Send welcome message to {user_id}: {welcome_message}")

async def process_user_command(message: str, source: dict, reply_token: str, db: Session) -> dict:
    """處理用戶指令"""
    user_id = source.get("userId")
    
    # 取得用戶物件
    user = UserService.get_by_line_user_id(db, user_id)
    if not user:
        user = UserService.create_or_get(db, user_id, f"LINE 用戶 {user_id[:8]}")
    
    # 指令解析
    if message.startswith("/"):
        response_text = await handle_command(message, user, db)
    elif message in ["菜單", "看菜單", "今日菜單", "今天菜單"]:
        response = await show_menu_carousel(user, reply_token, db)
        return response
    elif message in ["我的訂單", "訂單"]:
        response_text = await show_my_orders(user, db)
    elif message.startswith("訂") or message.startswith("我要訂"):
        response_text = await handle_order(message, user, db)
    elif message in ["取消訂單", "取消"]:
        response_text = await cancel_order(user, db)
    elif message in ["截止時間", "訂餐截止"]:
        response_text = await show_deadline(db)
    elif message in ["1", "2", "3", "4", "5"]:
        # 確認選擇
        response = await confirm_menu_selection(message, user, reply_token, db)
        return response
    else:
        response_text = get_welcome_message()
    
    # 傳送文字訊息
    if response_text:
        print(f"Reply to {reply_token}: {response_text}")
        # TODO: 實際使用 line_bot.reply_message
    
    return {"status": "ok"}

async def handle_postback(action_data: str, source: dict, reply_token: str, db: Session) -> dict:
    """處理 Rich Menu Postback"""
    user_id = source.get("userId")
    user = UserService.get_by_line_user_id(db, user_id)
    
    if not user:
        return {"status": "ok"}
    
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
        response = await show_menu_carousel(user, reply_token, db)
        return response
    
    elif action == "order":
        response_text = "📝 要訂餐請輸入：訂 [菜色名稱]\n例如：訂 三鮮水餃"
        print(f"Reply to {reply_token}: {response_text}")
    
    elif action == "myorder":
        response_text = await show_my_orders(user, db)
        if response_text:
            print(f"Reply to {reply_token}: {response_text}")
    
    elif action == "help":
        response_text = get_help_message()
        print(f"Reply to {reply_token}: {response_text}")
    
    elif action == "settings":
        response_text = "⚙️ 設定\n\n• 通知設定\n• 取餐地點\n\n需要更多設定請聯繫管理員"
        print(f"Reply to {reply_token}: {response_text}")
    
    elif action == "confirm_order":
        # 確認訂餐
        menu_id = value
        response = await confirm_order_from_menu(menu_id, user, reply_token, db)
        return response
    
    return {"status": "ok"}

# ============ 指令函數 ============

async def handle_command(command: str, user: User, db: Session) -> str:
    """處理系統指令"""
    if command == "/help":
        return get_help_message()
    
    elif command == "/menu":
        return await show_menu(user, db)
    
    elif command == "/order":
        return await show_my_orders(user, db)
    
    elif command == "/cancel":
        return await cancel_order(user, db)
    
    elif command.startswith("/admin"):
        # 管理員指令
        return await handle_admin_command(command[6:], user, db)
    
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

async def show_menu(user: User, db: Session) -> str:
    """顯示今日菜單 (文字版)"""
    menu_items = MenuItemService.get_today_menu(db)
    
    if not menu_items:
        return "❌ 今日暫無菜單，請稍後再查詢或聯繫管理員。"
    
    # 分組顯示
    meat_items = [item for item in menu_items if item.food_type == "meat"]
    veg_items = [item for item in menu_items if item.food_type == "vegetarian"]
    
    # 取得今日設定
    daily_setting = DailySettingService.get_today_setting(db)
    subsidy = daily_setting.subsidy_amount if daily_setting else 150.0
    deadline = daily_setting.order_end_time if daily_setting else datetime.time(11, 30)
    
    text = f"🍱 今日菜單 ({date.today().strftime('%Y/%m/%d')})\n\n"
    
    if meat_items:
        text += "【葷食】\n"
        for item in meat_items:
            restaurant_name = item.restaurant.name if item.restaurant else "未知餐廳"
            text += f"• {item.name} - {item.price} 元 ({restaurant_name})\n"
        text += "\n"
    
    if veg_items:
        text += "【素食】\n"
        for item in veg_items:
            restaurant_name = item.restaurant.name if item.restaurant else "未知餐廳"
            text += f"• {item.name} - {item.price} 元 ({restaurant_name})\n"
        text += "\n"
    
    text += f"💰 今日補助：{subsidy} 元\n"
    text += f"⏰ 訂餐截止：今日 {deadline.strftime('%H:%M')}\n"
    text += f"📍 取餐時間：11:30-13:00\n\n"
    text += "要訂餐請輸入：訂 [菜色名稱]\n"
    text += "或直接點擊菜單按鈕選擇"
    
    return text

async def show_menu_carousel(user: User, reply_token: str, db: Session) -> dict:
    """顯示今日菜單 (Carousel 卡片版)"""
    menu_items = MenuItemService.get_today_menu(db)
    
    if not menu_items:
        # 若無菜單，傳送文字訊息
        print(f"Reply: ❌ 今日暫無菜單")
        return {"status": "ok"}
    
    # 限制最多顯示 10 個
    menu_items = menu_items[:10]
    
    # 建立 Carousel 內容
    carousel_contents = []
    for item in menu_items:
        restaurant_name = item.restaurant.name if item.restaurant else "未知餐廳"
        
        # 模擬卡片內容 (實際需使用 line_bot 模組)
        bubble_data = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": item.image_url or "https://via.placeholder.com/250x150?text=Menu",
                "size": "full"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "葷食" if item.food_type == "meat" else "素食",
                        "size": "xs",
                        "color": "#666666"
                    },
                    {
                        "type": "text",
                        "text": item.name,
                        "size": "md",
                        "weight": "bold"
                    },
                    {
                        "type": "text",
                        "text": f"💰 {item.price} 元",
                        "size": "sm"
                    },
                    {
                        "type": "text",
                        "text": restaurant_name,
                        "size": "xs",
                        "color": "#666666"
                    }
                ]
            },
            "actions": [
                {
                    "type": "postback",
                    "label": "🛒 我要訂",
                    "data": f"confirm_order={item.id}"
                }
            ]
        }
        carousel_contents.append(bubble_data)
    
    # 傳送 Carousel
    flex_message = {
        "type": "flex",
        "altText": "今日菜單",
        "contents": {
            "type": "carousel",
            "contents": carousel_contents
        }
    }
    
    print(f"Send carousel to {reply_token}: {len(carousel_contents)} items")
    
    return {"status": "ok"}

async def confirm_menu_selection(selection: str, user: User, reply_token: str, db: Session) -> dict:
    """確認菜單選擇"""
    # TODO: 從 session 或資料庫讀取用戶選擇
    print(f"User {user.id} selected: {selection}")
    return {"status": "ok"}

async def confirm_order_from_menu(menu_id: str, user: User, reply_token: str, db: Session) -> dict:
    """從菜單確認訂餐"""
    try:
        menu_item_id = int(menu_id)
    except ValueError:
        print(f"Reply: ❌ 無效的菜單選項")
        return {"status": "ok"}
    
    # 取得菜單項目
    menu_item = db.query(MenuItem).filter(MenuItem.id == menu_item_id).first()
    if not menu_item:
        print(f"Reply: ❌ 找不到該菜單")
        return {"status": "ok"}
    
    # 取得今日設定
    daily_setting = DailySettingService.get_today_setting(db)
    subsidy = daily_setting.subsidy_amount if daily_setting else 150.0
    
    self_pay = max(0, menu_item.price - subsidy)
    restaurant_name = menu_item.restaurant.name if menu_item.restaurant else "未知餐廳"
    
    # 建立確認訊息
    confirm_text = f"""✅ 你要訂 {menu_item.name} 嗎？

🏪 餐廳：{restaurant_name}
💰 價格：{menu_item.price} 元
補助：{subsidy} 元
自付：{self_pay} 元

回覆 1 確認，2 重新選擇"""
    
    print(f"Reply to {reply_token}: {confirm_text}")
    
    # TODO: 儲存用戶選擇到 session (可改用 Redis 或資料庫)
    
    return {"status": "ok"}

async def show_my_orders(user: User, db: Session) -> str:
    """顯示我的訂單"""
    # 取得今日訂單
    today_order = OrderService.get_today_order(db, user.id)
    
    if not today_order:
        return """📋 我的訂單

今日尚未訂餐。

要訂餐請輸入：訂 [菜色名稱]
或點擊「菜單」按鈕選擇"""
    
    # 取得菜單與餐廳資訊
    menu_item = db.query(MenuItem).filter(MenuItem.id == today_order.menu_item_id).first()
    restaurant = db.query(Restaurant).filter(Restaurant.id == today_order.restaurant_id).first()
    
    menu_name = menu_item.name if menu_item else "未知菜色"
    restaurant_name = restaurant.name if restaurant else "未知餐廳"
    
    status_map = {
        "pending": "待確認",
        "confirmed": "已確認",
        "cancelled": "已取消",
        "picked_up": "已取餐"
    }
    status_text = status_map.get(today_order.status, today_order.status)
    
    text = f"""📋 我的訂單

✅ 今日已訂：
• {menu_name} - {today_order.price} 元
  補助：{today_order.subsidy_amount} 元 | 自付：{today_order.self_pay_amount} 元
  餐廳：{restaurant_name}
  取餐時間：11:30-13:00
  狀態：{status_text}"""
    
    # 取得本月統計
    orders = OrderService.get_user_orders(db, user.id, limit=30)
    if orders:
        total_subsidy = sum(order.subsidy_amount for order in orders)
        total_self_pay = sum(order.self_pay_amount for order in orders)
        text += f"""

📊 最近統計：
• 用餐次數：{len(orders)} 次
• 總補助：{total_subsidy} 元
• 總自付：{total_self_pay} 元"""
    
    return text

async def handle_order(message: str, user: User, db: Session) -> str:
    """處理訂餐指令"""
    # 解析菜色名稱
    menu_name = message[1:].strip()  # 移除"訂"或"我要訂"字
    
    if not menu_name:
        return "❌ 請輸入要訂的菜色名稱\n例如：訂 三鮮水餃"
    
    # 檢查今日是否已有訂單
    existing_order = OrderService.get_today_order(db, user.id)
    if existing_order:
        return f"""⚠️ 今日已訂餐

• {menu_name}
狀態：{existing_order.status}

若要更改，請先「取消訂單」再重新訂餐。"""
    
    # 查詢菜單
    menu_item = MenuItemService.get_by_name(db, menu_name)
    
    if not menu_item:
        # 嘗試模糊搜尋
        menu_items = MenuItemService.get_today_menu(db)
        matched = [item for item in menu_items if menu_name in item.name]
        
        if matched:
            menu_names = [item.name for item in matched[:5]]
            return f"""❌ 找不到完全符合的菜色，您可能要找：

{menu_names}

請輸入完整的菜色名稱。"""
        
        return f"❌ 找不到「{menu_name}」\n\n請使用「菜單」指令查看今日可用菜色。"
    
    # 取得今日設定
    daily_setting = DailySettingService.get_today_setting(db)
    subsidy = daily_setting.subsidy_amount if daily_setting else 150.0
    
    # 建立訂單
    order = OrderService.create_order(
        db=db,
        user_id=user.id,
        menu_item_id=menu_item.id,
        subsidy_amount=subsidy
    )
    
    if not order:
        return "❌ 訂餐失敗，請稍後再試或聯繫管理員。"
    
    restaurant = db.query(Restaurant).filter(Restaurant.id == order.restaurant_id).first()
    restaurant_name = restaurant.name if restaurant else "未知餐廳"
    
    return f"""✅ 訂餐成功！

🍱 {menu_item.name}
🏪 餐廳：{restaurant_name}
📅 用餐日期：{date.today().strftime('%Y/%m/%d')}
💰 價格：{order.price} 元
補助：{order.subsidy_amount} 元
自付：{order.self_pay_amount} 元
⏰ 取餐時間：11:30-13:00

請在截止前取餐，逾期不候！"""

async def cancel_order(user: User, db: Session) -> str:
    """取消訂單"""
    # 取得今日訂單
    today_order = OrderService.get_today_order(db, user.id)
    
    if not today_order:
        return "❌ 今日沒有訂單可取消。"
    
    if today_order.status == "cancelled":
        return "❌ 訂單已經取消。"
    
    # 取消訂單
    success = OrderService.cancel_order(db, today_order.id, user.id)
    
    if success:
        menu_item = db.query(MenuItem).filter(MenuItem.id == today_order.menu_item_id).first()
        menu_name = menu_item.name if menu_item else "該菜色"
        
        return f"""✅ 訂單已取消

你已取消：{menu_name}

若要重新訂餐，請輸入：訂 [菜色名稱]"""
    
    return "❌ 取消失敗，可能已超過截止時間或訂單狀態已變更。"

async def show_deadline(db: Session) -> str:
    """顯示訂餐截止時間"""
    daily_setting = DailySettingService.get_today_setting(db)
    
    if not daily_setting:
        return """⏰ 訂餐截止時間

今日截止：11:30 (預設)
取餐時間：11:30-13:00

⚠️ 請在截止前完成訂餐，逾期不候！"""
    
    deadline = daily_setting.order_end_time
    pickup_start = daily_setting.pickup_start_time
    pickup_end = daily_setting.pickup_end_time
    
    return f"""⏰ 訂餐截止時間

今日截止：{deadline.strftime('%H:%M')}
取餐時間：{pickup_start.strftime('%H:%M')}-{pickup_end.strftime('%H:%M')}

⚠️ 請在截止前完成訂餐，逾期不候！"""

# ============ 管理員功能 ============

async def handle_admin_command(command: str, user: User, db: Session) -> str:
    """處理管理員指令"""
    # TODO: 實際實作時驗證管理員權限
    
    if command.startswith("menu"):
        return "📋 管理員：菜單管理\n• /admin menu set - 設定今日菜單\n• /admin menu upload - 上傳菜單圖片"
    
    elif command.startswith("deadline"):
        return "⏰ 管理員：截止時間管理\n• /admin deadline set 11:30 - 設定截止時間"
    
    elif command.startswith("orders"):
        # 取得訂單統計
        summary = OrderService.get_order_summary(db)
        
        text = f"""📊 今日訂單統計 ({date.today().strftime('%Y/%m/%d')})

總訂單：{summary['total_orders']} 筆
總金額：{summary['total_amount']} 元
總補助：{summary['total_subsidy']} 元
總自付：{summary['total_self_pay']} 元

按餐廳統計："""
        
        for restaurant_name, stats in summary['restaurant_stats'].items():
            text += f"\n• {restaurant_name}: {stats['count']} 筆 ({stats['amount']} 元)"
        
        return text
    
    elif command.startswith("users"):
        users = UserService.get_all_users(db)
        return f"👥 用戶列表\n總共 {len(users)} 位用戶"
    
    else:
        return "❌ 未知管理員指令\n使用 /admin 查看可用指令"

async def handle_image_upload(source: dict, reply_token: str, image_id: str, db: Session) -> dict:
    """處理圖片上傳 (管理員用)"""
    user_id = source.get("userId")
    user = UserService.get_by_line_user_id(db, user_id)
    
    if not user:
        return {"status": "ok"}
    
    # TODO: 實際實作時下載圖片並進行 OCR
    print(f"Image upload from user {user.id}: {image_id}")
    
    print(f"Reply: ✅ 圖片已接收！\n\n管理員將進行 OCR 辨識菜單內容。")
    
    return {"status": "ok"}
