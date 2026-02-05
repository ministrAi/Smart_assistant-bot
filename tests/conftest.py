import pytest
from services.database import init_db

@pytest.fixture
def test_db(tmp_path, monkeypatch):
    test_db_dir = tmp_path / "data" # Создаем путь
    test_db_dir.mkdir() # Физически создаем пустую папку
    test_db_path = test_db_dir / "test_history.db" # Определяем путь к тестовой БД
    # Подменяем настоящую БД на тестовую
    monkeypatch.setattr("services.database.DB_PATH", str(test_db_path))
    init_db()

    yield test_db_path # Возвращаем путь в тест

