import pytest
import services.agent as agent_module
import logging
import pytest
import services.agent as agent_module


@pytest.mark.asyncio
async def test_agent_handles_parallel_tool_calls(monkeypatch):
    """Два tool_calls за один ход → оба tool_call_id получают role=tool → шаг 2 без 400."""
    monkeypatch.setattr(agent_module, "get_facts", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_reflection", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_conversation_history", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_tools_description", lambda: "- get_user_facts\n- get_current_time")
    monkeypatch.setattr(agent_module, "get_tools_schema", lambda: [])
    monkeypatch.setattr(agent_module, "build_constitution", lambda: "test constitution")

    # Критик всегда пропускает финальный ответ
    async def fake_critic(question, answer, history):
        return True, "OK"
    monkeypatch.setattr(agent_module, "evaluate_answer", fake_critic)

    # Реестр tools: два простых sync-инструмента
    def fake_get_tool(name):
        registry = {
            "get_user_facts": {
                "name": "get_user_facts",
                "function": lambda user_id: "fact: test",
                "parameters": {"user_id": "int"},
            },
            "get_current_time": {
                "name": "get_current_time",
                "function": lambda timezone="UTC": f"time:{timezone}",
                "parameters": {"timezone": "string"},
            },
        }
        return registry.get(name)
    monkeypatch.setattr(agent_module, "get_tool", fake_get_tool)

    call_count = {"n": 0}
    captured_second_messages = {}

    async def fake_call_llm(messages, tools=None):
        call_count["n"] += 1
        if call_count["n"] == 1:
            # Шаг 1: модель просит ДВА инструмента
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_facts_1",
                        "type": "function",
                        "function": {"name": "get_user_facts", "arguments": "{}"},
                    },
                    {
                        "id": "call_time_1",
                        "type": "function",
                        "function": {
                            "name": "get_current_time",
                            "arguments": '{"timezone": "America/New_York"}',
                        },
                    },
                ],
            }
        # Шаг 2: проверяем, что оба id закрыты, и отдаём финальный ответ
        captured_second_messages["messages"] = list(messages)
        return {
            "role": "assistant",
            "content": "Факты получены. В Вашингтоне сейчас время из tool.",
            "tool_calls": None,
        }

    monkeypatch.setattr(agent_module, "call_llm", fake_call_llm)

    result = await agent_module._run_agent_loop(
        user_id=123,
        message="Что помнишь? Сколько времени в Вашингтоне?",
    )

    assert "Факты получены" in result
    assert call_count["n"] == 2

    # --- главное утверждение ---
    tool_msgs = [
        m for m in captured_second_messages["messages"]
        if m.get("role") == "tool"
    ]
    tool_ids = {m["tool_call_id"] for m in tool_msgs}

    assert "call_facts_1" in tool_ids
    assert "call_time_1" in tool_ids
    assert len(tool_msgs) >= 2

@pytest.mark.asyncio
async def test_agent_stops_at_max_iterations(monkeypatch):
    monkeypatch.setattr(agent_module, "get_facts", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_reflection", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_conversation_history", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_tools_description", lambda: "- get_current_time")
    monkeypatch.setattr(agent_module, "get_tools_schema", lambda: [])
    monkeypatch.setattr(agent_module, "build_constitution", lambda: "test")
    monkeypatch.setattr(
        agent_module,
        "get_tool",
        lambda name: {
            "name": "get_current_time",
            "function": lambda timezone="UTC": "12:00",
            "parameters": {"timezone": "string"},
        } if name == "get_current_time" else None,
    )

    call_count = {"n": 0}

    async def fake_call_llm(messages, tools=None):
        call_count["n"] += 1
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": f"call_{call_count['n']}",
                "type": "function",
                "function": {"name": "get_current_time", "arguments": "{}"},
            }],
        }

    monkeypatch.setattr(agent_module, "call_llm", fake_call_llm)

    result = await agent_module._run_agent_loop(user_id=123, message="сколько время?")

    assert "слишком сложной" in result
    assert call_count["n"] == agent_module.MAX_ITERATIONS # ← tools=None обязателен

@pytest.mark.asyncio
async def test_agent_stops_at_max_tool_calls(monkeypatch, caplog):
    monkeypatch.setattr(agent_module, "get_facts", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_reflection", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_conversation_history", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_tools_description", lambda: "- get_current_time")
    monkeypatch.setattr(agent_module, "get_tools_schema", lambda: [])
    monkeypatch.setattr(agent_module, "build_constitution", lambda: "test")
    monkeypatch.setattr(
        agent_module,
        "get_tool",
        lambda name: {
            "name": "get_current_time",
            "function": lambda timezone="UTC": "12:00",
            "parameters": {"timezone": "string"},
        } if name == "get_current_time" else None,
    )
    caplog.set_level(logging.WARNING)

    async def fake_call_llm(messages, tools=None):
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": "call_loop",
                "type": "function",
                "function": {"name": "get_current_time", "arguments": "{}"},
            }],
        }

    monkeypatch.setattr(agent_module, "call_llm", fake_call_llm)

    await agent_module._run_agent_loop(user_id=123, message="сколько время?")

    assert "Лимит вызовов инструментов исчерпан" in caplog.text

@pytest.mark.asyncio
async def test_agent_handles_unknown_tool(monkeypatch, caplog):
    monkeypatch.setattr(agent_module, "get_facts", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_reflection", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_conversation_history", lambda user_id: [])
    monkeypatch.setattr(agent_module, "get_tools_description", lambda: "")
    monkeypatch.setattr(agent_module, "get_tools_schema", lambda: [])
    monkeypatch.setattr(agent_module, "build_constitution", lambda: "test")
    monkeypatch.setattr(agent_module, "get_tool", lambda name: None)  # всё неизвестно

    async def fake_critic(question, answer, history):
        return True, "OK"
    monkeypatch.setattr(agent_module, "evaluate_answer", fake_critic)

    caplog.set_level(logging.WARNING)
    call_count = {"n": 0}

    async def fake_call_llm(messages, tools=None):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_unknown",
                    "type": "function",
                    "function": {"name": "unknown_tool_123", "arguments": "{}"},
                }],
            }
        return {
            "role": "assistant",
            "content": "Тест прошёл успешно.",
            "tool_calls": None,
        }

    monkeypatch.setattr(agent_module, "call_llm", fake_call_llm)

    result = await agent_module._run_agent_loop(
        user_id=123, message="Протестируй неизвестный инструмент"
    )

    assert "Тест прошёл успешно" in result
    assert "Инструмент 'unknown_tool_123' не найден в реестре" in caplog.text
    assert call_count["n"] == 2