from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.models.menu_item import MenuItem
from app.models.restaurant import Restaurant
from app.models.daily_setting import DailySetting
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

router = APIRouter()

class MenuItemCreate(BaseModel):
    restaurant_id: int
    meal_date: date
    meal_type: str
    name: str
    price: float
    food_type: str  # meat/vegetarian
    image_url: Optional[str] = None

class MenuItemResponse(BaseModel):
    id: int
    restaurant_name: str
    meal_date: date
    meal_type: str
    name: str
    price: float
    food_type: str
    image_url: Optional[str]

@router.get("/", response_model=List[MenuItemResponse])
async def get_menu(
    meal_date: Optional[date] = None,
    food_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """取得菜單"""
    if not meal_date:
        meal_date = date.today()
    
    query = db.query(MenuItem).join(Restaurant).filter(
        MenuItem.meal_date == meal_date,
        MenuItem.is_available == True,
        Restaurant.is_active == True
    )
    
    if food_type:
        query = query.filter(MenuItem.food_type == food_type)
    
    results = query.all()
    
    return [{
        "id": item.id,
        "restaurant_name": restaurant.name,
        "meal_date": item.meal_date,
        "meal_type": item.meal_type,
        "name": item.name,
        "price": item.price,
        "food_type": item.food_type,
        "image_url": item.image_url
    } for item, restaurant in results]

@router.post("/ocr", summary="OCR 辨識菜單圖片")
async def ocr_menu_image(
    restaurant_id: int,
    meal_date: date,
    file: UploadFile = File(...)
):
    """上傳菜單圖片並用 LLM OCR 辨識"""
    # TODO: 整合 Ollama LLM 進行 OCR
    # 目前先回傳假資料
    return {
        "status": "success",
        "message": "圖片已接收，OCR 辨識中...",
        "raw_text": "等待 LLM 處理",
        "suggested_items": []
    }
