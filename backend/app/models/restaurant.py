from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from backend.app.models.base import Base

class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)  # 餐廳名稱
    contact_person = Column(String(100))  # 聯絡人
    phone = Column(String(20))  # 電話
    address = Column(String(500))  # 地址
    is_active = Column(Boolean, default=True)  # 是否開放訂餐
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Restaurant {self.id}: {self.name}>"
