from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey
from datetime import datetime, date
from backend.app.models.base import Base
import enum

class LeaveType(enum.Enum):
    ANNUAL = "annual"  # 年假
    SICK = "sick"  # 病假
    PERSONAL = "personal"  # 事假
    HOLIDAY = "holiday"  # 國定假日
    OTHER = "other"  # 其他

class LeaveRecord(Base):
    __tablename__ = "leave_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    leave_date = Column(Date, nullable=False, index=True)
    leave_type = Column(String(20), default=LeaveType.OTHER.value)
    
    # OCR 相關
    ocr_confidence = Column(Float)  # OCR 辨識置信度
    needs_review = Column(Boolean, default=True)  # 是否需要人工確認
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        # 確保同一員工同一日期不重複
        {'unique_constraints': [user_id, leave_date]}
    )
    
    def __repr__(self):
        return f"<LeaveRecord User {self.user_id} - {self.leave_date}>"
