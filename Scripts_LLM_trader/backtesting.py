import logging

logging.basicConfig(level=logging.INFO)
from flows.trading_flow_v2 import flow_v2 
from data_gathering.FinnHub import save_news 
import datetime

import sys, os  # To make it work no matter where it is executed from

# "https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates" -> get chat_id

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_per_ticker(start_date:str, end_date:str): # flow 1
    pass

def test_for_days(start_date:str, end_date:str): # flow 2
    save_news()
    for daate in range(start_date, end_date): # TODO FIX
        flow_v2(date = date, notify_users=False)

if __name__ == "__main__":
    logging.info("Starting Backtesting")
    save_news()
    logging.info("Finished Backtesting")
    