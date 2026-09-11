from .base import DatabaseManager
import logging
logger = logging.getLogger(__name__)

# Сохранение факта
def add_fact(user_id, fact, importance):
    conn = DatabaseManager.get_connection()
    try:
        cursor = conn.cursor()
        # Смысл: "Попробуй вставить, но если возникнет конфликт по (user_id, fact) — просто обнови важность"
        cursor.execute("""
        INSERT INTO LongTermMemory (user_id, fact, importance)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, fact) 
        DO UPDATE SET 
            importance = EXCLUDED.importance, 
            is_active = 1;
        """,(user_id, fact, importance))

        conn.commit()
    finally:
        DatabaseManager.put_connection(conn)


# Получение фактов
def get_facts(user_id):
    conn = DatabaseManager.get_connection()
    # Правило 1: нет соединения → пустой список, не None
    if not conn:
        return []

    try:
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
        return fact_list


    except Exception as e:
        # Правило 2: любая ошибка SQL → лог + пустой список
        logger.error(f"❌ get_facts failed user_id={user_id}: {e}")
        return []

    finally:
        # Правило 3: закрыть соединение всегда (и при успехе, и при ошибке)
        conn.close()


# Мягкое удаление факта
def deactivate_fact(id, user_id):
    conn = DatabaseManager.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE LongTermMemory 
        SET is_active = 0
        WHERE user_id = %s 
        AND id = %s
        """,(user_id, id,))

        conn.commit()
    finally:
        DatabaseManager.put_connection(conn)


