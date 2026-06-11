from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.app.models.base import engine, Base
from backend.app.routes import auth, menu, order, admin, line

# 建立資料庫表格
def create_tables():
    Base.metadata.create_all(bind=engine)

# 初始化 FastAPI 應用
app = FastAPI(
    title="公司員工訂餐系統",
    description="支援 LINE 點餐、本地 LLM OCR、休假表自動解析",
    version="1.0.0"
)

# CORS 設定 (允許前端連線)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境應改為特定 domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載靜態文件 (前端)
if os.path.exists("frontend/web/dist"):
    app.mount("/static", StaticFiles(directory="frontend/web/dist"), name="static")

# 註冊路由
app.include_router(auth.router, prefix="/api/auth", tags=["認證"])
app.include_router(menu.router, prefix="/api/menu", tags=["菜單"])
app.include_router(order.router, prefix="/api/order", tags=["訂單"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理"])
app.include_router(line.router, prefix="/api/line", tags=["LINE"])

@app.on_event("startup")
async def startup_event():
    """啟動時建立資料庫表格"""
    create_tables()
    print("✅ 資料庫表格已建立")

@app.get("/")
async def root():
    return {
        "message": "公司員工訂餐系統 API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "系統運作正常"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
