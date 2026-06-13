from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.models.order import Order
from app.models.user import User
from app.models.menu_item import MenuItem
from app.models.daily_setting import DailySetting
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

router = APIRouter()

class OrderCreate(BaseModel):
    menu_item_id: int
    meal_date: Optional[date] = None

class OrderResponse(BaseModel):
    id: int
    menu_name: str
    restaurant_name: str
    meal_date: date
    price: float
    subsidy_amount: float
    self_pay_amount: float
    status: str
    qr_code: Optional[str]

@router.post("/", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)  # TODO: 實際實作時從 LINE token 解析
):
    """建立訂單"""
    # 查找菜單項目
    menu_item = db.query(MenuItem).get(order_data.menu_item_id)
    if not menu_item:
        raise HTTPException(status_code=404, detail="菜單項目不存在")
    
    # 檢查是否可訂
    if not menu_item.is_available:
        raise HTTPException(status_code=400, detail="此菜色目前不可訂")
    
    # 取得當日設定
    meal_date = order_data.meal_date or menu_item.meal_date
    daily_setting = db.query(DailySetting).filter(
        DailySetting.meal_date == meal_date,
        DailySetting.is_active == True
    ).first()
    
    if not daily_setting:
        raise HTTPException(status_code=400, detail="今日未開放訂餐")
    
    # 計算補助
    subsidy_amount = daily_setting.subsidy_amount
    self_pay_amount = max(0, menu_item.price - subsidy_amount)
    
    # 建立訂單
    new_order = Order(
        user_id=current_user.id,
        meal_date=meal_date,
        restaurant_id=menu_item.restaurant_id,
        menu_item_id=menu_item.id,
        price=menu_item.price,
        subsidy_amount=subsidy_amount,
        self_pay_amount=self_pay_amount
    )
    
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    return OrderResponse(
        id=new_order.id,
        menu_name=menu_item.name,
        restaurant_name="待確認",  # TODO: 從 restaurant 表取得
        meal_date=new_order.meal_date,
        price=new_order.price,
        subsidy_amount=new_order.subsidy_amount,
        self_pay_amount=new_order.self_pay_amount,
        status=new_order.status,
        qr_code=new_order.qr_code
    )

@router.get("/my", response_model=List[OrderResponse])
async def get_my_orders(
    meal_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)
):
    """取得我的訂單"""
    query = db.query(Order).filter(Order.user_id == current_user.id)
    
    if meal_date:
        query = query.filter(Order.meal_date == meal_date)
    
    orders = query.all()
    
    return [{
        "id": order.id,
        "menu_name": "待確認",
        "restaurant_name": "待確認",
        "meal_date": order.meal_date,
        "price": order.price,
        "subsidy_amount": order.subsidy_amount,
        "self_pay_amount": order.self_pay_amount,
        "status": order.status,
        "qr_code": order.qr_code
    } for order in orders]

@router.delete("/{order_id}")
async def cancel_order(order_id: int, db: Session = Depends(get_db)):
    """取消訂單"""
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="訂單不存在")
    
    # 檢查是否可以取消
    if not order.can_reorder:
        raise HTTPException(status_code=400, detail="已超過取消期限")
    
    order.status = "cancelled"
    db.commit()
    
    return {"message": "訂單已取消", "order_id": order_id}
