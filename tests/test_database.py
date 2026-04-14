# import sqlite3
import psycopg2
from services.database import save_message, get_conversation_history, getting_statistics, delete_user_messages
from datetime import datetime
from config import TEST_DB_URL


# Тестирование сохранение и получение смс
def test_save_message_and_get_history(test_db):
    # 1. Arrange (Подготовка)
    user_id = 999
    role = "user"
    text = "Это тестовое смс"
    timestamp = datetime.now().isoformat()

    # 2. Act (Действие)
    # Сохраняем смс
    save_message(user_id, role, text, timestamp)
    # Достаем смс
    history = get_conversation_history(user_id)

    # 3. Assert (Проверка)
    assert len(history) == 1
    assert history[0]['role'] == role
    assert history[0]['content'] == text


# Тестирование получение статистики
def test_getting_statistics(test_db):
    # 1. Arrange (Подготовка)
    # Добавляем тестовые смс
    save_message(111, "user", 'Тест1', "2026-02-02T10:01:00")
    save_message(222, "assistant", 'Тест2', "2026-02-02T10:02:00")

    # 2. Act (Действие)
    # Вызываем статистику
    stats = getting_statistics()

    # 3. Assert (Проверка)
    # Проверяем точность смс
    assert stats["total_messages"] == 2
    assert stats["total_users"] == 2
    assert stats["user_messages"] == 1
    assert stats["assistant_messages"] == 1


# Тестируем лимиты смс
def  test_get_user_history_limit(test_db):

    user_id = 555
    for i in range(20):
        save_message(user_id, "user", f"Testing {i}", f"2026-02-02T10:13:{i}0")

    response = get_conversation_history(user_id, limit=5)

    assert len(response) == 5


# Проверка логики "мягкой" очистки данных
def test_message_limit_deactivates_old(test_db):
    # 1. Arrange (Подготовка)
    user_id = 555
    for i in range(40):
        save_message(user_id, 'user',f"Сообщение №{i}", f"2026-02-02T10:00:{i:02d}")

    # Проверяем, что кол-во смс 40
    history_before = get_conversation_history(user_id)
    assert len(history_before) == 40

    # 2. Act (Действие)
    # Добавляем 41-е смс
    save_message(user_id, "user", "Я - 41-е сообщение", "2026-02-02T13:01:00")

    # 3. Assert (Проверка)
    # Проверяем, что смс по прежнему 40 и не больше
    history_after = get_conversation_history(user_id)
    assert len(history_after) == 40

    # Проверяем, что первое смс ушло и второе заняло его место
    assert history_after[0]['text'] == "Сообщение №1"

    conn = psycopg2.connect(TEST_DB_URL)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT is_active
    FROM Communication
    WHERE text = %s
    """, ("Сообщение №0",))
    is_active_val = cursor.fetchone()[0]
    conn.close()


    assert is_active_val == 0


# Тестируем удаление смс
def test_delete_messages(test_db):

    user_id = 777
    for  number in range(6):
        save_message(user_id, "user", f"test{number}", f"2026-25-02T10:13:{number}0")

    deleted = delete_user_messages(user_id)
    assert deleted == 6

    history = get_conversation_history(user_id)
    assert  len(history) == 0

