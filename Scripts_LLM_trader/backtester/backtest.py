import logging, threading

logging.basicConfig(level=logging.INFO)
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

import sys, os  # To make it work no matter where it is executed from

from llm import flow_26_1
from headlines import ticker_news
from itertools import repeat

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas_market_calendars as mcal  # pip install pandas-market-calendars


def get_date_list_without_holidays(
    start_date: str, end_date: str, exchange: str = "NYSE"
) -> list[str]:  # bütün tatilleri çıkartır
    cal = mcal.get_calendar(exchange)

    schedule = cal.schedule(start_date=start_date, end_date=end_date)
    return [d.strftime("%Y-%m-%d") for d in schedule.index]


def __run_day(date_str, ticker):
    logging.info(f"Running flow for: {date_str}")


    d = datetime.strptime(date_str, "%Y-%m-%d")
    from_date = d - timedelta(days=30)
    from_date = from_date.strftime("%Y-%m-%d")

    
    data = {"headlines": ticker_news(date=date_str, ticker=ticker)}
    response = flow_26_1(ticker=ticker, data=data)
    print("asds",response)


def backtest(start_date: str, end_date: str, ticker: str):
    dates = get_date_list_without_holidays(start_date, end_date)
    with ThreadPoolExecutor(max_workers=10) as pool:  # Choose thread count as needed
        pool.map(__run_day, dates, repeat(ticker))


if __name__ == "__main__":
    logging.info("Starting Backtesting")

    # backtest(start_date="2025-06-01", end_date="2025-10-01", ticker = "AMZN")
    
    __run_day("2025-06-01", "AMZN")
    
    backtest(start_date="2025-06-01", end_date="2025-06-8", ticker="AMZN")

    logging.info("Finished Backtesting")
