import logging
from fatwoman_log_setup import script_end_log

logging.basicConfig(level=logging.INFO)
from flows.trading_flow_v2 import flow_v2
from flows.trading_flow_v1 import flow_v1
from data_gathering.FinnHub import save_news
from data_gathering.db_price_fetcher import _get_market_values
import datetime

import sys, os  # To make it work no matter where it is executed from

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sys, traceback


def _tracehook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)


sys.excepthook = _tracehook

if __name__ == "__main__":
    logging.info("Starting LLM main")
    save_news()

    date = datetime.date.today()
    logging.info(f"date being given: {date}")

    flow_v2(date=date, notify_users=True)
    script_end_log()
