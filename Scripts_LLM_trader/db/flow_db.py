import sqlite3, threading, os
from fatwoman_dir_setup import db_trades_name, db_trades

TABLE_NAME = db_trades_name
DB_FILE = db_trades
# id, date, ticker, order, amount, open, high, low, close,

# market kapandıktan sonra bu script tekrardan çalışıp open, high low, close priceları dolduracak ve profit_made ı hesaplayacak

mutex = threading.Lock()

# DB_PATH = db_trades
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DB_FILE = os.path.join(BASE_DIR, DB_PATH)

def _init_db():
    with mutex:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()

            q = f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Date TEXT, 
                Ticker TEXT,
                "Order" TEXT,
                "order_amount" REAL,
                Open REAL,
                High REAL, 
                Low REAL,
                Close REAL,
                profit_made REAL,
                flow_name TEXT
            )
            """

            cursor.execute(q)

# _init_db()

def add_base(
    ticker, date, flow_name="not_defined"
) -> int:  # this should probably check if this ticker and date pair was added before and if was; overwrite it ?
    with mutex:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            insert_query = f"""
            INSERT INTO {TABLE_NAME} (Ticker, Date, flow_name)
            VALUES (?, ?, ?)
            """
            cursor.execute(insert_query, (ticker, date, flow_name))
            return cursor.lastrowid


def add_order(flow_id, order, amount):

    with mutex:
        with sqlite3.connect(DB_FILE) as conn:
            query = f"""
            UPDATE {TABLE_NAME}
            SET "Order" = ?, order_amount = ?
            WHERE id = ?
            """
            conn.execute(query, (order, amount, flow_id))

# for flow_market_add.py
def add_market_values(id, open, high, low, close):
    with mutex:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()

            update_query = f"""
            UPDATE {TABLE_NAME}
            SET Open = ?, High = ?, Low = ?, Close = ?
            WHERE id = ?
            """

            cursor.execute(update_query, (open, high, low, close, id))
            conn.commit()

def add_profit(flow_id, profit_made):
    profit_made = round(profit_made, 3)
    with mutex:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()

            update_query = f"""
            UPDATE {TABLE_NAME}
            SET profit_made = ?
            WHERE id = ?
            """

            cursor.execute(update_query, (profit_made, flow_id))
            conn.commit()

def get_id(ticker, date):
    with sqlite3.connect(DB_FILE, timeout=10.0) as conn:
        query = f"""
            SELECT id FROM {TABLE_NAME}
            WHERE Ticker = ? AND Date = ?
            ORDER BY Date DESC
            LIMIT 1
        """

        cursor = conn.execute(query, (ticker, date))
        row = cursor.fetchone()
        return row[0] if row else None


def select_market_val_empty():  # TODO for flow_market_add.py; return list of rows in dict format
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        query = f""" 
        SELECT * FROM {TABLE_NAME}
        WHERE Close is NULL
    """
        res = conn.execute(query)
        return [dict(row) for row in res.fetchall()]

# """ DEPRECATED
# def select_row_until_date(date:str, limit:int=3):
#     with sqlite3.connect(DB_FILE) as conn:
#         conn.row_factory = sqlite3.Row
#         query = f"SELECT * FROM {TABLE_NAME}
#                 WHERE date <= ? LIMIT ?"
#         cursor = conn.execute(query, (date, limit))
#         return cursor.fetchall()
#         """

# THIS NEEDS TO BE CLOSED!!
def get_connection():
    conn = sqlite3.connect(DB_FILE)
    return conn    

def get_table_name():
    return TABLE_NAME