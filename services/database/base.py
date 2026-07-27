import psycopg2
import config
import logging
from psycopg2 import pool
logger = logging.getLogger(__name__)


# сохраняем соединение с БД в одну функцию
class DatabaseManager:
    _pool = None

    @classmethod
    def init_pool(cls, minconn=1, maxconn=10):
        cls._pool = pool.SimpleConnectionPool(
            minconn, maxconn, config.DATABASE_URL
        )
        logger.info(f"✅ Пул соединений создан (min={minconn}, max={maxconn})")

    @classmethod
    def get_connection(cls):
        return cls._pool.getconn()

    @classmethod
    def put_connection(cls, conn):
        cls._pool.putconn(conn)


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
    # не позволяет одному и тому же пользователю иметь два одинаковых факта
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS LongTermMemory (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        fact TEXT,
        importance TEXT,
        is_active INTEGER DEFAULT 1,
        UNIQUE(user_id, fact) 
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


    # Создаем таблицу для РЕФЛЕКСИВНОЙ памяти
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ReflectionMemory (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    reflection TEXT,
    timestamp TEXT,
    is_active INTEGER DEFAULT 1
    )
    """)
    conn.commit()
    conn.close()


