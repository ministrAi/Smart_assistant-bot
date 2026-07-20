import pytest
import services.critic as critic_module
from services.critic import evaluate_answer


@pytest.mark.asyncio
async def test_evaluate_answer_passes_on_high_score(monkeypatch):
    # Мокаем call_llm — не бьём в реальный API
    async def fake_call_llm(messages):
        return "Score: 7\nFeedback: OK"

    monkeypatch.setattr(critic_module, "call_llm", fake_call_llm)

    passed, feedback = await evaluate_answer(
        question="Который час?",
        answer="Сейчас 14:00",
        history=[]
    )

    assert passed is True
    assert feedback == "OK"

@pytest.mark.asyncio
async def test_evaluate_answer_fail_open_on_broken_format(monkeypatch):
    async def fake_call_llm(messages):
        return "hi"

    monkeypatch.setattr(critic_module, "call_llm", fake_call_llm)

    passed, feedback = await evaluate_answer(
        question="Который час?",
        answer="Сейчас 14:00",
        history=[]
    )