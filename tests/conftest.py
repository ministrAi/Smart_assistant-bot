import psycopg2
import pytest
from config import TEST_DB_URL
import config
from services.database.base import init_db


def clear_test_database():
    """Полная очистка тестовых таблиц"""
    conn = psycopg2.connect(TEST_DB_URL)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            TRUNCATE TABLE Communication, 
                          LongTermMemory, 
                          WorkingMemory, 
                          ReflectionMemory 
            RESTART IDENTITY CASCADE;
        """)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"⚠️ Ошибка при очистке тестовой БД: {e}")
    finally:
        conn.close()


@pytest.fixture(scope="function")
def test_db(monkeypatch):
    """
    Основная фикстура для тестов.
    - Подменяет PRODUCTION БД на тестовую
    - Инициализирует структуру БД
    - Полностью очищает таблицы ПЕРЕД каждым тестом
    """
    # 1. Подменяем DATABASE_URL на тестовую базу
    monkeypatch.setattr(config, "DATABASE_URL", TEST_DB_URL)

    # 2. Инициализируем таблицы (если нужно)
    init_db()

    # 3. Очищаем базу ПЕРЕД тестом
    clear_test_database()

    yield  # ← Здесь выполняются все тесты, которые используют эту фикстуру

    # 4. Опционально: очищаем после теста (на всякий случай)
    clear_test_database()