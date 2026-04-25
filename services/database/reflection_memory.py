import config
from .base import get_connection


# Сохранение рефлексии
def save_reflection(user_id, reflection, timestamp):
    if not isinstance(timestamp, str):
        timestamp = timestamp.isoformat()
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO ReflectionMemory (user_id, reflection, timestamp)
    VALUES (%s, %s, %s)
    """, (user_id, reflection, timestamp))
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
    conn.close()


def get_reflection(user_id):
    conn = get_connection()
    if not conn: return
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

    conn.close()
    return reflection_list

