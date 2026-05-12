from services.database import set_task, get_task, clear_task

def test_task(test_db):
    """Тестируем сохранение/получение/удаление задачи"""
    user_id = 123
    current_task = "Решить уравнение"

    set_task(user_id, current_task)
    current_task, started_at = get_task(user_id)

    assert current_task == "Решить уравнение"

    clear_task(user_id)
    tasks = get_task(user_id)

    assert tasks is None


def test_set_task_overwrites(test_db):
    """Тестируем переписывание задачи"""
    user_id = 123
    current_task1 = "Решить уравнение x"
    current_task2 = "Решить уравнение y"

    set_task(user_id, current_task1)
    set_task(user_id, current_task2)
    current_task, started_at = get_task(user_id)

    assert current_task == "Решить уравнение y"


