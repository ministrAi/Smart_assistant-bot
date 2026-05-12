from .base import get_connection
from datetime import datetime

# Сохранение задачи
def set_task(user_id, current_task):
    started_at=datetime.now().isoformat()
    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("""
                INSERT INTO WorkingMemory(user_id, current_task, started_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    current_task = EXCLUDED.current_task,
                    started_at = EXCLUDED.started_at;
            """, (user_id, current_task, started_at))

        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка при сохранении задачи: {e}")
        return False
    finally:
        conn.close()


# Получение задачи
def get_task(user_id):
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute("""
    SELECT current_task, started_at FROM WorkingMemory
    WHERE user_id = %s 
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0:2]
    return None


# Удаление задачи
def clear_task(user_id):
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute("""
     Delete FROM WorkingMemory 
     WHERE user_id = %s
    """, (user_id,))
    conn.commit()
    conn.close()
