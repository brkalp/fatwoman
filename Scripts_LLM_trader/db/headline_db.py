import sqlite3, os

TABLE_NAME = "headlines"
TABLE_DIR_NAME = TABLE_NAME + ".db"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, TABLE_DIR_NAME) 

# headline, datetime, summary,  source, url, tags_given, importance
# TODO this shouldn't be unix time ffs
def add_entry(
    headline: str, date: int,  summary: str, url: str, source:str, tags_given: str, importance: int
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
            date = convert_unix(date)

            conn.execute(  # Add entry
                """
                INSERT INTO headlines (headline, date, summary, url, tags_given, importance, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (headline, date, summary, url, tags_given, importance, source)
            )

        conn.commit()

# Filter by date TODO: and tags_given
def get_entry_summaries(date: str = ""):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        if date:
            cursor.execute(
                f"SELECT summary FROM {TABLE_NAME} WHERE date=? LIMIT 100",
                (date,)
            )
        else:
            cursor.execute(f"SELECT summary FROM {TABLE_NAME} DESC LIMIT 100")

        rows = cursor.fetchall()

        joined = "; ".join(row[0] for row in rows)

        return joined
    

def convert_unix(t:int):
    from datetime import datetime, UTC
    if not isinstance(t, (int, float)) and 1e9 < t < 2e10:
        return t  # already date string
    
    if t > 1e12:  # ms → s
        t /= 1000
    
    return datetime.fromtimestamp(t, tz=UTC).strftime("%Y-%m-%d")

def update_entryy():  # for adding tags_given and importance later
    pass

if __name__ == "__main__":
    print(get_entry_summaries("2025-10-16"))
    print(convert_unix(1694764800))