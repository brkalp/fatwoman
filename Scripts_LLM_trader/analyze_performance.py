from datetime import datetime, timedelta
from db.flow_db import get_connection, get_table_name
import sqlite3

def _get_order_null_ratio() -> float:
    with get_connection() as conn:
        query = f"SELECT COUNT(*) AS total, SUM(CASE WHEN order_col IS NULL THEN 1 ELSE 0 END) AS null_count FROM {get_table_name()}"
        row = conn.execute(query).fetchone()
        return row["null_count"] / row["total"] if row["total"] else 0

def _get_profit_all_time() -> float:
    with get_connection() as conn:
        today = datetime.today().strftime("%Y-%m-%d")
        return _get_profit_last_days(until_date=today, last=999)

def _get_profit_today(date: str):
    return _get_profit_last_days(until_date=date, last=1)

def _get_profit_last_days(until_date: str = None, last: int = 3) -> float:
    if until_date is None:
        until_date = datetime.today().strftime("%Y-%m-%d")
    from_date = (datetime.strptime(until_date, "%Y-%m-%d") - timedelta(days=last)).strftime("%Y-%m-%d")
    # print("until_date ", until_date, "   from_date: ", from_date)

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        query = f"SELECT SUM(profit_made) AS total_profit FROM {get_table_name()} WHERE date BETWEEN ? AND ?"
        row = conn.execute(query, (from_date, until_date)).fetchone()
        if not row:
            return "no flows"
        return row["total_profit"]

def flow_performance_of_date(date:str)->str: # Returns performance of all flows of a day
    """ 
    date: yyyy-mm-dd
    ticker, order, amount, profit, open, close, flow_id
    AAPL,   bullish,   1,      10,    100,  110,   85
    AMZN,   bearish,   1,      10,    100,   90,   86
    ...
    """
    pass


def EOD_message(date: str = None):
    date = date or datetime.today().strftime("%Y-%m-%d")
    last = 3
    text = (
        f"Profit made today: {_get_profit_today(date)}\n"
        f"Profit made from last {last} days: {_get_profit_last_days(until_date=date, last=last)}\n"
        f"Profit all time : {_get_profit_all_time()}"
    )
    return text

if __name__ == "__main__":
    print(EOD_message())
