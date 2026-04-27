from services.database import get_task
from services.database import get_messages_for_task
from services.ai_manager import get_ai_response


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



