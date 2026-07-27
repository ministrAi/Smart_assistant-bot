from .base import DatabaseManager
from datetime import datetime

# Сохранение задачи
def set_task(user_id, current_task):
    started_at = datetime.now().isoformat()
    conn = DatabaseManager.get_connection()
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
    finally:
        DatabaseManager.put_connection(conn)


# Получение задачи
def get_task(user_id):
    conn = DatabaseManager.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT current_task, started_at FROM WorkingMemory
        WHERE user_id = %s 
        """, (user_id,))

        row = cursor.fetchone()

        if row:
            return row[0:2]
        return None
    finally:
        DatabaseManager.put_connection(conn)


# Удаление задачи
def clear_task(user_id):
    conn = DatabaseManager.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
         Delete FROM WorkingMemory 
         WHERE user_id = %s
        """, (user_id,))
        conn.commit()
    finally:
        DatabaseManager.put_connection(conn)
