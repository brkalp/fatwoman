import sqlite3
# id, ticker, date, all_llm_responses, last_llm_response, final_order_decision, order_amount , t_open, t_high, t_low, t_close, profit_made,

# market kapandıktan sonra bu script tekrardan çalışıp open, high low, close priceları dolduracak ve profit_made ı hesaplayacak

def _init_db():
    with sqlite3.connect('flow_trading.db') as conn:
        cursor = conn.cursor()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            date TEXT,
            all_llm_responses TEXT,
            last_llm_response TEXT,
            final_order_decision TEXT,
            order_amount REAL,
            t_open REAL,
            t_high REAL,
            t_low REAL,
            t_close REAL,
            profit_made REAL
        )
        """

        cursor.execute(create_table_query)
        conn.commit() 

_init_db()

def add_entry(ticker, date, all_llm_responses, last_llm_response, final_order_decision, order_amount):
    with sqlite3.connect('flow_trading.db') as conn: 
        cursor = conn.cursor()

        insert_query = """
        INSERT INTO trades (ticker, date, all_llm_responses, last_llm_response, final_order_decision, order_amount)
        VALUES (?, ?, ?, ?, ?, ?)
        """

        cursor.execute(insert_query, (ticker, date, all_llm_responses, last_llm_response, final_order_decision, order_amount))
        conn.commit() 

def update_trade_entry(id, t_open, t_high, t_low, t_close, profit_made):
    with sqlite3.connect('flow_trading.db') as conn: 
        cursor = conn.cursor()

        update_query = """
        UPDATE trades
        SET t_open = ?, t_high = ?, t_low = ?, t_close = ?, profit_made = ?
        WHERE id = ?
        """

        cursor.execute(update_query, (t_open, t_high, t_low, t_close, profit_made, id))
        conn.commit() 

