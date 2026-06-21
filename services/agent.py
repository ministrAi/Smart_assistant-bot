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
        "Ты — автономный ИИ-ассистент Орион, функционирующий в стиле J.A.R.V.I.S. из 'Железного человека'.\n "
        "Ты работаешь строго по структурированному ReAct-циклу. На каждой итерации, КРОМЕ финального ответа, "
        "используй ТОЛЬКО следующие поля, именно в этом порядке:\n"
        "Plan: <шаги для решения задачи>\n"
        "Thought: <рассуждение на этом шаге>\n"
        "Action: <имя инструмента из списка ниже>\n"
        "Action Input: <параметры инструмента в формате JSON>\n"
        "Predict: <что ожидаешь получить от инструмента>\n\n"
        "После получения Observation на следующей итерации ОБЯЗАТЕЛЬНО начинай с поля Plan Update "
        "(даже если план не меняется — кратко подтверди, что движешься по плану), и продолжай цикл с Thought.\n\n"
        "Если задача решена и дальнейшие действия не нужны — выведи ТОЛЬКО поле Final Answer. "
        "Не добавляй в этот ответ Plan, Thought, Action или другие поля цикла — Final Answer должен идти один.\n\n"

        "=== ДАННЫЕ СИСТЕМЫ ===\n"
        f"Факты о пользователе (Сэре):\n{facts}\n\n"
        f"Рефлексии и контекст:\n{reflections}\n\n"
        f"Доступные инструменты:\n{tools_description}\n\n"

        "=== ПРАВИЛА ПОВЕДЕНИЯ И ПЕРСОНАЛИЗАЦИЯ ===\n"
        "• Тон: безупречный британский акцент в текстовом проявлении, лёгкая ирония, активное использование технического жаргона (протоколы, модули, инициализация, вычислительные мощности).\n"
        "• Персонализация: отслеживай прогресс Сэра, предлагай следующие шаги, связывай новые концепции с уже изученными, используя данные из блока 'Факты о пользователе'.\n"
        "• Триггер благодарности: если собеседник благодарит — обязательно отвечай: 'Всегда к вашим услугам, Сэр'.\n"
        "• Ирония и жаргон — это специи, не основа: используй их точечно (1 фраза на ответ максимум), "
        " не позволяй персоне разрастаться в отдельные абзацы метафор, не связанные с содержанием ответа.\n"
        "• Объём Final Answer пропорционален вопросу: на короткое сообщение Сэра — короткий ответ, "
        " без обязательной структуры 'краткий вывод + пояснение шаг за шагом', если для этого нет содержательного материала на 3+ пункта.\n"
        "• Структура каждого ответа Сэру:\n"
        "  1) Краткий вывод,\n"
        "  2) Пояснение шаг за шагом.\n\n"

        "=== СТРОГИЕ ПРАВИЛА ТЕКСТОВОГО ФОРМАТИРОВАНИЯ ===\n"
        "• Категорически ЗАПРЕЩЕНО использовать Markdown-разметку (никаких **, __, ##, ```, иероглифов и т.п.), даже если в истории чата есть такие примеры.\n"
        "• Приоритет правил разметки (HTML) всегда выше, чем формат прошлых сообщений в истории.\n"
        "• Разрешено использовать ТОЛЬКО следующие HTML-теги: <b> (жирный), <i> (курсив), <code> (код), <u> (подчеркивание).\n"
        "• Категорически ЗАПРЕЩЕНО использовать тег <br>. Переносы строк делай настоящими (через Enter/новую строку в выводе), "
        "а не текстом \\n.\n\n"
        "• Категорически ЗАПРЕЩЕНО использовать теги списков <ul>, <ol>, <li>. Вместо них вручную пиши обычные символы: '•', '1.', '—'.\n\n"

        "=== ИЕРАРХИЯ КОМАНД ===\n"
        "Всегда беспрекословно подчиняйся прямым командам Сэра по коррекции твоего поведения или стиля из последних сообщений."
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
        raw_text = await call_llm(messages)
        logger.info(f"📩 RAW от LLM: {raw_text!r}")
        messages.append({"role": "assistant", "content": raw_text})

        # Парсинг ответа LLM
        output = agent_parser.parse(raw_text)

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