import config
from .base import DatabaseManager


# Сохранение рефлексии
def save_reflection(user_id, reflection, timestamp):
    """Функция сохраняет новую рефлексию пользователя и автоматически поддерживает лимит активных рефлексий, деактивируя старые."""
    if not isinstance(timestamp, str):
        timestamp = timestamp.isoformat()
    conn = DatabaseManager.get_connection()
    try:
        cursor = conn.cursor()
        # Вставляем новую рефлексию
        cursor.execute("""
        INSERT INTO ReflectionMemory (user_id, reflection, timestamp)
        VALUES (%s, %s, %s)
        """, (user_id, reflection, timestamp))
        # Деактивируем старую
        cursor.execute("""
        UPDATE ReflectionMemory
        SET is_active = 0
        WHERE user_id = %s AND is_active = 1 AND id NOT IN (
            SELECT id FROM ReflectionMemory
            WHERE user_id = %s AND is_active = 1
            ORDER BY id DESC
            LIMIT %s
            )
        """, (user_id, user_id, config.MAX_ACTIVE_REFLECTION))
        conn.commit()
    finally:
        DatabaseManager.put_connection(conn)


# Получение рефлексии
def get_reflection(user_id):
    conn = DatabaseManager.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT reflection, timestamp FROM ReflectionMemory 
        WHERE user_id = %s 
            AND is_active = 1
        ORDER BY id
        LIMIT %s
        """, (user_id, config.MAX_ACTIVE_REFLECTION))

        reflection_list = []
        rows = cursor.fetchall()
        for row in rows:
            reflection = row[0]
            timestamp = row[1]

            if reflection and reflection.strip():
                reflection_list.append({
                    "timestamp": timestamp,
                    "content": reflection
                })

    finally:
        DatabaseManager.put_connection(conn)
    return reflection_list

