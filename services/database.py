import os
import sqlite3
from typing import List, Dict

import config


def _extract_sqlite_path(url: str) -> str:
    """
    Преобразуем строку вида sqlite:///c:/path/file.db -> c:/path/file.db
    """
    prefix = "sqlite:///"
    if url.startswith(prefix):
        return url[len(prefix):]
    return url


def _get_connection():
    db_path = _extract_sqlite_path(config.DATABASE_URL)
    # Гарантируем наличие директории
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path)


def init_db():
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Communication (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            timestamp TEXT,
            role TEXT,
            is_active INTEGER DEFAULT 1
        )
        """
    )
    conn.commit()
    conn.close()


def save_message(user_id: int, role: str, text: str, timestamp):
    print(f"🔵 Сохраняю: user={user_id}, role={role}, text={text[:20]}...")
    if not isinstance(timestamp, str):
        timestamp = timestamp.isoformat()

    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO Communication (user_id, role, text, timestamp)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, role, text, timestamp),
    )

    cursor.execute(
        """
        UPDATE Communication
        SET is_active = 0
        WHERE user_id = ?
          AND is_active = 1
          AND id NOT IN (
                SELECT id FROM Communication
                WHERE user_id = ?
                  AND is_active = 1
                ORDER BY id DESC
                LIMIT ?
          )
        """,
        (user_id, user_id, config.MAX_ACTIVE_MESSAGES),
    )

    conn.commit()
    conn.close()


def get_conversation_history(user_id: int, limit: int = config.MAX_ACTIVE_MESSAGES) -> List[Dict]:
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT role, text FROM Communication
        WHERE user_id = ?
          AND role IS NOT NULL
          AND role IN ('user', 'assistant')
          AND is_active = 1
        ORDER BY id
        LIMIT ?
        """,
        (user_id, limit),
    )

    message_list = []
    for role, text in cursor.fetchall():
        if text and text.strip():
            message_list.append({"role": role, "content": text, "text": text})

    conn.close()
    return message_list


# __API__
def delete_user_messages(user_id: int) -> int:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Communication
        SET is_active = 0
        WHERE user_id = ? AND is_active = 1
        """,
        (user_id,),
    )
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count


def get_all_users() -> List[int]:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT DISTINCT user_id
        FROM Communication
        """
    )
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users


def getting_statistics() -> Dict:
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Communication")
    total_message = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM Communication")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Communication WHERE role = 'user'")
    user_messages = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Communication WHERE role = 'assistant'")
    assistant_messages = cursor.fetchone()[0]

    conn.close()

    return {
        "total_messages": total_message,
        "total_users": total_users,
        "user_messages": user_messages,
        "assistant_messages": assistant_messages,
    }
