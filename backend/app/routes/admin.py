from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from backend.app.models.base import get_db
from backend.app.models.restaurant import Restaurant
from backend.app.models.daily_setting import DailySetting
from backend.app.models.leave_record import LeaveRecord
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import pandas as pd
import io

router = APIRouter()

class RestaurantCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class DailySettingCreate(BaseModel):
    meal_date: date
    available_restaurants: List[int]
    subsidy_amount: float = 150.0
    order_end_time: Optional[str] = "16:00"

@router.get("/restaurants", response_model=List[Restaurant])
async def get_restaurants(db: Session = Depends(get_db)):
    """取得所有餐廳"""
    return db.query(Restaurant).all()

@router.post("/restaurants", response_model=Restaurant)
async def create_restaurant(restaurant_data: RestaurantCreate, db: Session = Depends(get_db)):
    """新增餐廳"""
    new_restaurant = Restaurant(**restaurant_data.dict())
    db.add(new_restaurant)
    db.commit()
    db.refresh(new_restaurant)
    return new_restaurant

@router.post("/daily-setting", response_model=DailySetting)
async def create_daily_setting(setting_data: DailySettingCreate, db: Session = Depends(get_db)):
    """設定當日訂餐規則"""
    # 檢查是否已存在
    existing = db.query(DailySetting).filter(
        DailySetting.meal_date == setting_data.meal_date
    ).first()
    
    if existing:
        # 更新
        existing.available_restaurants = setting_data.available_restaurants
        existing.subsidy_amount = setting_data.subsidy_amount
        if setting_data.order_end_time:
            from datetime import time
            h, m = map(int, setting_data.order_end_time.split(":"))
            existing.order_end_time = time(h, m)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # 新增
        from datetime import time
        h, m = map(int, setting_data.order_end_time.split(":"))
        new_setting = DailySetting(
            meal_date=setting_data.meal_date,
            available_restaurants=setting_data.available_restaurants,
            subsidy_amount=setting_data.subsidy_amount,
            order_end_time=time(h, m)
        )
        db.add(new_setting)
        db.commit()
        db.refresh(new_setting)
        return new_setting

@router.post("/leave/upload")
async def upload_leave_table(
    file: UploadFile = File(...),
    meal_date: Optional[date] = Form(None),
    db: Session = Depends(get_db)
):
    """上傳休假表 Excel"""
    # 讀取 Excel
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Excel 讀取失敗：{str(e)}")
    
    # TODO: 用 LLM 辨識手動勾選的休假欄位
    # 目前先回傳成功訊息
    return {
        "status": "success",
        "message": f"休假表已接收，共 {len(df)} 筆記錄",
        "needs_review": True,
        "review_url": "/admin/leave/review"
    }

@router.get("/accounting/daily")
async def get_daily_accounting(
    meal_date: date,
    db: Session = Depends(get_db)
):
    """取得當日對帳表"""
    # TODO: 實際計算
    return {
        "meal_date": meal_date,
        "total_orders": 0,
        "total_subsidy": 0.0,
        "total_self_pay": 0.0,
        "by_restaurant": []
    }
