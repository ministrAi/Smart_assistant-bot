from services.memory_manager import create_reflection, add_fact_with_check
from services.database import set_task, get_task, save_message, get_reflection, get_facts
from datetime import datetime
import pytest

async def fake_response(history):
    return "Тестовый отчет"

@pytest.mark.asyncio
async def test_create_reflection(test_db, monkeypatch):
    monkeypatch.setattr("services.memory_manager.get_ai_response", fake_response)
    user_id = 123
    current_task = "Решить уравнение"
    set_task(user_id, current_task)

    user_id = 123
    role = "user"
    text = "Это тестовое смс"
    timestamp = datetime.now().isoformat()

    save_message(user_id, role, text, timestamp)
    await create_reflection(user_id)
    reflections = get_reflection(user_id)

    assert reflections[0]["content"] == "Тестовый отчет"
    assert get_task(user_id) is None



@pytest.mark.asyncio
async def test_add_fact_with_check(test_db, monkeypatch):
    """Тест add_fact_with_check: добавление нового факта и обработка дубликата"""
    user_id = 123
    fact = "Я очень люблю программировать на Python"

    # Мокаем AI-ответ
    async def fake_ai(messages):
        return "None"                    # Первый раз — конфликта нет

    monkeypatch.setattr("services.memory_manager.get_ai_response", fake_ai)

    # Первый вызов — добавление нового факта
    await add_fact_with_check(user_id, fact, importance="high")

    facts = get_facts(user_id)
    assert len(facts) == 1
    assert facts[0]["content"] == fact
    assert facts[0]["importance"] == "high"

    # Второй вызов — тот же факт с другой важностью
    async def fake_ai_conflict(messages):
        return "1"                       # AI нашёл конфликт с id=1

    monkeypatch.setattr("services.memory_manager.get_ai_response", fake_ai_conflict)

    await add_fact_with_check(user_id, fact, importance="low")

    facts = get_facts(user_id)
    assert len(facts) == 1, "Факт не должен дублироваться"
    assert facts[0]["importance"] == "low", "Важность должна обновиться"
