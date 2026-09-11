import logging
from services.ai_manager import call_llm
from services.database import get_facts, get_reflection, get_conversation_history
from services.tools import get_tools_description, get_tool, get_tools_schema
from services.constitution import build_constitution
from  services.critic import evaluate_answer
import asyncio
import re
import json


logger = logging.getLogger(__name__)

# лимиты
AGENT_TIMEOUT = 60
MAX_ITERATIONS = 5
MAX_TOOL_CALLS = 3
MAX_CRITIC_ATTEMPTS = 2


async def run_agent(user_id: int, message: str) -> str:
    """Публичная точка входа. Оборачивает цикл в жёсткий тайм-аут."""
    logger.info(f"🤖 run_agent запущен: user_id={user_id}")
    try:
        return await asyncio.wait_for(
            _run_agent_loop(user_id, message),
            timeout=AGENT_TIMEOUT       # если цикл не уложился в 30с — TimeoutError
        )
    except asyncio.TimeoutError:
        logger.warning(f"⏱ Превышен тайм-аут агента ({AGENT_TIMEOUT}s): user_id={user_id}")
        return "Прошу прощения, Сэр. Превышено время выполнения задачи."


def _clean_for_telegram(text: str) -> str:
    """Приводит текст к безопасному для Telegram HTML виду перед отправкой."""
    if not text:
        return text

    text = text.replace('\\n', '\n')
    text = re.sub(r'(?i)<br\s*/?>', '\n', text)
    text = re.sub(r'(?i)<ul>|</ul>|<p>|</p>', '', text)
    text = re.sub(r'(?i)<li>', '• ', text)
    text = re.sub(r'(?i)</li>', '\n', text)
    text = text.replace('**', '')
    text = text.replace(' < ', ' &lt; ').replace(' > ', ' &gt; ')
    return text


async def _run_agent_loop(user_id: int, message: str) -> str:
    """Запускаем ReAct-цикл для одного смс"""
    # Блок 1: сборка контекста
    facts = get_facts(user_id)
    reflections = get_reflection(user_id)
    tools_description = get_tools_description()

    # Блок 2: Системный промпт контекста
    system_prompt = build_constitution()
    # Динамически добавляем данные
    if facts:
        system_prompt += f"Факты о пользователе: {facts}\n"
    if reflections:
        system_prompt += f"Рефлексии: {reflections}\n"
    system_prompt += f"Инструменты:\n{tools_description}\n"


    # БЛОК 3: СБОРКА messages
    # Сборка истории диалога.
    # Формируем список сообщений в формате OpenAI (ChatML).
    history = get_conversation_history(user_id)
    messages = [
        {"role": "system", "content": system_prompt},
    ] + history + [
        {"role": "user", "content": message}
    ]
    current_turn_start = len(messages)
    logger.debug(f"📚 Контекст собран: фактов={len(facts)}, рефлексий={len(reflections)}, истории={len(history)}")


    # счётчики
    critic_attempts = 0
    iterations = 0
    tool_calls = 0

    # Фаза цикла
    while iterations < MAX_ITERATIONS:
        # Отправка контекста в LLM
        iterations += 1
        logger.info(f"--- [Шаг ReAct №{iterations}] ---")

        # Запрос к LLM с передачей схемы инструментов + запись ответа ассистента в историю диалога
        try:
            llm_response = await call_llm(
                messages,
                tools=get_tools_schema()
            )
            # Сырой ответ LLM — debug-уровень, для расследования проблем формата
            logger.debug(f"📩 RAW от LLM: {llm_response!r}")
            messages.append({
                **llm_response,
                "role": "assistant"
            })
        except ValueError as e:
            if "loop detected" in str(e):
                logger.warning(
                    f"⚠️ Попытка {iterations} провалилась из-за зацикливания модели. Сбрасываем шаг и пробуем снова...")
                # Уменьшаем счетчик итераций обратно, чтобы этот сбойный шаг не тратил лимит попыток
                iterations -= 1     # не тратим итерацию на детектированный цикл
                await asyncio.sleep(0.5)  # Небольшая пауза перед повторным запросом
                continue
            else:
                raise e  # Если это другая ошибка ValueError, прокидываем её дальше

        # Сырой ответ LLM — debug-уровень, для расследования проблем формата
        logger.debug(f"📩 RAW от LLM: {llm_response!r}")
        # Текст рассуждений модели (Thought/Plan/Predict слиты в content)
        if llm_response['content']:
            logger.info(f"🧠 {llm_response['content']}")

        # ВЕТКА А: финальный ответ
        # Если ответ готов - вывод, если нет - вызов инструмента
        if not llm_response.get('tool_calls'):
            passed, feedback = await evaluate_answer(
                question=message,
                answer=llm_response['content'],
                history=messages[current_turn_start:]
            )
            if passed :
                logger.info("✅ Агент нашел финальный ответ.")
                logger.info("✅ Критик одобрил.")
                return _clean_for_telegram(llm_response['content'])      # чистый выход
            else:
                critic_attempts += 1
                logger.warning(f"⚠️ Критик отклонил ответ (попытка {critic_attempts}): {feedback}")
                if critic_attempts >= MAX_CRITIC_ATTEMPTS:
                    logger.warning("⚠️ Лимит попыток критика исчерпан, отдаём ответ как есть.")
                    return _clean_for_telegram(llm_response['content'])


                messages.append({
                    "role": "user",
                    "content": f"Observation: Критик отклонил твой ответ. {feedback} Переформулируй Final Answer с учётом этого."
                })
                iterations -= 1 # не тратим обычную итерацию на попытку критика


        # ВЕТКА Б: вызов инструмента
        else:
            # 1. Извлекаем список запрошенных инструментов.
            # Модель может запросить сразу несколько (Parallel Tool Calling).
            tool_calls_list = llm_response.get("tool_calls") or []

            if len(tool_calls_list) > 1:
                logger.warning(
                    f"⚠️ Модель вернула {len(tool_calls_list)} tool_calls, обрабатываем все "
                    f"(лимит реальных вызовов MAX_TOOL_CALLS={MAX_TOOL_CALLS})"
                )
            # 2. Итерируемся по каждому запросу инструмента
            for tool_call in tool_calls_list:
                tool_name = tool_call["function"]["name"]

                # Парсим аргументы. LLM всегда отдаёт строку, её нужно превратить в dict.
                tool_args = json.loads(tool_call["function"]["arguments"] or "{}")

                # ID конкретного вызова — критически важен. По нему LLM поймёт, к какому запросу относится наш ответ.
                tool_call_id = tool_call["id"]
                logger.info(f"🛠 Агент запрашивает инструмент: {tool_name} с аргументами {tool_args}")

                # 3. Достаём функцию из нашего паттерна Registry
                tool = get_tool(tool_name)

                # 4. Блок проверок (Guardrails)
                if not tool:
                    # Инструмент выдуман моделью (галлюцинация)
                    result = f"Инструмент '{tool_name}' не найден в реестре"
                    logger.warning(f"⚠️ {result}")
                elif tool_calls >= MAX_TOOL_CALLS:
                    # Защита от бесконечных циклов и перерасхода токенов
                    result = (
                        "Лимит вызовов инструментов исчерпан. "
                        "Сформируй финальный ответ на основе уже полученных данных."
                    )
                    logger.warning(f"⚠️ {result}")
                else:
                    # 5. Исполнение инструмента
                    # Прокидываем контекст пользователя, если инструмент этого требует
                    if "user_id" in tool["parameters"]:
                        tool_args["user_id"] = user_id
                    tool_calls += 1
                    try:
                        # Поддержка как асинхронных, так и синхронных функций (гибкость архитектуры)
                        if asyncio.iscoroutinefunction(tool["function"]):
                            result = await tool["function"](**tool_args)
                        else:
                            result = tool["function"](**tool_args)
                        logger.info(f"✅ Результат инструмента: {result}")
                    except Exception as e:
                        # Изолируем ошибку: падение инструмента не должно убивать агента
                        result = f"Ошибка инструмента '{tool_name}': {e}"
                        logger.error(f"❌ {result}")
                # 6. Формирование ответа (Observation)
                # Нативный tool calling требует роль "tool" и ОБЯЗАТЕЛЬНО передачи tool_call_id.
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": str(result),
                })
    logger.warning(f"⚠️ Превышен лимит: iterations={iterations}, tool_calls={tool_calls}")
    return f"Прошу прощения, Сэр. Задача оказалась слишком сложной."