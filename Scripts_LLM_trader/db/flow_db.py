import sqlite3, threading, os

# id, date, ticker, order, amount, open, high, low, close,

# market kapandıktan sonra bu script tekrardan çalışıp open, high low, close priceları dolduracak ve profit_made ı hesaplayacak

mutex = threading.Lock()

DB_NAME = "flow"
DB_PATH = DB_NAME + ".db"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, DB_PATH)


def _init_db():
    with mutex:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()

            q = f"""
            CREATE TABLE IF NOT EXISTS {DB_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT, 
                ticker TEXT,
                "order" TEXT,
                "order_amount" REAL,
                open REAL,
                high REAL, 
                low REAL,
                close REAL,
                profit_made REAL,
                flow_name TEXT
            )
            """

            cursor.execute(q)


_init_db()


def add_base(
    ticker, date, flow_name=""
):  # this should probably check if this ticker and date pair was added before and if was; overwrite it ?
    with mutex:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()

            insert_query = f"""
            INSERT INTO {DB_NAME} (ticker, date)
            VALUES (?, ?)
            """

            cursor.execute(insert_query, (ticker, date))


def add_order(flow_id, order, amount):

    with mutex:
        with sqlite3.connect(DB_FILE) as conn:

            query = f"""
            UPDATE {DB_NAME}
            SET "order" = ?, order_amount = ?
            WHERE id = ?
            """
            conn.execute(query, (order, amount, flow_id))


# for flow_market_add.py
def add_market_values(id, open, high, low, close):
    with mutex:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()

            update_query = f"""
            UPDATE {DB_NAME}
            SET open = ?, high = ?, low = ?, close = ?
            WHERE id = ?
            """

            cursor.execute(update_query, (open, high, low, close, id))
            conn.commit()


def add_profit(flow_id, profit_made):
    with mutex:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()

            update_query = f"""
            UPDATE {DB_NAME}
            SET profit_made = ?
            WHERE id = ?
            """

            cursor.execute(update_query, (profit_made, flow_id))
            conn.commit()

def get_id(ticker, date):
    with sqlite3.connect(DB_FILE, timeout=10.0) as conn:
        query = f"""
            SELECT id FROM {DB_NAME}
            WHERE ticker = ? AND date = ?
            ORDER BY date DESC
            LIMIT 1
        """

        cursor = conn.execute(query, (ticker, date))
        row = cursor.fetchone()
        return row[0] if row else None


def select_market_val_empty():  # TODO for flow_market_add.py; return list of rows in dict format
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        query = f""" 
        SELECT * FROM {DB_NAME}
        WHERE close is NULL
    """
        res = conn.execute(query)
        return [dict(row) for row in res.fetchall()]
