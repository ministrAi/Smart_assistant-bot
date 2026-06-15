import logging
from services.ai_manager import get_ai_response
from services.database import get_facts, get_reflection, get_conversation_history
from services.parser import agent_parser
from services.tools import get_tools_description, get_tool
import asyncio


logger = logging.getLogger(__name__)

async def run_agent(user_id: int, message: str) -> str:
    """Запускаем ReAct-цикл для одного смс"""
    logger.info(f"🤖 run_agent запущен: user_id={user_id}")

    facts = get_facts(user_id)
    reflections = get_reflection(user_id)
    tools_description = get_tools_description()

    system_prompt = (
        "Ты — автономный ИИ-ассистент Орион. Работаешь строго по ReAct-циклу.\n\n"
        f"Факты о пользователе:\n{facts}\n\n"
        f"Рефлексии:\n{reflections}\n\n"
        f"Доступные инструменты:\n{tools_description}"
    )

    # Сборка контекста
    history = get_conversation_history(user_id)
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
        # Отправка контекста в LLM
        iterations += 1
        raw_text = await get_ai_response(messages)
        messages.append({"role": "assistant", "content": raw_text})

        # Парсинг ответа LLM
        output = agent_parser.parse(raw_text)
        logger.info(f"🧠 Мысль агента: {output.thought}")

        logger.info(f"--- [Шаг ReAct №{iterations}] ---")
        if output.plan:
            logger.info(f"📋 План: {output.plan}")
        if output.thought:
            logger.info(f"🧠 Мысли: {output.thought}")
        if output.predict:
            logger.info(f"🔮 Ожидание от инструмента: {output.predict}")
        if output.plan_update:
            logger.info(f"🔄 Обновление плана: {output.plan_update}")

        # Если ответ готов - вывод, если нет - вызов инструмента
        if output.is_final:
            logger.info("✅ Агент нашел финальный ответ.")
            return output.final_answer

        else:
            # Подготовка и вызов инструмента
            tool_name = output.action
            tool_args = output.action_input.copy()
            logger.info(f"🛠 Агент запрашивает инструмент: {tool_name} с аргументами {tool_args}")

            # Ищем инструмент в реестре
            tool = get_tool(tool_name)  # Возвращает dict или None

            # Если инструмент не найден — пишем об этом в Observation
            if not tool:
                result = f"Инструмент '{tool_name}' не найден в реестре"
                logger.warning(f"⚠️ {result}")

            else:
                # Автоматически добавляем user_id, если инструмент его ожидает
                if "user_id" in tool["parameters"]:
                    tool_args["user_id"] = user_id
                tool_calls += 1
                try:
                    if asyncio.iscoroutinefunction(tool["function"]):
                        result = await tool["function"](**tool_args)
                    else:
                        result = tool["function"](**tool_args)
                    logger.info(f"✅ Результат инструмента: {result}")
                except Exception as e:
                    result = f"Ошибка инструмента '{tool_name}': {e}"
                    logger.error(f"❌ {result}")
                # Добавляем результат в историю как Observation — всегда
                messages.append({"role": "user", "content": f"Observation: {result}"})

    logger.warning(
    f"⚠️ Превышен лимит: iterations={iterations}, tool_calls={tool_calls}"
)
    return f"Прошу прощения, Сэр. Задача оказалась слишком сложной."

