from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 資料庫 URL (可透過環境變數設定)
DATABASE_URL = "postgresql://mealorder:mealorder123@localhost:5432/meal_ordering"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """取得資料庫連線"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
