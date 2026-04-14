import pytest
import sqlite3
import os
from config import TEST_DB_URL
import config


@pytest.fixture
def test_db(monkeypatch):
    monkeypatch.setattr(config, "DATABASE_URL", TEST_DB_URL)
    from services.database import init_db  # импорт ПОСЛЕ подмены
    init_db()
    yield  # здесь выполняются тесты

    # Очищаем тестовую БД после тестов
    db_path = TEST_DB_URL.replace("sqlite:///", "")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Communication")
        conn.commit()
        conn.close()
