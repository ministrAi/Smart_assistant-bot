import pytest
import services.agent as agent_module
import logging

@pytest.mark.asyncio
async def test_agent_stops_at_max_iterations(monkeypatch):
    # Мокаем контекст — БД не трогаем вообще
    monkeypatch.setattr(agent_module, "get_facts", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_reflection", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_conversation_history", lambda user_id: [])

    # LLM всегда отвечает одинаково — без Action и без Final Answer,
    # но это провоцирует ветку "деградации формата", а не лимит.
    # Чтобы упереться именно в MAX_ITERATIONS, отвечаем валидным Action,
    # который никогда не завершается Final Answer.
    call_count = {"n": 0}

    async def fake_call_llm(messages):
        call_count["n"] += 1
        return (
            "Thought: думаю\n"
            "Action: get_current_time\n"
            "Action Input: {}\n"
            "Predict: время"
        )

    monkeypatch.setattr(agent_module, "call_llm", fake_call_llm)

    result = await agent_module._run_agent_loop(user_id=123, message="сколько время?")

    assert "слишком сложной" in result
    assert call_count["n"] == agent_module.MAX_ITERATIONS  # MAX_ITERATIONS




@pytest.mark.asyncio
async def test_agent_stops_at_max_tool_calls(monkeypatch, caplog):
    monkeypatch.setattr(agent_module, "get_facts", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_reflection", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_conversation_history", lambda user_id: [])
    caplog.set_level(logging.WARNING)
    call_count = {"n": 0}

    async def fake_call_llm(messages):
        call_count["n"] += 1
        return (
            "Thought: думаю\n"
            "Action: get_current_time\n"
            "Action Input: {}\n"
            "Predict: время"
        )

    monkeypatch.setattr(agent_module, "call_llm", fake_call_llm)

    result = await agent_module._run_agent_loop(user_id=123, message="сколько время?")

    assert "Лимит вызовов инструментов исчерпан" in caplog.text



@pytest.mark.asyncio
async def test_agent_handles_unknown_tool(monkeypatch, caplog):
    """Тест обработки неизвестного инструмента агентом."""
    # Мокаем контекст
    monkeypatch.setattr(agent_module, "get_facts", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_reflection", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_conversation_history", lambda user_id: [])

    caplog.set_level(logging.WARNING)

    call_count = {"n": 0}

    async def fake_call_llm(messages):
        call_count["n"] += 1
        if call_count["n"] == 1:
            # Первая итерация: несуществующий инструмент
            return (
                "Thought: попробую использовать неизвестный инструмент\n"
                "Action: unknown_tool_123\n"
                "Action Input: {}\n"
                "Predict: что-то"
            )
        else:
            # Вторая итерация: валидный Final Answer
            return (
                "Thought: инструмент не найден, формирую ответ\n"
                "Final Answer: Тест прошёл успешно."
            )

    monkeypatch.setattr(agent_module, "call_llm", fake_call_llm)

    result = await agent_module._run_agent_loop(user_id=123, message="Протестируй неизвестный инструмент")

    assert "Тест прошёл успешно" in result
    assert "Инструмент 'unknown_tool_123' не найден в реестре" in caplog.text
    assert call_count["n"] == 2