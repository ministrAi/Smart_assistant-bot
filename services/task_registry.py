import logging

logger = logging.getLogger(__name__)

# Реестр активных задач: user_id -> asyncio.Task
# Один и тот же словарь импортируется и в user_handlers.py (запись),
# и в обработчике /stop (чтение + cancel)
_active_tasks: dict[int, "asyncio.Task"] = {}


def register_task(user_id: int, task) -> None:
    """Регистрирует задачу пользователя. Если уже есть активная — перезаписывает (старая просто потеряет ссылку, но не отменяется автоматически)."""
    _active_tasks[user_id] = task
    logger.debug(f"📝 Задача зарегистрирована: user_id={user_id}")


def unregister_task(user_id: int) -> None:
    """Удаляет задачу из реестра. Вызывать в finally — независимо от исхода."""
    _active_tasks.pop(user_id, None)
    logger.debug(f"🗑 Задача удалена из реестра: user_id={user_id}")


def get_task(user_id: int):
    """Возвращает Task пользователя или None, если активной задачи нет."""
    return _active_tasks.get(user_id)


def cancel_task(user_id: int) -> bool:
    """Отменяет активную задачу пользователя. Возвращает True если задача была найдена и отмена запрошена, False если активной задачи не было."""
    task = _active_tasks.get(user_id)
    if task is None:
        return False
    if task.done():
        # Задача уже завершилась, но не успела убраться из реестра
        return False
    task.cancel()
    logger.info(f"🛑 Запрошена отмена задачи: user_id={user_id}")
    return True