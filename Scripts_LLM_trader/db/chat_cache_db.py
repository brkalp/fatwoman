import sqlite3, os, threading 

DB_PATH = "chat_cache.db"
TABLE = "chat_cache"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, DB_PATH)

mutex_lock = threading.Lock() # Prevent concurrent write issues to db

# Recycled'ı sil
def _init_table():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
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
 

_init_table()


def log_chat_interaction(prompt, context, response, input_tokens, output_tokens,
                         agent_name, model_used, recycled=False):

    with mutex_lock: # Threading safety
        with sqlite3.connect(DB_FILE, timeout=10.0) as conn:
            conn.execute("BEGIN IMMEDIATE;")
            conn.execute(f"""
                INSERT INTO {TABLE} 
                (prompt, context, response, recycled, input_tokens, output_tokens, agent_name, model_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (prompt, context, response, recycled, input_tokens, output_tokens, agent_name, model_used))
    


def fetch_cached_row(prompt, context, model_used):
    with sqlite3.connect(DB_FILE, timeout=10.0) as conn:
        conn.row_factory = sqlite3.Row # no idea why this is needed for dict-like access. TODO research
        cursor = conn.execute(f"""
            SELECT * FROM {TABLE}
            WHERE prompt = ? AND context = ? AND model_used = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (prompt, context, model_used))
        row = cursor.fetchone()
  
    return row

def get_id(prompt, resp): # TODO how to get value from row
    with sqlite3.connect(DB_FILE, timeout=10.0) as conn:
        query = """
            SELECT id FROM {TABLE}
            WHERE prompt = ? AND context = ? AND model_used = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """
        
        cursor = conn.execute(query, (prompt, resp))
        row = cursor.fetchone()
        return row


def print_db_contents():
    print("Database contents:")
    with sqlite3.connect(DB_FILE) as conn:
        for row in conn.execute(f"SELECT * FROM {TABLE}"):
            print(row) 
            
if __name__ == "__main__":
    print_db_contents()
