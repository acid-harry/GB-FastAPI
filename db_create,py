import sqlite3

# Подключение к базе данных
conn = sqlite3.connect('online_store.db')
cursor = conn.cursor()

# Создание таблицы "users"
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        email TEXT,
        password TEXT
    )
''')

# Создание таблицы "products"
cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        description TEXT,
        price REAL
    )
''')

# Создание таблицы "orders"
cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        product_id INTEGER,
        order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
''')

# Закрываем соединение
conn.close()
