import logging, threading

logging.basicConfig(level=logging.INFO)
from flows.trading_flow_v2 import flow_v2 
from flows.trading_flow_v1 import flow_v1
from data_gathering.FinnHub import save_news 
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

import sys, os  # To make it work no matter where it is executed from

# "https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates" -> get chat_id

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_flow_v1(start_date: str, end_date: str, ticker: str):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    dates = []
    cur = start
    while cur <= end:
        dates.append(cur.strftime("%Y-%m-%d"))
        cur += timedelta(days=1)

    def run_day(date_str):
        logging.info(f"Running flow for: {date_str}")
        flow_v1(
            ticker=ticker,
            date=date_str,
            notify_users=False,
            headline_factory="ticker_news"
        )

    # choose worker count as needed
    with ThreadPoolExecutor(max_workers=10) as pool:
        pool.map(run_day, dates)

"""
def test_for_days(start_date:str, end_date:str): # flow 2
    save_news()
    for daate in range(start_date, end_date): # TODO FIX
        flow_v2(date = date, notify_users=False)
"""

if __name__ == "__main__":
    logging.info("Starting Backtesting")
    test_flow_v1(start_date="2025-02-01", end_date="2025-03-01", ticker = "AAPL")
    logging.info("Finished Backtesting")
    