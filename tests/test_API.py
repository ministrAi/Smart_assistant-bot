
from fastapi.testclient import TestClient
from api.main1 import app
from services.database import save_message, get_conversation_history

# Создаем клиента. Он будет делать запросы к приложению в памяти, не запуская реальный сервер в терминале.
client = TestClient(app)

# Тестируем получение смс
def test_get_user_history(test_db):
    user_id = 111
    save_message(user_id, "user", "Test1", "2026-02-02T10:01:00")
    save_message(user_id, "assistant", "Test2", "2026-02-02T10:02:00")

    response = client.get(f"/users/{user_id}/messages")

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == 111
    assert data["messages"][0]["role"] == 'user'
    assert data["messages"][1]["role"] == 'assistant'
    assert data["messages"][1]["content"] == 'Test2'
    assert data["count"] == 2


# Тестируем отсутствие пользователя
def test_get_user_history_not_found(test_db):

    response = client.get("/users/999/messages")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data  # FastAPI возвращает {"detail": "..."} - это стандарт
    assert "Такого пользователя не существует" in data["detail"]  # Проверяем текст ошибки


# Тестируем лимиты смс
def  test_get_user_history_limit(test_db):

    user_id = 555
    for i in range(20):
        save_message(user_id, "user", f"Testing {i}", f"2026-02-02T10:13:{i}0")

    response = client.get(f"/users/{user_id}/messages?limit=5")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 5
    assert len(data["messages"]) == 5


# Тестируем кол-во пользователей
def test_list_users(test_db):
    save_message(111, "user", "Testing1", "2026-02-02T10:13:10")
    save_message(112, "user", "Testing2", "2026-02-02T10:13:20")
    save_message(111, "user", "Testing3", "2026-02-02T10:13:30")

    response = client.get("/users")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2


# Тестируем получение статистики
def test_getting_statistics(test_db):
    user_id = 111
    for i in range(6):
        save_message(user_id, "user", f"Testing{i}", f"2026-02-02T10:13:{i}0")
        save_message(user_id, "assistant", f"TTesting{i}", f"2026-02-02T10:13:{i}0")

    response = client.get("/stats")

    assert response.status_code == 200
    assert response.json() == {
        "total_messages": 12,  # Общее кол-во смс
        "total_users": 1,  # Кол-во уникальных юзеров
        "user_messages": 6,  # Кол-во смс юзера
        "assistant_messages": 6
    }


# Тестируем сохранение смс
def test_create_message(test_db):
    payload = {
        "user_id": 111,
        "role": "user",
        "text": "test1"
    }

    response = client.post("/messages", json = payload)

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    history = get_conversation_history(111)
    assert history[0]["role"] == "user"
    assert len(history) == 1


# Тестируем удаление смс
def test_delete_messages(test_db):

    user_id = 777
    for  number in range(6):
        save_message(user_id, "user", f"test{number}", f"2026-25-02T10:13:{number}0")

    response = client.delete(f"/users/{user_id}/messages")

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "deleted_count": 6
    }

