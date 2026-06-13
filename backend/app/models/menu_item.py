from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Date, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, date
from app.models.base import Base
import enum

class MealType(enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"

class FoodType(enum.Enum):
    MEAT = "meat"  # 葷食
    VEGETARIAN = "vegetarian"  # 素食

class MenuItem(Base):
    __tablename__ = "menu_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False)
    meal_date = Column(Date, nullable=False, index=True)  # 餐點日期
    meal_type = Column(String(20), default='lunch')  # 餐別 (lunch/dinner)
    name = Column(String(300), nullable=False)  # 菜名
    price = Column(Float, nullable=False)  # 價格
    food_type = Column(String(20), nullable=False)  # meat/vegetarian
    image_url = Column(String(500))  # 圖片 URL
    ocr_raw_text = Column(String(1000))  # OCR 原始辨識文字
    is_available = Column(Boolean, default=True)  # 是否可訂
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        # 確保同一餐廳同一日期同一餐別不重複
        {'unique_constraints': [restaurant_id, meal_date, meal_type, name]}
    )
    
    def __repr__(self):
        return f"<MenuItem {self.id}: {self.name} @ {self.meal_date}>"
