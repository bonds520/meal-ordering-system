# 建立資料表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    sso_id VARCHAR(100) UNIQUE,
    line_user_id VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS restaurants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    address VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS menu_items (
    id SERIAL PRIMARY KEY,
    restaurant_id INTEGER REFERENCES restaurants(id) ON DELETE CASCADE,
    meal_date DATE NOT NULL,
    meal_type VARCHAR(20) DEFAULT 'lunch',
    name VARCHAR(300) NOT NULL,
    price FLOAT NOT NULL,
    food_type VARCHAR(20) NOT NULL,
    image_url VARCHAR(500),
    ocr_raw_text VARCHAR(1000),
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(restaurant_id, meal_date, meal_type, name)
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    meal_date DATE NOT NULL,
    restaurant_id INTEGER REFERENCES restaurants(id) ON DELETE CASCADE,
    menu_item_id INTEGER REFERENCES menu_items(id) ON DELETE CASCADE,
    price FLOAT NOT NULL,
    subsidy_amount FLOAT NOT NULL,
    self_pay_amount FLOAT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    qr_code VARCHAR(500),
    qr_code_hash VARCHAR(100),
    can_reorder BOOLEAN DEFAULT TRUE,
    reorder_count INTEGER DEFAULT 0,
    notes VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_settings (
    id SERIAL PRIMARY KEY,
    meal_date DATE UNIQUE NOT NULL,
    available_restaurants JSONB DEFAULT '[]',
    subsidy_amount FLOAT DEFAULT 150.0,
    order_start_time TIME DEFAULT '08:00:00',
    order_end_time TIME DEFAULT '16:00:00',
    pickup_start_time TIME DEFAULT '11:30:00',
    pickup_end_time TIME DEFAULT '13:00:00',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS leave_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    leave_date DATE NOT NULL,
    leave_type VARCHAR(20) DEFAULT 'other',
    ocr_confidence FLOAT,
    needs_review BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, leave_date)
);

CREATE TABLE IF NOT EXISTS order_logs (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    log_type VARCHAR(50) NOT NULL,
    description VARCHAR(1000),
    old_value VARCHAR(500),
    new_value VARCHAR(500),
    operator_id INTEGER,
    operator_type VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 建立索引
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_meal_date ON orders(meal_date);
CREATE INDEX idx_menu_items_meal_date ON menu_items(meal_date);
CREATE INDEX idx_leave_records_user_date ON leave_records(user_id, leave_date);
CREATE INDEX idx_order_logs_order_id ON order_logs(order_id);

-- 插入預設資料
INSERT INTO restaurants (name, contact_person, phone) VALUES 
    ('美味中式料理', '王經理', '0912-345-678'),
    ('素食小屋', '李小姐', '0918-765-432')
ON CONFLICT DO NOTHING;

INSERT INTO daily_settings (meal_date, available_restaurants, subsidy_amount) VALUES 
    (CURRENT_DATE, '[1, 2]', 150.0)
ON CONFLICT (meal_date) DO NOTHING;
