import psycopg2
import config
import logging
logger = logging.getLogger(__name__)


# Создаем таблицу
def init_db():
    conn = psycopg2.connect(config.DATABASE_URL)
    cursor = conn.cursor()

    # Создаем таблицу Message если ее нет
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Communication (
        id SERIAL PRIMARY KEY ,
        user_id INTEGER,
        text TEXT,
        timestamp TEXT,
        role TEXT,
        is_active INTEGER DEFAULT 1
    )
    """)


    # Фиксируем изменения и закрываем
    conn.commit()
    conn.close()



# Сохраняем сообщения в таблицу
def save_message(user_id, role, text, timestamp):
    logger.debug(f"🔵 Сохраняю сообщение: user={user_id}, role={role}, text={text[:20]}...")
    if not isinstance(timestamp, str):
        timestamp = timestamp.isoformat()

    conn = psycopg2.connect(config.DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO Communication (user_id, role, text, timestamp)
    VALUES (%s, %s, %s, %s)
    """, (user_id, role, text, timestamp))

    cursor.execute("""
            UPDATE Communication 
            SET is_active = 0 
            WHERE user_id = %s AND is_active = 1 AND id NOT IN (
                  SELECT id FROM Communication 
                  WHERE user_id = %s AND is_active = 1
                  ORDER BY id DESC 
                  LIMIT %s
              )
        """, (user_id, user_id, config.MAX_ACTIVE_MESSAGES))

    conn.commit()
    conn.close()



# Получаем диалог
def get_conversation_history(user_id, limit=config.MAX_ACTIVE_MESSAGES):
    conn = psycopg2.connect(config.DATABASE_URL)
    cursor = conn.cursor()


    cursor.execute("""
    SELECT role, text FROM Communication 
    WHERE user_id = %s 
      AND role IS NOT NULL 
      AND role IN ('user', 'assistant') 
      AND is_active = 1
    ORDER BY id
    LIMIT %s
    """, (user_id, limit,))

    message_list = []
    rows = cursor.fetchall()
    for row in rows:
        role = row[0]
        text = row[1]

        if text and text.strip():  # если текст не пустой
            message_list.append({
                "role": role,
                "content": text
            })

    # .commit не нужен т.к. ничего не изменяем
    conn.close()

    return message_list

# Полное удаление всех сообщений и обнуление ID.
def hard_reset_communications():
    conn = psycopg2.connect(config.DATABASE_URL)
    cursor = conn.cursor()

    try:
        cursor.execute("""
        TRUNCATE TABLE Communication
        RESTART IDENTITY""")
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке БД: {e}")
        conn.rollback()
    finally:
        conn.close()



                                            # __API__



# Мягкое удаление смс из БД
def delete_user_messages(user_id):
    conn = psycopg2.connect(config.DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE Communication
    SET is_active = 0
    WHERE user_id = %s AND is_active = 1
    """, (user_id,))

    count = cursor.rowcount  # кол-во строк которые реально изменились
    conn.commit()
    conn.close()
    return count



# Список пользователей
def get_all_users():
    conn = psycopg2.connect(config.DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT DISTINCT user_id
    FROM Communication
    """)

    rows = cursor.fetchall()
    conn.close()
    users = [row[0] for row in rows]
    return users



# Отображение статистики
def getting_statistics():
    conn = psycopg2.connect(config.DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*) FROM Communication
    """)
    total_message = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT user_id) FROM Communication
        """)
    total_users = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM Communication
        WHERE role = 'user'
        """)
    user_messages = cursor.fetchone()[0]

    cursor.execute("""
            SELECT COUNT(*) FROM Communication
            WHERE role = 'assistant'
            """)
    assistant_messages = cursor.fetchone()[0]

    conn.close()

    receiving = {
            "total_messages": total_message,            # Общее кол-во смс
            "total_users": total_users,                 # Кол-во уникальных юзеров
            "user_messages": user_messages,             # Кол-во смс юзера
            "assistant_messages": assistant_messages    # Кол-во смс ассистента
        }
    return receiving
