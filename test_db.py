import sqlite3
from config import DB_PATH

def get_user_history(user_id, limit=10):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT text, timestamp FROM Messages WHERE user_id=? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()

    print(f"Последние {limit} сообщений пользователя {user_id}:")
    for text, ts in rows:
        print(f"{ts} | {text}")

if __name__ == "__main__":
    get_user_history(1067369536, limit=5)
