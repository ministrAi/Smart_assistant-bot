from services.database import save_reflection, get_reflection


def test_save_and_get_reflection(test_db):
    """Тестируем сохранение и получение рефлексии"""
    user_id = 123
    content = "Выжимка"
    timestamp = "2026-04-11T10:21:28.313814"

    save_reflection(user_id, content, timestamp)
    get_reflection1 = get_reflection(user_id)


    assert get_reflection1[0]["content"] == "Выжимка"