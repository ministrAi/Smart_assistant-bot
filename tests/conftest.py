import psycopg2
import pytest
from config import TEST_DB_URL
import config
# from services.database import init_db


@pytest.fixture
def test_db(monkeypatch):
    monkeypatch.setattr(config, "DATABASE_URL", TEST_DB_URL)
    from services.database import init_db  # импорт ПОСЛЕ подмены
    init_db()
    yield  # здесь выполняются тесты

    # Очищаем тестовую БД после тестов
    conn = psycopg2.connect(TEST_DB_URL)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE Communication RESTART IDENTITY CASCADE ")
    conn.commit()
    conn.close()