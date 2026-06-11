import logging
from services.ai_manager import get_ai_response
from services.database import get_facts, get_reflection, get_conversation_history
from services.tools import get_tools_description

logger = logging.getLogger(__name__)

async def run_agent(user_id: int, message: str) -> None:
    """
    Запускаем ReAct-цикл для одного смс
    """
    logger.info(f"🤖 run_agent запущен: user_id={user_id}")

    facts = get_facts(user_id)
    reflections = get_reflection(user_id)
    tools_description = get_tools_description()

    system_prompt = (
        "Ты — автономный ИИ-ассистент Джарвис. Работаешь по ReAct-циклу.\n\n"
        f"Факты о пользователе:\n{facts}\n\n"
        f"Рефлексии:\n{reflections}\n\n"
        f"Доступные инструменты:\n{tools_description}"
    )

    history = get_conversation_history(user_id)
    # Сборка контекста
    messages = [
        {"role": "system", "content": system_prompt},
    ] + history + [
        {"role": "user", "content": message}
    ]
    logger.debug(f"📚 Контекст собран: фактов={len(facts)}, рефлексий={len(reflections)}, истории={len(history)}")

    # лимиты
    MAX_ITERATIONS = 5
    MAX_TOOL_CALLS = 3

    # счётчики
    iterations = 0
    tool_calls = 0

    while iterations < MAX_ITERATIONS and tool_calls < MAX_TOOL_CALLS:
        await get_ai_response(messages)