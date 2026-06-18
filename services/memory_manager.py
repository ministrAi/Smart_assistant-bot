import json
import re
from services.database import add_fact, get_facts, deactivate_fact
from services.database import get_task, get_messages_for_task, save_reflection, clear_task
from services.ai_manager import call_llm
from datetime import datetime
import logging
logger = logging.getLogger(__name__)


# Пишем функцию формирования краткого отчета по завершенной задаче
async def create_reflection(user_id):
    """Получаем текущую задачу из рабочей памяти если она есть, если нет то None"""
    task = get_task(user_id)
    if not task:
        logger.info(f"create_reflection: задача не найдена для user_id={user_id}, пропускаем")
        return

    current_task, started_at = task     # Распаковываем кортеж: текст задачи и время старта.
    logger.info(f"create_reflection: старт для user_id={user_id}, задача='{current_task[:50]}'")

    # Получаем смс по текущей задачи из общей памяти
    task_messages = get_messages_for_task(user_id, started_at)
    logger.debug(f"create_reflection: получено {len(task_messages)} сообщений с {started_at}")
    user_prompt = {
        "role": "user",
        "content": (
            f'Сэр завершил задачу: "{current_task}".\n\n'
            "Проанализируй протокол диалога и сформируй отчёт:\n"
            "1. Цель задачи\n"
            "2. Выполненные действия (кратко)\n"
            "3. Итог / рекомендация\n\n"
            "Формат: слитный текст, 3-5 предложений, британский стиль."
        )
    }
    # Склеиваем пользовательский промпт и полученные смс по текущей задачи,
    # передаем в LLM и сохраняем в переменную
    full_task = [user_prompt] + task_messages

    summary_report = await call_llm(full_task)
    logger.debug(f"create_reflection: LLM вернул рефлексию длиной {len(summary_report)} символов")

    save_reflection(user_id, reflection=summary_report, timestamp=datetime.now().isoformat())
    clear_task(user_id)
    logger.info(f"create_reflection: рефлексия сохранена, задача очищена для user_id={user_id}")



# Пишем логику устаревания фактов
async def add_fact_with_check(user_id, fact, importance):
    """Получаем факт, если факта нет, то добавляем сразу, если есть то проверяем на конфликт"""
    receiving = get_facts(user_id)
    if not receiving:
        logger.info(f"add_fact_with_check: фактов нет, добавляем без проверки. user_id={user_id}, факт='{fact[:60]}'")
        add_fact(user_id, fact, importance)
        return
    else:
        logger.info(f"add_fact_with_check: найдено {len(receiving)} фактов, проверяем конфликт. user_id={user_id}")
        prompt = {
            "role": "user",
            "content": (
                f"Новый факт {fact}\n\n"
                f"Существующие факты {json.dumps(receiving, ensure_ascii=False)}\n\n"
                "Есть ли конфликт? Если да - ответь только цифрой id конфликтующего факта. Если нет — ответь словом None."
            )
        }
        full_task_1 = [prompt]
        summary_report_1 = await call_llm(full_task_1)
        logger.debug(f"add_fact_with_check: LLM ответил '{summary_report_1.strip()}'")

        # Если ответ на промпт содержит только цифру, то деактивируем старый факт и добавляем новый
        # Приводим к нижнему регистру для надежности анализа текста
        llm_reply = summary_report_1.strip().lower()

        # Защита: если модель явно написала "none" или "нет", то конфликта точно нет
        if "none" in llm_reply or "нет" in llm_reply:
            logger.info(f"add_fact_with_check: Конфликтов не обнаружено (модель ответила None).")
            add_fact(user_id, fact, importance)
            return

        # Ищем первую последовательность цифр в ответе (\d+)
        match = re.search(r'\d+', llm_reply)

        if match:
            # Извлекаем найденную цифру и превращаем в int
            conflict_id = int(match.group())
            logger.warning(f"add_fact_with_check: Обнаружен конфликт! Деактивируем старый факт ID={conflict_id}")
            deactivate_fact(conflict_id)
            add_fact(user_id, fact, importance)
        else:
            # Если цифр не найдено и явного "none" не было (на случай странного ответа модели)
            logger.info(f"add_fact_with_check: Цифр в ответе не найдено, добавляем факт как новый.")
            add_fact(user_id, fact, importance)