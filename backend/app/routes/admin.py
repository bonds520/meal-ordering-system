"""
管理員 API 路由
提供管理員後台所需的 API 端點
"""

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, date, time
import os
import shutil
import logging

from app.models.base import get_db
from app.models.user import User
from app.models.restaurant import Restaurant
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.daily_setting import DailySetting
from app.models.leave_record import LeaveRecord
from app.models.order_log import OrderLog
from app.services.db_service import (
    UserService,
    RestaurantService,
    MenuItemService,
    OrderService,
    DailySettingService,
    LeaveRecordService,
    OrderLogService
)
from app.services.ocr_service import ocr_service

router = APIRouter(prefix="/api/admin", tags=["admin"])

logger = logging.getLogger(__name__)

# ============ 權限驗證 ============

def verify_admin(user: User) -> bool:
    """驗證管理員權限"""
    return user.is_admin if user else False

def get_current_admin(db: Session, line_user_id: Optional[str] = None) -> User:
    """取得當前管理員用戶"""
    # TODO: 實際應從 JWT token 或 session 取得用戶
    # 這裡先簡化，假設所有呼叫此 API 的都是管理員
    if line_user_id:
        user = UserService.get_by_line_user_id(db, line_user_id)
        if user and not user.is_admin:
            raise HTTPException(status_code=403, detail="無管理員權限")
        return user
    # 暫時允許無認證 (僅限本地測試)
    return None

# ============ 訂單管理 ============

@router.get("/orders")
async def get_all_orders(
    meal_date: Optional[date] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """取得所有訂單"""
    if not meal_date:
        meal_date = date.today()
    
    orders = OrderService.get_all_today_orders(db, meal_date)
    
    if status:
        orders = [o for o in orders if o.status == status]
    
    result = []
    for order in orders:
        user = db.query(User).filter(User.id == order.user_id).first()
        menu_item = db.query(MenuItem).filter(MenuItem.id == order.menu_item_id).first()
        restaurant = db.query(Restaurant).filter(Restaurant.id == order.restaurant_id).first()
        
        result.append({
            "id": order.id,
            "user_id": order.user_id,
            "user_name": user.name if user else "Unknown",
            "employee_id": user.employee_id if user else "Unknown",
            "meal_date": order.meal_date.isoformat(),
            "restaurant_id": order.restaurant_id,
            "restaurant_name": restaurant.name if restaurant else "Unknown",
            "menu_item_id": order.menu_item_id,
            "menu_name": menu_item.name if menu_item else "Unknown",
            "price": order.price,
            "subsidy_amount": order.subsidy_amount,
            "self_pay_amount": order.self_pay_amount,
            "status": order.status,
            "notes": order.notes,
            "created_at": order.created_at.isoformat() if order.created_at else None
        })
    
    return {"count": len(result), "orders": result}

@router.get("/orders/summary")
async def get_order_summary(
    meal_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """取得訂單統計"""
    if not meal_date:
        meal_date = date.today()
    
    summary = OrderService.get_order_summary(db, meal_date)
    
    return summary

@router.post("/orders/{order_id}/confirm")
async def confirm_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    """確認訂單"""
    success = OrderService.confirm_order(db, order_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="訂單確認失敗")
    
    logger.info(f"[ADMIN] 訂單已確認 - order_id: {order_id}")
    
    return {"status": "success", "message": "訂單已確認"}

@router.post("/orders/{order_id}/pickup")
async def mark_order_picked_up(
    order_id: int,
    db: Session = Depends(get_db)
):
    """標記訂單已取餐"""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="找不到訂單")
    
    if order.status == "picked_up":
        raise HTTPException(status_code=400, detail="訂單已標記為已取餐")
    
    old_status = order.status
    order.status = "picked_up"
    order.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(order)
    
    # 記錄日誌
    OrderLogService.create(
        db=db,
        user_id=order.user_id,
        order_id=order_id,
        action=f"取餐核銷 - {old_status} -> picked_up",
        log_type="order_pickup",
        details=f"餐廳端核銷，舊狀態：{old_status}"
    )
    
    logger.info(f"[ADMIN] 訂單已取餐 - order_id: {order_id}")
    
    return {"status": "success", "message": "訂單已標記為已取餐"}

# ============ 菜單管理 ============

@router.get("/menu")
async def get_menu_items(
    meal_date: Optional[date] = None,
    restaurant_id: Optional[int] = None,
    food_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """取得菜單項目"""
    if not meal_date:
        meal_date = date.today()
    
    query = db.query(MenuItem).filter(
        MenuItem.meal_date == meal_date,
        MenuItem.is_available == True
    )
    
    if restaurant_id:
        query = query.filter(MenuItem.restaurant_id == restaurant_id)
    
    if food_type:
        query = query.filter(MenuItem.food_type == food_type)
    
    menu_items = query.all()
    
    result = []
    for item in menu_items:
        restaurant = db.query(Restaurant).filter(Restaurant.id == item.restaurant_id).first()
        result.append({
            "id": item.id,
            "restaurant_id": item.restaurant_id,
            "restaurant_name": restaurant.name if restaurant else "Unknown",
            "meal_date": item.meal_date.isoformat(),
            "meal_type": item.meal_type,
            "name": item.name,
            "price": item.price,
            "food_type": item.food_type,
            "image_url": item.image_url,
            "is_available": item.is_available
        })
    
    return {"count": len(result), "menu_items": result}

@router.post("/menu")
async def create_menu_item(
    restaurant_id: int,
    name: str,
    price: float,
    food_type: str = "meat",
    meal_date: Optional[date] = None,
    meal_type: str = "lunch",
    image_url: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """建立菜單項目"""
    if not meal_date:
        meal_date = date.today()
    
    menu_item = MenuItemService.create(
        db=db,
        restaurant_id=restaurant_id,
        name=name,
        price=price,
        food_type=food_type,
        meal_date=meal_date,
        meal_type=meal_type,
        image_url=image_url
    )
    
    logger.info(f"[ADMIN] 建立菜單 - name: {name}, price: {price}")
    
    return {"status": "success", "menu_item": {
        "id": menu_item.id,
        "name": menu_item.name,
        "price": menu_item.price
    }}

@router.post("/menu/batch")
async def create_menu_items_batch(
    items: List[Dict[str, Any]],
    restaurant_id: int,
    meal_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """批量建立菜單項目"""
    if not meal_date:
        meal_date = date.today()
    
    created_items = MenuItemService.create_batch(
        db=db,
        restaurant_id=restaurant_id,
        items=items,
        meal_date=meal_date
    )
    
    logger.info(f"[ADMIN] 批量建立菜單 - count: {len(created_items)}")
    
    return {"status": "success", "count": len(created_items)}

@router.delete("/menu/{menu_item_id}")
async def delete_menu_item(
    menu_item_id: int,
    db: Session = Depends(get_db)
):
    """刪除菜單項目"""
    menu_item = db.query(MenuItem).filter(MenuItem.id == menu_item_id).first()
    
    if not menu_item:
        raise HTTPException(status_code=404, detail="找不到菜單項目")
    
    db.delete(menu_item)
    db.commit()
    
    logger.info(f"[ADMIN] 刪除菜單 - id: {menu_item_id}, name: {menu_item.name}")
    
    return {"status": "success", "message": "菜單已刪除"}

@router.post("/menu/upload")
async def upload_menu_image(
    file: UploadFile = File(...),
    restaurant_id: int = Form(...),
    meal_date: Optional[date] = Form(None),
    db: Session = Depends(get_db)
):
    """上傳菜單圖片並進行 OCR 辨識"""
    if not meal_date:
        meal_date = date.today()
    
    # 儲存上傳的圖片
    upload_dir = "/tmp/menu_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    image_path = os.path.join(upload_dir, f"{file.filename}")
    
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    logger.info(f"[ADMIN] 上傳菜單圖片 - path: {image_path}")
    
    # 進行 OCR 辨識
    result = ocr_service.recognize_menu(image_path)
    
    if not result:
        raise HTTPException(status_code=500, detail="OCR 辨識失敗")
    
    if result.get("success"):
        # 建立菜單項目
        created_items = []
        for item_data in result["items"]:
            menu_item = MenuItemService.create(
                db=db,
                restaurant_id=restaurant_id,
                name=item_data["name"],
                price=item_data["price"],
                food_type=item_data.get("food_type", "meat"),
                meal_date=meal_date,
                ocr_raw_text=result.get("raw_text")
            )
            created_items.append(menu_item.id)
        
        logger.info(f"[ADMIN] OCR 成功建立 {len(created_items)} 個菜單項目")
        
        return {
            "status": "success",
            "count": len(created_items),
            "item_ids": created_items,
            "items": result["items"],
            "processing_time": result.get("processing_time", 0)
        }
    else:
        # OCR 失敗，返回原始文字供管理員手動處理
        return {
            "status": "warning",
            "message": "OCR 無法自動解析，請手動輸入",
            "raw_text": result.get("raw_text", ""),
            "error": result.get("error", "辨識失敗")
        }

# ============ 每日設定管理 ============

@router.get("/settings")
async def get_daily_settings(
    meal_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """取得每日設定"""
    if not meal_date:
        meal_date = date.today()
    
    setting = DailySettingService.get_by_date(db, meal_date)
    
    if not setting:
        return {"setting": None}
    
    return {
        "setting": {
            "id": setting.id,
            "meal_date": setting.meal_date.isoformat(),
            "available_restaurants": setting.available_restaurants,
            "subsidy_amount": setting.subsidy_amount,
            "order_start_time": setting.order_start_time.isoformat() if setting.order_start_time else None,
            "order_end_time": setting.order_end_time.isoformat() if setting.order_end_time else None,
            "pickup_start_time": setting.pickup_start_time.isoformat() if setting.pickup_start_time else None,
            "pickup_end_time": setting.pickup_end_time.isoformat() if setting.pickup_end_time else None,
            "is_active": setting.is_active
        }
    }

@router.post("/settings")
async def create_or_update_daily_setting(
    meal_date: date,
    subsidy_amount: Optional[float] = 150.0,
    order_end_time: Optional[time] = None,
    available_restaurants: Optional[List[int]] = None,
    db: Session = Depends(get_db)
):
    """建立或更新每日設定"""
    if not order_end_time:
        order_end_time = time(11, 30)
    
    if not available_restaurants:
        available_restaurants = []
    
    setting = DailySettingService.create_or_update(
        db=db,
        meal_date=meal_date,
        subsidy_amount=subsidy_amount,
        order_end_time=order_end_time,
        available_restaurants=available_restaurants,
        is_active=True
    )
    
    logger.info(f"[ADMIN] 更新每日設定 - date: {meal_date}, subsidy: {subsidy_amount}")
    
    return {"status": "success", "setting": {
        "id": setting.id,
        "meal_date": setting.meal_date.isoformat(),
        "subsidy_amount": setting.subsidy_amount,
        "order_end_time": setting.order_end_time.isoformat()
    }}

# ============ 餐廳管理 ============

@router.get("/restaurants")
async def get_restaurants(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """取得所有餐廳"""
    restaurants = RestaurantService.get_all(db)
    
    result = []
    for restaurant in restaurants:
        result.append({
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
            "contact": restaurant.contact,
            "is_active": restaurant.is_active
        })
    
    return {"count": len(result), "restaurants": result}

@router.post("/restaurants")
async def create_restaurant(
    name: str,
    address: str,
    contact: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """建立餐廳"""
    restaurant = RestaurantService.create(
        db=db,
        name=name,
        address=address,
        contact=contact
    )
    
    logger.info(f"[ADMIN] 建立餐廳 - name: {name}")
    
    return {"status": "success", "restaurant": {
        "id": restaurant.id,
        "name": restaurant.name
    }}

@router.delete("/restaurants/{restaurant_id}")
async def deactivate_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    """停用餐廳"""
    restaurant = RestaurantService.get_by_id(db, restaurant_id)
    
    if not restaurant:
        raise HTTPException(status_code=404, detail="找不到餐廳")
    
    restaurant.is_active = False
    restaurant.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(restaurant)
    
    logger.info(f"[ADMIN] 停用餐廳 - id: {restaurant_id}, name: {restaurant.name}")
    
    return {"status": "success", "message": "餐廳已停用"}

# ============ 用戶管理 ============

@router.get("/users")
async def get_users(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """取得所有用戶"""
    from app.models.user import UserStatus
    
    users = UserService.get_all_users(db, UserStatus(status) if status else None)
    
    result = []
    for user in users:
        result.append({
            "id": user.id,
            "employee_id": user.employee_id,
            "name": user.name,
            "department": user.department,
            "line_user_id": user.line_user_id,
            "phone": user.phone,
            "status": user.status,
            "is_admin": user.is_admin
        })
    
    return {"count": len(result), "users": result}

@router.post("/users/{user_id}/admin")
async def set_user_admin(
    user_id: int,
    is_admin: bool = True,
    db: Session = Depends(get_db)
):
    """設定用戶為管理員"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="找不到用戶")
    
    user.is_admin = is_admin
    user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"[ADMIN] 設定管理員 - user_id: {user_id}, is_admin: {is_admin}")
    
    return {"status": "success", "message": f"用戶 {'已設定為' if is_admin else '已取消'} 管理員"}

# ============ 休假管理 ============

@router.get("/leaves")
async def get_leave_records(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """取得休假記錄"""
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()
    
    if user_id:
        leaves = LeaveRecordService.get_user_leaves(db, user_id, start_date, end_date)
    else:
        # 取得所有休假記錄
        query = db.query(LeaveRecord).filter(
            LeaveRecord.leave_date >= start_date,
            LeaveRecord.leave_date <= end_date,
            LeaveRecord.approved == True
        )
        leaves = query.all()
    
    result = []
    for leave in leaves:
        user = db.query(User).filter(User.id == leave.user_id).first()
        result.append({
            "id": leave.id,
            "user_id": leave.user_id,
            "user_name": user.name if user else "Unknown",
            "employee_id": user.employee_id if user else "Unknown",
            "leave_date": leave.leave_date.isoformat(),
            "leave_type": leave.leave_type,
            "approved": leave.approved,
            "ocr_confidence": leave.ocr_confidence,
            "needs_review": leave.needs_review
        })
    
    return {"count": len(result), "leaves": result}

@router.post("/leaves")
async def create_leave_record(
    user_id: int,
    leave_date: date,
    leave_type: str = "annual",
    approved: bool = False,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """建立休假記錄"""
    leave_record = LeaveRecordService.create(
        db=db,
        user_id=user_id,
        leave_date=leave_date,
        leave_type=leave_type,
        approved=approved,
        notes=notes
    )
    
    logger.info(f"[ADMIN] 建立休假記錄 - user_id: {user_id}, date: {leave_date}")
    
    return {"status": "success", "leave_record": {
        "id": leave_record.id,
        "user_id": leave_record.user_id,
        "leave_date": leave_record.leave_date.isoformat()
    }}

# ============ OCR 管理 ============

@router.post("/ocr/leave-form")
async def recognize_leave_form(
    file: UploadFile = File(...),
    employee_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """上傳休假表圖片並進行 OCR 辨識"""
    # 儲存上傳的圖片
    upload_dir = "/tmp/leave_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    image_path = os.path.join(upload_dir, f"{file.filename}")
    
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    logger.info(f"[ADMIN] 上傳休假表圖片 - path: {image_path}")
    
    # 進行 OCR 辨識
    result = ocr_service.recognize_leave_form(image_path, employee_id)
    
    if not result:
        raise HTTPException(status_code=500, detail="OCR 辨識失敗")
    
    if result.get("success"):
        # 自動建立休假記錄
        created_leaves = []
        if employee_id:
            user = UserService.get_by_employee_id(db, employee_id)
            if user:
                for leave_date in result["leave_dates"]:
                    try:
                        leave_date_obj = datetime.strptime(leave_date, "%Y-%m-%d").date()
                        leave_record = LeaveRecordService.create(
                            db=db,
                            user_id=user.id,
                            leave_date=leave_date_obj,
                            leave_type=result.get("leave_type", "annual"),
                            approved=True,
                            notes=result.get("notes"),
                        )
                        created_leaves.append(leave_record.id)
                    except ValueError:
                        logger.warning(f"無效日期格式：{leave_date}")
        
        logger.info(f"[ADMIN] 休假表 OCR 成功建立 {len(created_leaves)} 筆休假記錄")
        
        return {
            "status": "success",
            "count": len(created_leaves),
            "leave_ids": created_leaves,
            "leave_dates": result["leave_dates"],
            "leave_type": result.get("leave_type", ""),
            "processing_time": result.get("processing_time", 0)
        }
    else:
        return {
            "status": "warning",
            "message": "OCR 無法自動解析，請手動輸入",
            "raw_text": result.get("raw_text", ""),
            "error": result.get("error", "辨識失敗")
        }

@router.get("/ocr/models")
async def list_ocr_models():
    """列出已安裝的 OCR 模型"""
    models = ocr_service.list_models()
    return {"models": models}

@router.post("/ocr/models/pull")
async def pull_ocr_model(model_name: str):
    """下載 OCR 模型"""
    success = ocr_service.pull_model(model_name)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"模型下載失敗：{model_name}")
    
    return {"status": "success", "message": f"模型 {model_name} 下載完成"}

# ============ 系統健康檢查 ============

@router.get("/health")
async def admin_health_check(db: Session = Depends(get_db)):
    """管理員端健康檢查"""
    try:
        # 檢查資料庫
        db.execute("SELECT 1")
        db_ok = True
    except Exception as e:
        db_ok = False
    
    # 檢查 OCR 服務
    ocr_ok = ocr_service.health_check()
    
    return {
        "status": "healthy" if (db_ok and ocr_ok) else "unhealthy",
        "database": "ok" if db_ok else "error",
        "ocr_service": "ok" if ocr_ok else "error",
        "timestamp": datetime.utcnow().isoformat()
    }
