import psycopg2
import config
import logging
logger = logging.getLogger(__name__)


# Создаем таблицу
def init_db():
    conn = psycopg2.connect(config.DATABASE_URL)
    cursor = conn.cursor()

    # Создаем таблицу для ОБЩЕЙ памяти если ее нет
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Communication (
        id SERIAL PRIMARY KEY ,
        user_id INTEGER,
        text TEXT,
        timestamp TEXT,
        role TEXT,
        is_active INTEGER DEFAULT 1
    )
    """)


    # создаем таблицу для ДОЛГОСРОЧНОЙ памяти
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS LongTermMemory (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        fact TEXT,
        importance TEXT,
        is_active INTEGER DEFAULT 1,
        UNIQUE(user_id, fact) -- не позволяет одному и тому же пользователю иметь два одинаковых факта
    )
    """)


    #  создаем таблицу для РАБОЧЕЙ памяти
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS WorkingMemory (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        current_task TEXT,
        started_at TEXT,
        is_active INTEGER DEFAULT 1,
        UNIQUE(user_id)
    )
    """)
    conn.commit()
    conn.close()


    # Создаем таблицу для РЕФЛЕКСИВНОЙ памяти
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ReflectionMemory (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    reflection TEXT,
    timestamp TEXT,
    is_active INTEGER DEFAULT 1,
    """)
    conn.commit()
    conn.close()


# сохраняем соединение с БД в одну функцию
def get_connection():
    try:
        conn = psycopg2.connect(config.DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return None
