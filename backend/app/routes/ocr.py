"""
OCR 處理 API
提供圖片上傳與辨識功能
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
import os
import uuid
import shutil
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.ocr_service import OCRService, ocr_service
from backend.app.services.db_service import MenuItemService, RestaurantService
from backend.app.models.menu_item import MenuItem
from backend.app.models.restaurant import Restaurant

router = APIRouter()
security = HTTPBearer()

# 上傳目錄
UPLOAD_DIR = "/app/uploads"
MENU_UPLOAD_DIR = os.path.join(UPLOAD_DIR, "menus")

# 確保目錄存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(MENU_UPLOAD_DIR, exist_ok=True)

@router.get("/health")
async def ocr_health_check():
    """檢查 OCR 服務狀態"""
    ollama_available = ocr_service.health_check()
    models = ocr_service.list_models() if ollama_available else []
    
    return {
        "status": "ok" if ollama_available else "error",
        "ollama_available": ollama_available,
        "available_models": models,
        "current_model": ocr_service.model
    }

@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    restaurant_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    上傳菜單圖片並進行 OCR 辨識
    
    Args:
        file: 圖片檔案
        restaurant_id: 餐廳 ID
    
    Returns:
        OCR 辨識結果與菜單項目
    """
    # 驗證餐廳是否存在
    restaurant = RestaurantService.get_by_id(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="餐廳不存在")
    
    # 儲存上傳的圖片
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    file_uuid = str(uuid.uuid4())
    filename = f"{file_uuid}{file_ext}"
    file_path = os.path.join(MENU_UPLOAD_DIR, filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"檔案儲存失敗：{str(e)}")
    
    # 進行 OCR 辨識
    result = ocr_service.recognize_menu(file_path)
    
    if not result:
        raise HTTPException(status_code=500, detail="OCR 辨識失敗")
    
    # 如果辨識成功，自動建立菜單項目
    if result["success"] and result["items"]:
        created_items = []
        for item_data in result["items"]:
            try:
                menu_item = MenuItemService.create(
                    db=db,
                    restaurant_id=restaurant_id,
                    name=item_data["name"],
                    price=item_data["price"],
                    food_type=item_data.get("food_type", "meat"),
                    image_url=f"/uploads/menus/{filename}",
                    ocr_raw_text=result["raw_text"]
                )
                created_items.append({
                    "id": menu_item.id,
                    "name": menu_item.name,
                    "price": menu_item.price,
                    "food_type": menu_item.food_type
                })
            except Exception as e:
                print(f"建立菜單項目失敗 {item_data}: {e}")
        
        return {
            "success": True,
            "message": f"成功辨識並建立 {len(created_items)} 個菜單項目",
            "file_url": f"/uploads/menus/{filename}",
            "items": created_items,
            "processing_time": result["processing_time"]
        }
    
    # 如果辨識失敗，返回原始文字供管理員手動處理
    else:
        return {
            "success": False,
            "message": "OCR 辨識完成，但無法自動解析，請手動輸入",
            "file_url": f"/uploads/menus/{filename}",
            "raw_text": result["raw_text"],
            "error": result.get("error"),
            "processing_time": result["processing_time"]
        }

@router.post("/recognize")
async def recognize_text(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    通用 OCR 文字辨識
    
    Args:
        file: 圖片檔案
        prompt: 自訂提示詞
    
    Returns:
        辨識到的文字
    """
    # 儲存上傳的圖片
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    file_uuid = str(uuid.uuid4())
    filename = f"temp_{file_uuid}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"檔案儲存失敗：{str(e)}")
    
    # 進行 OCR 辨識
    result = ocr_service.recognize(file_path, prompt)
    
    if not result:
        # 刪除失敗的檔案
        try:
            os.remove(file_path)
        except:
            pass
        
        raise HTTPException(status_code=500, detail="OCR 辨識失敗")
    
    return {
        "success": True,
        "text": result.text,
        "confidence": result.confidence,
        "processing_time": result.processing_time
    }

@router.post("/leave-form")
async def recognize_leave_form(
    file: UploadFile = File(...),
    employee_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    辨識休假表勾選
    
    Args:
        file: 休假表圖片
        employee_id: 員工編號
    
    Returns:
        休假日期與類型
    """
    # 儲存上傳的圖片
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    file_uuid = str(uuid.uuid4())
    filename = f"leave_{file_uuid}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"檔案儲存失敗：{str(e)}")
    
    # 進行 OCR 辨識
    result = ocr_service.recognize_leave_form(file_path, employee_id)
    
    if not result:
        raise HTTPException(status_code=500, detail="OCR 辨識失敗")
    
    return {
        "success": result["success"],
        "leave_dates": result.get("leave_dates", []),
        "leave_type": result.get("leave_type", ""),
        "notes": result.get("notes", ""),
        "file_url": f"/uploads/{filename}",
        "processing_time": result["processing_time"]
    }

@router.get("/models")
async def list_models():
    """列出已安裝的模型"""
    models = ocr_service.list_models()
    return {
        "models": models,
        "current": ocr_service.model
    }

@router.post("/models/pull")
async def pull_model(
    model_name: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    """
    下載模型
    
    Args:
        model_name: 模型名稱 (例如：llama3)
    """
    # 在背景任務中下載模型
    def download_task():
        return ocr_service.pull_model(model_name)
    
    background_tasks.add_task(download_task)
    
    return {
        "success": True,
        "message": f"開始下載模型 {model_name}",
        "model_name": model_name
    }

@router.delete("/uploads/{filename}")
async def delete_upload(
    filename: str,
    db: Session = Depends(get_db)
):
    """
    刪除上傳的圖片
    
    Args:
        filename: 檔案名稱
    """
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="檔案不存在")
    
    try:
        os.remove(file_path)
        return {
            "success": True,
            "message": f"已刪除 {filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除失敗：{str(e)}")
