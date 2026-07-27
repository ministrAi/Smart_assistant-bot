# from datetime import datetime
import config
from .base import DatabaseManager

import logging
logger = logging.getLogger(__name__)


# Сохраняем сообщения в таблицу
def save_message(user_id, role, text, timestamp):
    logger.debug(f"🔵 Сохраняю сообщение: user={user_id}, role={role}, text={text[:20]}...")
    if not isinstance(timestamp, str):
        timestamp = timestamp.isoformat()
    conn = DatabaseManager.get_connection()
    try:
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
    finally:
        DatabaseManager.put_connection(conn)


    # Получаем смс по текущей задаче
def get_messages_for_task(user_id, started_at):
    conn = DatabaseManager.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT role, text FROM Communication 
        WHERE user_id = %s 
          AND role IS NOT NULL 
          AND role IN ('user', 'assistant') 
          AND is_active = 1
          AND timestamp >= %s
        ORDER BY id
        """, (user_id, started_at))

        message_current_list = []
        rows = cursor.fetchall()
        for row in rows:
            role = row[0]
            text = row[1]

            if text and text.strip():
                message_current_list.append({
                    "role": role,
                    "content": text
                })
    finally:
        DatabaseManager.put_connection(conn)
    return message_current_list


# Получаем диалог
def get_conversation_history(user_id, limit=config.MAX_ACTIVE_MESSAGES):
    conn = DatabaseManager.get_connection()
    try:
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
    finally:
        DatabaseManager.put_connection(conn)
    return message_list


# Полное удаление всех сообщений и обнуление ID.
def hard_reset_communications():
    conn = DatabaseManager.get_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("""
            TRUNCATE TABLE Communication
            RESTART IDENTITY""")
            conn.commit()
        except Exception as e:
            logger.error(f"❌ Ошибка при очистке БД: {e}")
            conn.rollback()
            raise   # ← без этого ошибка молча исчезает
    finally:
        DatabaseManager.put_connection(conn)


# Мягкое удаление смс из БД
def delete_user_messages(user_id):
    conn = DatabaseManager.get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE Communication
        SET is_active = 0
        WHERE user_id = %s AND is_active = 1
        """, (user_id,))

        count = cursor.rowcount  # кол-во строк которые реально изменились
        conn.commit()
    finally:
        DatabaseManager.put_connection(conn)
    return count



                                    # __API__


# Список пользователей
def get_all_users():
    conn = DatabaseManager.get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT DISTINCT user_id
        FROM Communication
        """)

        rows = cursor.fetchall()
    finally:
        DatabaseManager.put_connection(conn)
    users = [row[0] for row in rows]
    return users



# Отображение статистики
def getting_statistics():
    conn = DatabaseManager.get_connection()
    try:
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

    finally:
        DatabaseManager.put_connection(conn)

    receiving = {
            "total_messages": total_message,            # Общее кол-во смс
            "total_users": total_users,                 # Кол-во уникальных юзеров
            "user_messages": user_messages,             # Кол-во смс юзера
            "assistant_messages": assistant_messages    # Кол-во смс ассистента
        }
    return receiving