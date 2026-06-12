"""
資料庫服務模組
提供所有資料庫操作的 Service 層
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time
from sqlalchemy import and_, or_, func

from backend.app.models.user import User, UserStatus
from backend.app.models.restaurant import Restaurant
from backend.app.models.menu_item import MenuItem, FoodType
from backend.app.models.order import Order, OrderStatus
from backend.app.models.daily_setting import DailySetting
from backend.app.models.leave_record import LeaveRecord
from backend.app.models.order_log import OrderLog


class UserService:
    """用戶服務"""
    
    @staticmethod
    def get_by_line_user_id(db: Session, line_user_id: str) -> Optional[User]:
        """根據 LINE User ID 查詢用戶"""
        return db.query(User).filter(User.line_user_id == line_user_id).first()
    
    @staticmethod
    def get_by_employee_id(db: Session, employee_id: str) -> Optional[User]:
        """根據員工編號查詢用戶"""
        return db.query(User).filter(User.employee_id == employee_id).first()
    
    @staticmethod
    def create_or_get(db: Session, line_user_id: str, name: str, employee_id: Optional[str] = None) -> User:
        """建立或取得用戶"""
        user = db.query(User).filter(User.line_user_id == line_user_id).first()
        
        if not user:
            # 建立新用戶
            user = User(
                line_user_id=line_user_id,
                name=name,
                employee_id=employee_id or line_user_id,  # 若無員工編號，先用 LINE ID
                status=UserStatus.ACTIVE
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return user
    
    @staticmethod
    def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
        """更新用戶資料"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
        return user
    
    @staticmethod
    def get_all_users(db: Session, status: Optional[UserStatus] = None) -> List[User]:
        """取得所有用戶"""
        query = db.query(User)
        if status:
            query = query.filter(User.status == status)
        return query.all()


class RestaurantService:
    """餐廳服務"""
    
    @staticmethod
    def get_all(db: Session) -> List[Restaurant]:
        """取得所有餐廳"""
        return db.query(Restaurant).filter(Restaurant.is_active == True).all()
    
    @staticmethod
    def get_by_id(db: Session, restaurant_id: int) -> Optional[Restaurant]:
        """根據 ID 查詢餐廳"""
        return db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    
    @staticmethod
    def create(db: Session, name: str, address: str, contact: Optional[str] = None) -> Restaurant:
        """建立餐廳"""
        restaurant = Restaurant(
            name=name,
            address=address,
            contact=contact,
            is_active=True
        )
        db.add(restaurant)
        db.commit()
        db.refresh(restaurant)
        return restaurant


class MenuItemService:
    """菜單項目服務"""
    
    @staticmethod
    def get_today_menu(db: Session, meal_date: Optional[date] = None) -> List[MenuItem]:
        """取得今日菜單"""
        if not meal_date:
            meal_date = date.today()
        
        return db.query(MenuItem).filter(
            MenuItem.meal_date == meal_date,
            MenuItem.is_available == True
        ).all()
    
    @staticmethod
    def get_by_restaurant(db: Session, restaurant_id: int, meal_date: Optional[date] = None) -> List[MenuItem]:
        """取得特定餐廳的菜單"""
        if not meal_date:
            meal_date = date.today()
        
        return db.query(MenuItem).filter(
            MenuItem.restaurant_id == restaurant_id,
            MenuItem.meal_date == meal_date,
            MenuItem.is_available == True
        ).all()
    
    @staticmethod
    def create(db: Session, restaurant_id: int, name: str, price: float, food_type: str, 
               meal_date: Optional[date] = None, meal_type: str = "lunch", 
               image_url: Optional[str] = None, ocr_raw_text: Optional[str] = None) -> MenuItem:
        """建立菜單項目"""
        if not meal_date:
            meal_date = date.today()
        
        menu_item = MenuItem(
            restaurant_id=restaurant_id,
            meal_date=meal_date,
            meal_type=meal_type,
            name=name,
            price=price,
            food_type=food_type,
            image_url=image_url,
            ocr_raw_text=ocr_raw_text,
            is_available=True
        )
        db.add(menu_item)
        db.commit()
        db.refresh(menu_item)
        return menu_item
    
    @staticmethod
    def create_batch(db: Session, restaurant_id: int, items: List[Dict[str, Any]], 
                    meal_date: Optional[date] = None) -> List[MenuItem]:
        """批量建立菜單項目"""
        created_items = []
        for item_data in items:
            menu_item = MenuItemService.create(
                db=db,
                restaurant_id=restaurant_id,
                name=item_data['name'],
                price=item_data['price'],
                food_type=item_data.get('food_type', 'meat'),
                meal_date=meal_date,
                image_url=item_data.get('image_url'),
                ocr_raw_text=item_data.get('ocr_raw_text')
            )
            created_items.append(menu_item)
        return created_items
    
    @staticmethod
    def get_by_name(db: Session, name: str, meal_date: Optional[date] = None) -> Optional[MenuItem]:
        """根據菜名查詢"""
        if not meal_date:
            meal_date = date.today()
        
        return db.query(MenuItem).filter(
            MenuItem.name == name,
            MenuItem.meal_date == meal_date,
            MenuItem.is_available == True
        ).first()


class OrderService:
    """訂單服務"""
    
    @staticmethod
    def create_order(db: Session, user_id: int, menu_item_id: int, 
                    subsidy_amount: float, meal_date: Optional[date] = None) -> Optional[Order]:
        """建立訂單"""
        # 檢查今日是否已有訂單
        if not meal_date:
            meal_date = date.today()
        
        existing_order = db.query(Order).filter(
            Order.user_id == user_id,
            Order.meal_date == meal_date,
            Order.status != OrderStatus.CANCELLED.value
        ).first()
        
        if existing_order:
            return None  # 今日已有訂單
        
        # 取得菜單項目資訊
        menu_item = db.query(MenuItem).filter(MenuItem.id == menu_item_id).first()
        if not menu_item:
            return None
        
        # 計算自付金額
        price = menu_item.price
        self_pay_amount = max(0, price - subsidy_amount)
        
        # 建立訂單
        order = Order(
            user_id=user_id,
            meal_date=meal_date,
            restaurant_id=menu_item.restaurant_id,
            menu_item_id=menu_item_id,
            price=price,
            subsidy_amount=subsidy_amount,
            self_pay_amount=self_pay_amount,
            status=OrderStatus.PENDING.value,
            can_reorder=True
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        # 記錄日誌
        OrderLogService.create(db, user_id, f"建立訂單：{menu_item.name}", "order_created")
        
        return order
    
    @staticmethod
    def get_today_order(db: Session, user_id: int, meal_date: Optional[date] = None) -> Optional[Order]:
        """取得今日訂單"""
        if not meal_date:
            meal_date = date.today()
        
        return db.query(Order).filter(
            Order.user_id == user_id,
            Order.meal_date == meal_date,
            Order.status != OrderStatus.CANCELLED.value
        ).first()
    
    @staticmethod
    def get_user_orders(db: Session, user_id: int, limit: int = 10) -> List[Order]:
        """取得用戶訂單歷史"""
        return db.query(Order).filter(
            Order.user_id == user_id
        ).order_by(Order.meal_date.desc(), Order.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def cancel_order(db: Session, order_id: int, user_id: int) -> bool:
        """取消訂單"""
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == user_id
        ).first()
        
        if not order:
            return False
        
        if order.status == OrderStatus.CANCELLED.value:
            return False  # 已經取消
        
        # 檢查是否超過截止時間
        daily_setting = DailySettingService.get_by_date(db, order.meal_date)
        if daily_setting and daily_setting.order_end_time:
            now = datetime.utcnow().time()
            if now > daily_setting.order_end_time:
                return False  # 已超過截止時間，無法取消
        
        order.status = OrderStatus.CANCELLED.value
        order.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(order)
        
        # 記錄日誌
        OrderLogService.create(db, user_id, f"取消訂單：{order.id}", "order_cancelled")
        
        return True
    
    @staticmethod
    def confirm_order(db: Session, order_id: int) -> bool:
        """確認訂單 (管理員用)"""
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order or order.status != OrderStatus.PENDING.value:
            return False
        
        order.status = OrderStatus.CONFIRMED.value
        order.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(order)
        
        return True
    
    @staticmethod
    def get_all_today_orders(db: Session, meal_date: Optional[date] = None) -> List[Order]:
        """取得今日所有訂單 (管理員用)"""
        if not meal_date:
            meal_date = date.today()
        
        return db.query(Order).filter(
            Order.meal_date == meal_date,
            Order.status != OrderStatus.CANCELLED.value
        ).all()
    
    @staticmethod
    def get_order_summary(db: Session, meal_date: Optional[date] = None) -> Dict[str, Any]:
        """取得訂單統計 (管理員用)"""
        if not meal_date:
            meal_date = date.today()
        
        orders = db.query(Order).filter(
            Order.meal_date == meal_date,
            Order.status != OrderStatus.CANCELLED.value
        ).all()
        
        total_orders = len(orders)
        total_amount = sum(order.price for order in orders)
        total_subsidy = sum(order.subsidy_amount for order in orders)
        total_self_pay = sum(order.self_pay_amount for order in orders)
        
        # 按餐廳統計
        restaurant_stats = {}
        for order in orders:
            restaurant_name = order.restaurant.name if order.restaurant else "Unknown"
            if restaurant_name not in restaurant_stats:
                restaurant_stats[restaurant_name] = {
                    "count": 0,
                    "amount": 0
                }
            restaurant_stats[restaurant_name]["count"] += 1
            restaurant_stats[restaurant_name]["amount"] += order.price
        
        return {
            "meal_date": meal_date,
            "total_orders": total_orders,
            "total_amount": total_amount,
            "total_subsidy": total_subsidy,
            "total_self_pay": total_self_pay,
            "restaurant_stats": restaurant_stats
        }


class DailySettingService:
    """每日設定服務"""
    
    @staticmethod
    def get_by_date(db: Session, meal_date: date) -> Optional[DailySetting]:
        """根據日期查詢設定"""
        return db.query(DailySetting).filter(
            DailySetting.meal_date == meal_date
        ).first()
    
    @staticmethod
    def get_today_setting(db: Session) -> Optional[DailySetting]:
        """取得今日設定"""
        return DailySettingService.get_by_date(db, date.today())
    
    @staticmethod
    def create_or_update(db: Session, meal_date: date, **kwargs) -> DailySetting:
        """建立或更新每日設定"""
        setting = db.query(DailySetting).filter(DailySetting.meal_date == meal_date).first()
        
        if not setting:
            setting = DailySetting(meal_date=meal_date)
            db.add(setting)
        
        for key, value in kwargs.items():
            if hasattr(setting, key):
                setattr(setting, key, value)
        
        setting.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(setting)
        
        return setting
    
    @staticmethod
    def initialize_today(db: Session, subsidy_amount: float = 150.0, 
                        order_end_time: time = time(11, 30)) -> DailySetting:
        """初始化今日設定"""
        return DailySettingService.create_or_update(
            db=db,
            meal_date=date.today(),
            subsidy_amount=subsidy_amount,
            order_end_time=order_end_time,
            is_active=True
        )


class LeaveRecordService:
    """休假記錄服務"""
    
    @staticmethod
    def create(db: Session, user_id: int, leave_date: date, leave_type: str, 
              approved: bool = False, notes: Optional[str] = None) -> LeaveRecord:
        """建立休假記錄"""
        leave_record = LeaveRecord(
            user_id=user_id,
            leave_date=leave_date,
            leave_type=leave_type,
            approved=approved,
            notes=notes
        )
        db.add(leave_record)
        db.commit()
        db.refresh(leave_record)
        return leave_record
    
    @staticmethod
    def get_user_leaves(db: Session, user_id: int, start_date: date, end_date: date) -> List[LeaveRecord]:
        """取得用戶休假記錄"""
        return db.query(LeaveRecord).filter(
            LeaveRecord.user_id == user_id,
            LeaveRecord.leave_date >= start_date,
            LeaveRecord.leave_date <= end_date,
            LeaveRecord.approved == True
        ).all()
    
    @staticmethod
    def is_user_on_leave(db: Session, user_id: int, leave_date: date) -> bool:
        """檢查用戶當日是否休假"""
        leave_record = db.query(LeaveRecord).filter(
            LeaveRecord.user_id == user_id,
            LeaveRecord.leave_date == leave_date,
            LeaveRecord.approved == True
        ).first()
        
        return leave_record is not None


class OrderLogService:
    """訂單日誌服務"""
    
    @staticmethod
    def create(db: Session, user_id: int, action: str, log_type: str, 
              order_id: Optional[int] = None, details: Optional[str] = None) -> OrderLog:
        """建立日誌記錄"""
        log = OrderLog(
            user_id=user_id,
            order_id=order_id,
            action=action,
            log_type=log_type,
            details=details
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def get_user_logs(db: Session, user_id: int, limit: int = 50) -> List[OrderLog]:
        """取得用戶日誌"""
        return db.query(OrderLog).filter(
            OrderLog.user_id == user_id
        ).order_by(OrderLog.created_at.desc()).limit(limit).all()
