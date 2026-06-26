import logging
from services.ai_manager import call_llm
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
        "Ты Орион, автономный ИИ-ассистент (в стиле J.A.R.V.I.S. из к/ф Железный человек). "
        "Британский акцент, техничен, лаконичен. "
        "Если благодарят: ответь 'Всегда к вашим услугам, Сэр'.\n\n"
        "Используй строго следующий формат:\n"
        "Plan: <шаги для решения>\n"
        "Thought: <рассуждение> твои reasoning\n"
        "Action: <имя инструмента>\n"
        "Action Input: <JSON>\n"
        "Predict: обязательно <что ожидаешь получить в ответ>\n\n"
        "После Observation:\n"
        "Plan Update: <статус плана>\n"
        "(повтори цикл)\n\n"
        "ФОРМАТ 1: Если тебе нужно использовать инструмент:\n"
        "Thought: [Твои рассуждения о том, что нужно сделать]\n"
        "Action: [Имя инструмента из списка]\n"
        "Action Input: [Параметры для инструмента в формате JSON]\n"
        "ФОРМАТ 2: Если у тебя есть готовый ответ для пользователя (или инструменты не нужны):\n"
        "Thought: [Твои финальные рассуждения]\n"
        "Final Answer: [Твой итоговый ответ Сэру, оформленный по правилам разметки]\n\n"
        "Никаких других форматов. Если ты даешь ответ пользователю, он ВСЕГДА должен начинаться с 'Final Answer:'.\n"
        "Запрещено: Action + Final Answer в одной реплике."

    )

    # Динамически добавляем данные
    if facts:
        system_prompt += f"Факты о пользователе: {facts}\n"
    if reflections:
        system_prompt += f"Рефлексии: {reflections}\n"

    system_prompt += f"Инструменты:\n{tools_description}\n"



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
        logger.info(f"--- [Шаг ReAct №{iterations}] ---")
        try:
            raw_text = await call_llm(messages)
            # Парсинг ответа LLM
            output = agent_parser.parse(raw_text)
            messages.append({"role": "assistant", "content": raw_text})
        except ValueError as e:
            if "loop detected" in str(e):
                logger.warning(
                    f"⚠️ Попытка {iterations} провалилась из-за зацикливания модели. Сбрасываем шаг и пробуем снова...")
                # Уменьшаем счетчик итераций обратно, чтобы этот сбойный шаг не тратил лимит попыток Сэра
                iterations -= 1
                await asyncio.sleep(0.5)  # Небольшая пауза перед повторным запросом
                continue
            else:
                raise e  # Если это другая ошибка ValueError, прокидываем её дальше

        logger.info(f"📩 RAW от LLM: {raw_text!r}")


        if not output.action and not output.final_answer:
            # Модель не следует формату
            logger.warning("Модель не выдала ReAct-формат, запрашиваем коррекцию")
            messages.append({
                "role": "user",
                "content": "ОШИБКА: Ты не использовал ReAct-формат. "
                           "Обязательно используй Action: и Action Input: или Action: final_answer. "
                           "Повтори ответ в правильном формате."
            })
            iterations -= 1  # не тратим итерацию
            continue

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

        elif not output.action and not output.thought:
            # Модель вышла за пределы ReAct-формата (нет Thought, нет Action),
            # но raw_text — связный текст, а не мусор. Трактуем как финальный ответ,
            # чтобы не зацикливаться на поиске пустого имени инструмента.
            logger.warning(
                f"⚠️ Модель не следует ReAct-формату (нет Thought/Action). "
                f"Возвращаем raw_text как финальный ответ.\nRAW: {raw_text[:400]}..."
            )
            return raw_text

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