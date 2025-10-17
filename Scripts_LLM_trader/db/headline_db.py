import sqlite3, os

TABLE_NAME = "headlines"
TABLE_DIR_NAME = TABLE_NAME + ".db"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, TABLE_DIR_NAME)
print(f"DB file path: {DB_FILE}")


# headline, datetime, summary,  source, url, tags_given, importance
def add_entry(
    headline: str, date: str,  summary: str, url: str, source:str, tags_given: str, importance: int
):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(  # create table
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                headline TEXT NOT NULL,
                date TEXT DEFAULT (DATE('now')),
                summary TEXT,
                source TEXT,
                url TEXT,
                tags_given TEXT,
                importance INTEGER DEFAULT 0
            )
        """
        )

        # check for duplicates
        cur = conn.execute(
            f"SELECT 1 FROM {TABLE_NAME} WHERE headline=? AND summary=? LIMIT 1",
            (headline, summary)
        )

        if cur.fetchone() is None:
            conn.execute(  # Add entry
                """
                INSERT INTO headlines (headline, date, summary, url, tags_given, importance, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (headline, date, summary, url, tags_given, importance, source)
            )

        conn.commit()

def update_entryy():  # for adding tags_given and importance later
    pass