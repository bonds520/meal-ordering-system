"""
資料庫初始化腳本
建立所有資料表與初始資料
"""

import sys
import os

# 加入專案根目錄到 Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from datetime import datetime, date, time

from backend.app.database import Base, get_db, DATABASE_URL
from backend.app.models.user import User, UserStatus
from backend.app.models.restaurant import Restaurant
from backend.app.models.menu_item import MenuItem
from backend.app.models.order import Order
from backend.app.models.daily_setting import DailySetting
from backend.app.models.leave_record import LeaveRecord
from backend.app.models.order_log import OrderLog

# 建立資料庫引擎
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """建立所有資料表"""
    print("📋 正在建立資料表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 資料表建立完成")

def seed_initial_data():
    """初始化基本資料"""
    print("\n🌱 正在初始化基本資料...")
    
    db = SessionLocal()
    
    try:
        # 建立預設餐廳
        restaurants = [
            Restaurant(
                name="三鮮水餃",
                address="台北市信義區信義路五段 100 號",
                contact="02-1234-5678",
                is_active=True
            ),
            Restaurant(
                name="素食小館",
                address="台北市信義區信義路五段 200 號",
                contact="02-8765-4321",
                is_active=True
            ),
            Restaurant(
                name="日式便當",
                address="台北市信義區信義路五段 300 號",
                contact="02-1111-2222",
                is_active=True
            ),
            Restaurant(
                name="中式快餐",
                address="台北市信義區信義路五段 400 號",
                contact="02-3333-4444",
                is_active=True
            ),
            Restaurant(
                name="西式餐廳",
                address="台北市信義區信義路五段 500 號",
                contact="02-5555-6666",
                is_active=True
            )
        ]
        
        for restaurant in restaurants:
            db.add(restaurant)
        db.commit()
        print(f"✅ 已建立 {len(restaurants)} 家餐廳")
        
        # 建立今日菜單
        today = date.today()
        menu_items = [
            MenuItem(
                restaurant_id=1,
                meal_date=today,
                meal_type="lunch",
                name="三鮮水餃",
                price=150.0,
                food_type="meat",
                is_available=True
            ),
            MenuItem(
                restaurant_id=1,
                meal_date=today,
                meal_type="lunch",
                name="韭菜水餃",
                price=120.0,
                food_type="meat",
                is_available=True
            ),
            MenuItem(
                restaurant_id=2,
                meal_date=today,
                meal_type="lunch",
                name="素炒青菜",
                price=80.0,
                food_type="vegetarian",
                is_available=True
            ),
            MenuItem(
                restaurant_id=2,
                meal_date=today,
                meal_type="lunch",
                name="素滷肉飯",
                price=100.0,
                food_type="vegetarian",
                is_available=True
            ),
            MenuItem(
                restaurant_id=3,
                meal_date=today,
                meal_type="lunch",
                name="鰻魚飯",
                price=200.0,
                food_type="meat",
                is_available=True
            ),
            MenuItem(
                restaurant_id=3,
                meal_date=today,
                meal_type="lunch",
                name="鮭魚便當",
                price=180.0,
                food_type="meat",
                is_available=True
            ),
            MenuItem(
                restaurant_id=4,
                meal_date=today,
                meal_type="lunch",
                name="宮保雞丁飯",
                price=120.0,
                food_type="meat",
                is_available=True
            ),
            MenuItem(
                restaurant_id=4,
                meal_date=today,
                meal_type="lunch",
                name="麻婆豆腐飯",
                price=100.0,
                food_type="meat",
                is_available=True
            ),
            MenuItem(
                restaurant_id=5,
                meal_date=today,
                meal_type="lunch",
                name="燻雞三明治",
                price=150.0,
                food_type="meat",
                is_available=True
            ),
            MenuItem(
                restaurant_id=5,
                meal_date=today,
                meal_type="lunch",
                name="凱撒沙拉",
                price=130.0,
                food_type="meat",
                is_available=True
            )
        ]
        
        for menu_item in menu_items:
            db.add(menu_item)
        db.commit()
        print(f"✅ 已建立 {len(menu_items)} 個菜單項目")
        
        # 建立今日設定
        daily_setting = DailySetting(
            meal_date=today,
            available_restaurants=[1, 2, 3, 4, 5],
            subsidy_amount=150.0,
            order_start_time=time(8, 0),
            order_end_time=time(11, 30),
            pickup_start_time=time(11, 30),
            pickup_end_time=time(13, 0),
            is_active=True
        )
        db.add(daily_setting)
        db.commit()
        print("✅ 已建立今日設定")
        
        print("\n🎉 初始資料建立完成！")
        print(f"📅 今日菜單：{len(menu_items)} 道菜色")
        print(f"🏪 開放餐廳：{len(restaurants)} 家")
        print(f"💰 今日補助：{daily_setting.subsidy_amount} 元")
        print(f"⏰ 訂餐截止：{daily_setting.order_end_time.strftime('%H:%M')}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 初始化資料失敗：{e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def check_database_connection():
    """檢查資料庫連線"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("✅ 資料庫連線成功")
        return True
    except OperationalError as e:
        print(f"❌ 資料庫連線失敗：{e}")
        print("\n請確認以下設定:")
        print(f"• 資料庫 URL: {DATABASE_URL}")
        print("• PostgreSQL 服務已啟動")
        print("• 資料庫已建立")
        return False

def main():
    """主函數"""
    print("=" * 60)
    print("🚀 訂餐系統 - 資料庫初始化")
    print("=" * 60)
    
    # 檢查連線
    if not check_database_connection():
        sys.exit(1)
    
    # 建立資料表
    create_tables()
    
    # 初始化資料
    seed_initial_data()
    
    print("\n" + "=" * 60)
    print("✅ 資料庫初始化完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
