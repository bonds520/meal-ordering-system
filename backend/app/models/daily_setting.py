from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Date, Time
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, time
from app.models.base import Base

class DailySetting(Base):
    __tablename__ = "daily_settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    meal_date = Column(Date, unique=True, nullable=False, index=True)  # 用餐日期
    
    # 開放餐廳 (JSONB 儲存餐廳 ID 列表)
    available_restaurants = Column(JSONB, default=list)  # [restaurant_id1, restaurant_id2, ...]
    
    # 補助金額
    subsidy_amount = Column(Float, default=150.0)  # 每人補助額度
    
    # 時間設定
    order_start_time = Column(Time, default=time(8, 0))  # 訂餐開始時間
    order_end_time = Column(Time, default=time(16, 0))   # 訂餐截止時間
    pickup_start_time = Column(Time, default=time(11, 30))  # 取餐開始時間
    pickup_end_time = Column(Time, default=time(13, 0))    # 取餐結束時間
    
    # 狀態
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<DailySetting {self.meal_date}: 補助 {self.subsidy_amount}>"
