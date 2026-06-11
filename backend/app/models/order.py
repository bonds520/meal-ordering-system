from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Date, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, date
from backend.app.models.base import Base
import enum

class OrderStatus(enum.Enum):
    PENDING = "pending"  # 待確認
    CONFIRMED = "confirmed"  # 已確認
    CANCELLED = "cancelled"  # 已取消
    PICKED_UP = "picked_up"  # 已取餐
    REPLACED = "replaced"  # 已更換餐廳

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    meal_date = Column(Date, nullable=False, index=True)  # 用餐日期
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False)
    menu_item_id = Column(Integer, ForeignKey('menu_items.id'), nullable=False)
    
    # 金額相關
    price = Column(Float, nullable=False)  # 菜色價格
    subsidy_amount = Column(Float, nullable=False)  # 補助金額
    self_pay_amount = Column(Float, nullable=False)  # 自付金額
    
    # 狀態
    status = Column(String(20), default=OrderStatus.PENDING.value)
    qr_code = Column(String(500))  # 取餐 QR Code
    qr_code_hash = Column(String(100))  # QR Code 驗證用 hash
    
    # 反悔重訂
    can_reorder = Column(Boolean, default=True)  # 是否可重訂
    reorder_count = Column(Integer, default=0)  # 已重訂次數
    
    # 備註
    notes = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Order {self.id}: User {self.user_id} - {self.meal_date}>"
