import logging

logging.basicConfig(level=logging.INFO)
from flows.trading_flow_v2 import flow_v2 
from flows.trading_flow_v1 import flow_v1
from data_gathering.FinnHub import save_news 
from datetime import datetime, timedelta

import sys, os  # To make it work no matter where it is executed from

# "https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates" -> get chat_id

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_flow_v1(start_date:str, end_date:str, ticker:str): # flow 1 # BU DA THREADLENEBİLİR
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    cur_date = start_date
    while cur_date <= end_date:
        date_str = cur_date.strftime("%Y-%m-%d")
        logging.info(f"Running flow for: {date_str}")
        flow_v1(ticker=ticker, date=date_str, notify_users=False, headline_factory="ticker_news")

        cur_date += timedelta(days=1)

"""
def test_for_days(start_date:str, end_date:str): # flow 2
    save_news()
    for daate in range(start_date, end_date): # TODO FIX
        flow_v2(date = date, notify_users=False)
"""

if __name__ == "__main__":
    logging.info("Starting Backtesting")
    test_flow_v1(start_date="2025-01-01", end_date="2025-02-01", ticker = "AAPL")
    logging.info("Finished Backtesting")
    