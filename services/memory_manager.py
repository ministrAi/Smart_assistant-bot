import json
from services.database import add_fact, get_facts, deactivate_fact
from services.database import get_task, get_messages_for_task, save_reflection, clear_task
from services.ai_manager import get_ai_response
from datetime import datetime


# Пишем функцию формирования краткого отчета по завершенной задаче
async def create_reflection(user_id):
    """Получаем текущую задачу из рабочей памяти если она есть, если нет то None"""
    task = get_task(user_id)
    if not task:
        return
    current_task, started_at = task

    # Получаем смс по текущей задачи из общей памяти
    task_messages = get_messages_for_task(user_id, started_at)
    user_prompt = {
        "role": "user",
        "content": (
            f'Сэр завершил задачу: "{current_task}".\n\n'
            "Проанализируй протокол диалога и сформируй отчёт:\n"
            "1. Цель\n"
            "2. Выполненные действия (кратко)\n"
            "3. Итог / рекомендация\n\n"
            "Формат: слитный текст, 3-5 предложений, британский стиль."
        )
    }
    # Склеиваем пользовательский промпт и полученные смс по текущей задачи, передаем в LLM и сохраняем в переменную
    full_task = [user_prompt] + task_messages
    summary_report = await get_ai_response(full_task)

    save_reflection(user_id, reflection=summary_report, timestamp=datetime.now().isoformat())
    clear_task(user_id)


# Пишем логику устаревания фактов
async def add_fact_with_check(user_id, fact, importance):
    """Получаем факт, если факта нет, то добавляем сразу, если есть то проверяем на конфликт"""
    receiving = get_facts(user_id)
    if not receiving:
        add_fact(user_id, fact, importance)
        return
    else:
        prompt = {
            "role": "user",
            "content": (
                f"Новый факт {fact}\n\n"
                f"Существующие факты {json.dumps(receiving, ensure_ascii=False)}\n\n"
                "Есть ли конфликт? Если да - ответь только цифрой id конфликтующего факта. Если нет — ответь словом None."
            )
        }
        full_task_1 = [prompt]
        summary_report_1 = await get_ai_response(full_task_1)

        # Если ответ на промпт содержит только цифру, то деактивируем старый факт и добавляем новый
        # Если не только цифру, то просто добавляем факт
        if summary_report_1.strip().isdigit():
            deactivate_fact(int(summary_report_1), user_id)
        add_fact(user_id, fact, importance)
