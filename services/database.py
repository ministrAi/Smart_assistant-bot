import  sqlite3
from config import DB_PATH


# Создаем таблицу
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Создаем таблицу Message если ее нет
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Communication (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()


    cursor.execute("""
    INSERT INTO Communication (user_id, role, text, timestamp)
    VALUES (?, ?, ?, ?)
    """, (user_id, role, text, timestamp),
    )

    conn.commit()
    conn.close()



# Получаем диалог
def get_conversation_history(user_id, limit=40):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()


    cursor.execute("""
    SELECT role, text FROM Communication 
    WHERE user_id = ? AND role IS NOT NULL AND role IN ('user', 'assistant') AND is_active = 1
    ORDER BY id ASC 
    LIMIT ?
    """, (user_id, limit,))

    message_list = []
    rows = cursor.fetchall()
    for row in rows:
        role = row[0]
        text = row[1]

        if text and text.strip():  # если текст не пустой
            message_list.append({
                "role": role,
                "text": text
            })

    # .commit не нужен т.к. ничего не изменяем
    conn.close()

    return message_list




                                            # __API__

# Удаление смс из БД
def delete_user_messages(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE Communication
    SET is_active = 0
    WHERE user_id = ?  AND is_active = 1
    """, (user_id,))

    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count



# Список пользователей
def get_all_users(user_id):
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
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
            "total_messages": total_message,
            "total_users": total_users,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages
        }
    return receiving






