# FK -> FK connector db
# flow_id, chat_id
# TODO: ADD MUTEX LOCK
import sqlite3, threading

DB_NAME = "flow_chat_conn"
DB_PATH = DB_NAME + ".db"

mutex_lock = threading.Lock()

def _init():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        query = f"""
            CREATE TABLE IF NOT EXISTS {DB_NAME} (
            flow_id INTEGER NOT NULL PRIMARY KEY,
            chat_id INTEGER NOT NULL PRIMARY KEY
            )
        """
        cursor.execute(query)

        conn.commit()

_init()


def add_chat(flow_id, chat_id):
    with mutex_lock:
        with sqlite3.connect(DB_PATH) as conn:
            query = (
                f"""
            INSERT INTO {DB_NAME} (flow_id, chat_id) VALUES (?,?)
            """,
            )
            conn.execute(query, (flow_id, chat_id))
            conn.commit()
