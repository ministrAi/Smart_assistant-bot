import  sqlite3
from config import DB_PATH


# Создаем таблицу
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Messages (
        id INTEGER,
        user_id INTEGER,
        text TEXT,
        timestamp TEXT
    )
    """)
    # Попытка добавить поле role (если его ещё нет)
    try:
        cursor.execute("""
        ALTER TABLE Messages ADD COLUMN role TEXT
        """)

    except sqlite3.OperationalError:
        # Поле уже существует — пропускаем
        pass

    conn.commit()
    conn.close()

# Вставляем данные в таблицу
def save_message(user_id, role, text, timestamp):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO Messages (user_id, role, text, timestamp)
    VALUES (?, ?, ?, ?)
    """, (user_id, role, text, timestamp))
    conn.commit()
    conn.close()
