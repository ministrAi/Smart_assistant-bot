import psycopg2
import pytest

from config import TEST_DB_URL
from services.database import init_db

@pytest.fixture
def test_db(monkeypatch):
    # test_db_dir = tmp_path / "data" # Создаем путь
    # test_db_dir.mkdir() # Физически создаем пустую папку
    # test_db_path = test_db_dir / "test_history.db" # Определяем путь к тестовой БД
    # Подменяем настоящую БД на тестовую
    monkeypatch.setattr("config.DATABASE_URL", str(TEST_DB_URL))
    init_db()

    yield # Возвращаем путь в тест

    conn = psycopg2.connect(TEST_DB_URL)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE Communication")
    conn.commit()
    conn.close()