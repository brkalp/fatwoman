import sqlite3
from datetime import datetime

TABLE = "chat_cache.db"

# prompt not Null, context not Null, response not Null, recycled = False, input tokens not Null, output tokens not Null, timestamp not Null
# Ortak bir db bütün ajanların farklı dblere sahip olmasından daha iyi olabilir.


def create_table():
    conn = sqlite3.connect(TABLE)

    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            context TEXT NOT NULL,
            response TEXT NOT NULL,
            recycled BOOLEAN NOT NULL,
            input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()
    conn.close()


def log_chat_interaction(prompt, context, response, input_tokens, output_tokens, agent_name, model_used, recycled=False):
    conn = sqlite3.connect(TABLE)

    create_table()  # Ensure table exists

    conn.execute(
        f"""
        INSERT INTO {TABLE} (prompt, context, response, recycled, input_tokens, output_tokens)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (prompt, context, response, recycled, input_tokens, output_tokens),
    )

    conn.commit()
    conn.close()


def fetch_cached_row(prompt, context, model_used):
    conn = sqlite3.connect(TABLE)
    create_table()  # Ensure table exists
    
    cursor = conn.execute(
        f"""
        SELECT response FROM {TABLE}
        WHERE prompt = ? AND context = ? AND model_used = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """,
        (prompt, context, model_used),
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        return row
    return None


def print_db_contents():
    conn = sqlite3.connect(TABLE)
    cursor = conn.execute(f"SELECT * FROM {TABLE}")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()


if __name__ == "__main__":
    print_db_contents()
