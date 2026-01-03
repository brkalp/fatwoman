import sqlite3, os, threading

TABLE = "cache"
DB_FILE = "cache_db.py"

# DB_PATH = TABLE + ".db"
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DB_FILE = os.path.join(BASE_DIR, DB_PATH)

mutex_lock = threading.Lock()  # Prevent concurrent write issues to db


# TODO: add another field for flow_id; remove flow_chat_conn
def _init_table():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
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
                model_used TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            )
        """
        )

        # Add new collumn if not exists
        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({TABLE});")}
        needed = {"flow_id"}
        for col in needed - cols:
            conn.execute(f"ALTER TABLE {TABLE} ADD COLUMN {col} INTEGER;")


_init_table()


def log_chat_interaction(
    prompt,
    context,
    response,
    input_tokens,
    output_tokens,
    agent_name,
    model_used,
    recycled=False,
    flow_id=None,
):
    with mutex_lock:  # Threading safety
        with sqlite3.connect(DB_FILE, timeout=10.0) as conn:
            conn.execute("BEGIN IMMEDIATE;")

            if flow_id:
                query = f"""
                INSERT INTO {TABLE} 
                (prompt, context, response, recycled, input_tokens, output_tokens , model_used )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                conn.execute(
                    query,
                    (
                        prompt,
                        context,
                        response,
                        recycled,
                        input_tokens,
                        output_tokens,
                        model_used,
                    ),
                )
            else:
                query = f"""
                INSERT INTO {TABLE} 
                (prompt, context, response, recycled, input_tokens, output_tokens , model_used )
                VALUES (?, ?, ?, ?, ?, ?,   ?)
                """
                conn.execute(
                    query,
                    (
                        prompt,
                        context,
                        response,
                        recycled,
                        input_tokens,
                        output_tokens, 
                        model_used,
                    ),
                )

            print("Logged chat interaction to DB.")


def fetch_cached_row(prompt, context, model_used):
    with sqlite3.connect(DB_FILE, timeout=10.0) as conn:
        conn.row_factory = (
            sqlite3.Row
        )  # no idea why this is needed for dict-like access. TODO research
        cursor = conn.execute(
            f"""
            SELECT * FROM {TABLE}
            WHERE prompt = ? AND context = ? AND model_used = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """,
            (prompt, context, model_used),
        )

        row = cursor.fetchone()
        print("returned row from db: ", len(row) if row else -1)
        return dict(row) if row else None


def get_id(prompt, resp):  # TODO how to get value from row
    with sqlite3.connect(DB_FILE, timeout=10.0) as conn:
        query = f"""
            SELECT id FROM {TABLE}
            WHERE prompt = ? AND response = ? 
            ORDER BY timestamp DESC
            LIMIT 1
        """

        cursor = conn.execute(query, (prompt, resp))
        row = cursor.fetchone()
        return row

 