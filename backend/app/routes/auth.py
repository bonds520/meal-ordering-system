from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.models.user import User
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class UserLogin(BaseModel):
    line_user_id: str
    name: Optional[str] = None

class UserResponse(BaseModel):
    employee_id: str
    name: str
    department: Optional[str]
    status: str

@router.post("/login", response_model=UserResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """LINE 登入/註冊"""
    # 查找是否已存在
    user = db.query(User).filter(User.line_user_id == login_data.line_user_id).first()
    
    if user:
        # 更新用戶資料
        if login_data.name:
            user.name = login_data.name
        return user
    else:
        # 新增用戶 (需要管理員後續確認員工編號)
        new_user = User(
            line_user_id=login_data.line_user_id,
            name=login_data.name or "未命名",
            employee_id=f"LINE_{login_data.line_user_id[:8]}",
            department="待確認"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

@router.get("/me", response_model=UserResponse)
async def get_current_user(line_user_id: str, db: Session = Depends(get_db)):
    """取得當前用戶資料"""
    user = db.query(User).filter(User.line_user_id == line_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    return user
