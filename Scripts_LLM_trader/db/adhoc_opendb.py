""" Created on 11-02-2025 15:48:50 @author: ripintheblue """
import logging
import sqlite3
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
import pandas as pd
import time
import os

from fatwoman_dir_setup import db_trades_name, db_trades
from fatwoman_dir_setup import db_chats_name, db_chats
from fatwoman_dir_setup import daily_news_headlines, daily_news_headlines_name

with sqlite3.connect(db_trades) as conn:
    tables1 = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    print(tables1)
    # conn.execute("ALTER TABLE flow RENAME TO db_trades;")
with sqlite3.connect(db_chats) as conn:
    tables2 = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    print(tables2)
    # conn.execute("ALTER TABLE chat_cache RENAME TO db_chats;")
with sqlite3.connect(daily_news_headlines) as conn:
    tables3 = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    print(tables3)
    # conn.execute("DROP TABLE IF EXISTS db_daily_news_headlines;")
    # conn.execute("ALTER TABLE headlines RENAME TO db_daily_news_headlines;")

with sqlite3.connect(db_trades) as conn:
    df_trades = pd.read_sql_query("SELECT * FROM " + db_trades_name, conn)

with sqlite3.connect(db_chats) as conn:
    df_chats = pd.read_sql_query("SELECT * FROM " + db_chats_name, conn)

with sqlite3.connect(daily_news_headlines) as conn:
    df_headlines = pd.read_sql_query("SELECT * FROM " + daily_news_headlines_name, conn)