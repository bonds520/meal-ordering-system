FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements 並安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式
COPY . .

# 設定環境變數
ENV PYTHONPATH=/app
ENV DATABASE_URL=postgresql://mealorder:password@db:5432/meal_ordering

# 暴露端口
EXPOSE 8000

# 啟動應用程式
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
