import logging

logging.basicConfig(level=logging.INFO)
from flows.trading_flow_v2 import flow_v2
from flows.trading_flow_v1 import flow_v1
from data_gathering.FinnHub import save_news
from data_gathering.flow_market_add import _get_market_values
import datetime

import sys, os  # To make it work no matter where it is executed from

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


if __name__ == "__main__":
    logging.info("Starting LLM main")
    # save_news()
    
    # print("text",_get_market_values("AAPL", "2025-10-24"))
    
    date=datetime.date.today()
    logging.info(f"date being given: {date}")

    flow_v2(date=date, notify_users=True)
    # flow_v1(date=date,ticker="TSLA", notify_users=True)
    logging.info("Finished LLM main")
    