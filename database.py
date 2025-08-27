import sqlite3
from contextlib import contextmanager

DATABASE = "bot_database.db"

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER,
                action TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        conn.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def add_user(user_id: int, username: str, full_name: str):
    with get_db() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO users (user_id, username, full_name)
            VALUES (?, ?, ?)
        """, (user_id, username, full_name))
        conn.execute("""
            UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?
        """, (user_id,))

def get_all_user_ids():
    with get_db() as conn:
        cursor = conn.execute("SELECT user_id FROM users")
        return [row[0] for row in cursor.fetchall()]

def log_user_action(user_id: int, action: str):
    with get_db() as conn:
        conn.execute("INSERT INTO user_stats (user_id, action) VALUES (?, ?)", (user_id, action))