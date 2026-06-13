from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.models.base import Base
import enum

class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    VACATION = "vacation"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)  # 員工編號
    name = Column(String(100), nullable=False)  # 姓名
    department = Column(String(100))  # 部門
    sso_id = Column(String(100), unique=True)  # SSO ID (LINE UserID)
    line_user_id = Column(String(100), unique=True)  # LINE UserID
    phone = Column(String(20))  # 手機
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User {self.employee_id}: {self.name}>"
