from .base import get_connection


# Сохранение факта
def add_fact(user_id, fact, importance):
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    # Смысл: "Попробуй вставить, но если возникнет конфликт по (user_id, fact) — просто обнови важность"
    cursor.execute("""
    INSERT INTO LongTermMemory (user_id, fact, importance)
    VALUES (%s, %s, %s)
    ON CONFLICT (user_id, fact) 
    DO UPDATE SET importance = EXCLUDED.importance;
    """,(user_id, fact, importance))

    conn.commit()
    conn.close()


# Получение фактов
def get_facts(user_id):
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, fact, importance FROM LongTermMemory
    WHERE user_id = %s 
        AND is_active = 1
    ORDER BY id
    """, (user_id,))

    fact_list = []
    rows = cursor.fetchall()
    for row in rows:
        id  = row[0]
        fact = row[1]
        importance = row[2]

        if fact and fact.strip():
            fact_list.append({
                "id": id,
                "content": fact,
                "importance": importance
            })

    conn.close()

    return fact_list


# Мягкое удаление факта
def deactivate_fact(id, user_id):
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE LongTermMemory 
    SET is_active = 0
    WHERE user_id = %s 
    AND id = %s
    """,(user_id, id,))

    conn.commit()
    conn.close()


