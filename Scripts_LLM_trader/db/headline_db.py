import sqlite3, os

TABLE_NAME = "headlines"
TABLE_DIR_NAME = TABLE_NAME + ".db"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, TABLE_DIR_NAME)


# TODO: Headline db columns: headline, date, source, tags_given, importance
def add_entry(headline: str, date: str, tags_given: str, importance: int, source: str):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(  # create table
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                headline TEXT NOT NULL,
                date TEXT DEFAULT (DATE('now')),
                tags_given TEXT,
                importance INTEGER DEFAULT 0,
                source TEXT
            )
        """
        )

        conn.execute(  # Add entry
            """
            INSERT INTO headlines (headline, date, tags_given, importance, source)
            VALUES (?, ?, ?, ?, ?)
        """,
            (headline, date, tags_given, importance, source),
        )

        conn.commit()
