from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from datetime import datetime
from app.models.base import Base
import enum

class LogType(enum.Enum):
    ORDER_CREATE = "order_create"  # 建立訂單
    ORDER_UPDATE = "order_update"  # 更新訂單
    ORDER_CANCEL = "order_cancel"  # 取消訂單
    ORDER_REORDER = "order_reorder"  # 重訂
    ORDER_PICKUP = "order_pickup"  # 取餐核銷
    RESTAURANT_CHANGE = "restaurant_change"  # 餐廳更換
    SYSTEM_SETTING = "system_setting"  # 系統設定

class OrderLog(Base):
    __tablename__ = "order_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False, index=True)
    log_type = Column(String(50), nullable=False)
    description = Column(String(1000))  # 操作描述
    old_value = Column(String(500))  # 舊值 (如有變更)
    new_value = Column(String(500))  # 新值 (如有變更)
    
    # 操作者
    operator_id = Column(Integer, nullable=True)  # 操作者 ID (員工或管理員)
    operator_type = Column(String(20))  # 'user' or 'admin'
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<OrderLog {self.order_id}: {self.log_type}>"
