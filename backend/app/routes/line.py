from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import hashlib
import hmac
import base64
import json

router = APIRouter()

# LINE 驗證
class LineVerifyRequest(BaseModel):
    mode: str
    timestamp: str
    channelAccessToken: str
    signature: str

class LineVerifyResponse(BaseModel):
    validity: bool

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

# LINE 訊息處理
class LineMessage(BaseModel):
    type: str
    text: Optional[str] = None

class LineEvent(BaseModel):
    type: str
    mode: str
    timestamp: int
    source: dict
    href: Optional[str] = None
    replyToken: Optional[str] = None
    message: Optional[LineMessage] = None
    message_id: Optional[int] = None

class LineWebhookEvent(BaseModel):
    destination: Optional[str] = None
    events: List[LineEvent]

@router.post("/webhook")
async def handle_line_webhook(request: Request):
    """處理 LINE Webhook 事件"""
    body = await request.json()
    event_data = LineWebhookEvent(**body)
    
    responses = []
    
    for event in event_data.events:
        if event.type == "message" and event.message and event.message.type == "text":
            # 處理文字訊息
            user_message = event.message.text
            reply_token = event.replyToken
            
            # 解析用戶指令
            response_text = await process_user_command(user_message, event.source)
            
            if response_text:
                responses.append({
                    "type": "text",
                    "text": response_text
                })
    
    if responses:
        return JSONResponse({
            "replyToken": event_data.events[0].replyToken,
            "messages": responses
        })
    
    return JSONResponse({"status": "ok"})

async def process_user_command(message: str, source: dict) -> str:
    """處理用戶指令"""
    user_id = source.get("userId")
    
    # 指令解析
    if message.startswith("/"):
        return await handle_command(message, user_id)
    elif message in ["菜單", "看菜單", "今日菜單"]:
        return await show_menu(user_id)
    elif message in ["我的訂單", "訂單"]:
        return await show_my_orders(user_id)
    elif message.startswith("訂"):
        return await handle_order(message, user_id)
    else:
        return "👋 歡迎使用訂餐系統！\n\n可使用的指令：\n• 菜單 - 查看今日菜單\n• 我的訂單 - 查看已訂餐點\n• 訂 [菜色名稱] - 訂餐\n• /help - 查看幫助"

async def handle_command(command: str, user_id: str) -> str:
    """處理系統指令"""
    if command == "/help":
        return """📱 訂餐系統使用說明

🔍 查詢指令：
• 菜單 - 查看今日菜單
• 我的訂單 - 查看已訂餐點
• 補助餘額 - 查看今日補助

📝 訂餐指令：
• 訂 [菜色名稱] - 例如：訂 三鮮水餃
• 取消訂單 - 取消今日訂單

⚙️ 其他指令：
• /help - 查看幫助"""
    
    elif command == "/menu":
        return await show_menu(user_id)
    
    elif command == "/order":
        return await show_my_orders(user_id)
    
    else:
        return "❌ 未知指令，請使用 /help 查看可用指令"

async def show_menu(user_id: str) -> str:
    """顯示今日菜單"""
    # TODO: 實際實作時從資料庫讀取
    return """🍱 今日菜單 (2024/06/12)

【葷食】
• 三鮮水餃 - 120 元
• 宮保雞丁飯 - 150 元
• 红烧牛肉麵 - 180 元

【素食】
• 素三鮮水餃 - 110 元
• 麻婆豆腐飯 (素) - 130 元
• 素蔬食麵 - 100 元

💰 今日補助：150 元
⏰ 訂餐截止：今日 16:00

要訂餐請輸入：訂 [菜色名稱]"""

async def show_my_orders(user_id: str) -> str:
    """顯示我的訂單"""
    # TODO: 實際實作時從資料庫讀取
    return """📋 我的訂單

✅ 今日已訂：
• 宮保雞丁飯 - 150 元
  補助：150 元 | 自付：0 元
  餐廳：美味中式料理
  取餐時間：11:30-13:00

📊 本月統計：
• 用餐次數：15 次
• 總補助：2,250 元
• 總自付：450 元"""

async def handle_order(message: str, user_id: str) -> str:
    """處理訂餐指令"""
    # 解析菜色名稱
    menu_name = message[1:].strip()  # 移除"訂"字
    
    if not menu_name:
        return "❌ 請輸入要訂的菜色名稱\n例如：訂 三鮮水餃"
    
    # TODO: 實際實作時檢查庫存、補助、休假等
    return f"""✅ 訂餐成功！

🍱 {menu_name}
📅 用餐日期：今日
💰 價格：待確認
🏪 餐廳：待確認

請稍候，管理員確認後會通知您。"""
