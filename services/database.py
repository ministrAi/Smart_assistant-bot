import  sqlite3
from config import DB_PATH


# Создаем таблицу
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Создаем таблицу Message если ее нет
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Message (
        user_id INTEGER,
        text TEXT,
        timestamp TEXT
    )
    """)

    # Переименовываем Message → Communication
    try:
        cursor.execute("ALTER TABLE Message RENAME TO Communication")

    except sqlite3.OperationalError:
        # Таблица Message не существует (уже переименована ранее)
        pass

    # Добавляем 4-е поле role (если его ещё нет)
    try:
        cursor.execute("""
        ALTER TABLE Communication ADD COLUMN role TEXT
        """)

    except sqlite3.OperationalError:
        # Поле уже существует — пропускаем
        pass

    # Фиксируем изменения и закрываем
    conn.commit()
    conn.close()


def save_message(user_id, role, text, timestamp):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Сохраняем сообщения в таблицу
    cursor.execute("""
    INSERT INTO Communication (user_id, role, text, timestamp)
    VALUES (?, ?, ?, ?)
    """, (user_id, role, text, timestamp))
    conn.commit()
    conn.close()


def get_conversation_history(user_id, limit=20):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Получаем диалог
    cursor.execute("""
    SELECT role, text FROM Communication 
    WHERE user_id = ? 
    ORDER BY timestamp ASC 
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
