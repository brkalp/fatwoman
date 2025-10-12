import sqlite3, os
from datetime import datetime

DB_PATH = "chat_cache.db"
TABLE = "chat_cache"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, DB_PATH)

def create_table():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                context TEXT NOT NULL,
                response TEXT NOT NULL,
                recycled BOOLEAN NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                agent_name TEXT,
                model_used TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # conn.commit() # TODO: Is this needed with 'with' statement? # I guess not


def log_chat_interaction(prompt, context, response, input_tokens, output_tokens,
                         agent_name, model_used, recycled=False):
    create_table()
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(f"""
            INSERT INTO {TABLE} 
            (prompt, context, response, recycled, input_tokens, output_tokens, agent_name, model_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (prompt, context, response, recycled, input_tokens, output_tokens, agent_name, model_used))
    


def fetch_cached_row(prompt, context, model_used):
    create_table()
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row # no idea why this is needed for dict-like access. TODO research
        cursor = conn.execute(f"""
            SELECT * FROM {TABLE}
            WHERE prompt = ? AND context = ? AND model_used = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (prompt, context, model_used))
        row = cursor.fetchone()
  
    return row


def print_db_contents():
    create_table()
    print("Database contents:")
    with sqlite3.connect(DB_FILE) as conn:
        for row in conn.execute(f"SELECT * FROM {TABLE}"):
            print(row) 
            
if __name__ == "__main__":
    print_db_contents()
