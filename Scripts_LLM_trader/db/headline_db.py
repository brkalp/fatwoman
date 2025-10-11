import sqlite3

TABLE_NAME = 'headlines'

# Headline db columns: headline, date, source, tags_given, importance
def add_entry(headline: str, source: str, url: str, timestamp: str):
    conn = sqlite3.connect(f'{TABLE_NAME}.db') 

    conn.execute('''
        CREATE TABLE IF NOT EXISTS headlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            headline TEXT,
            source TEXT,
            url TEXT,
            timestamp TEXT
        )
    ''')
    conn.execute('''
        INSERT INTO headlines (headline, source, url, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (headline, source, url, timestamp))
    
    conn.commit()
    conn.close()

# add functions to get rows by date and probably by source