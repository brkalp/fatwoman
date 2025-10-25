# This will be executed by crontab after markets close and enter market value to flows that didn't get their market value entered.
import yfinance as yf
import logging

from db.flow_db import add_market_values, select_market_val_empty, add_profit
from datetime import datetime, timedelta


# (open-close)*amount, if bullish order made multiply by -1 # TODO: maybe add support for day-trading? this assumes we are the first order
def _calculate_profit(order, amount, open, close):
    if order is None or amount is None:
        return 0
    return (close - open) * amount if order == "bullish" else (open - close) * amount


def _get_market_values(ticker_name, date):
    start = datetime.strptime(date, "%Y-%m-%d")
    end = start + timedelta(days=1)

    df = yf.download(ticker_name, start=start, end=end, interval="1d", auto_adjust=True)
    if df.empty:
        return None

    row = df.iloc[0]
    return  round(row["Open"].iloc[0], 3), round(row["High"].iloc[0], 3), round(row["Low"].iloc[0], 3), round(row["Close"].iloc[0], 3)
    




# For every null market value flow, get market values and add them to the flow entry, calculate profit and add it too
def add_values():
    flows = select_market_val_empty()
    for flow in flows:
        flow_id = flow["id"]
        ticker = flow["ticker"]
        date = flow["date"]

        open, high, low, close = _get_market_values(ticker, date)

        add_market_values(flow_id, open, high, low, close)

        try:  # order being null doesn't make it crash actually
            order = flow["order"]
            amount = flow["order_amount"]
            profit = _calculate_profit(order, amount, open, close)
            add_profit(flow_id, profit)
        except Exception as e:
            logging.error(f"Error calculating profit for flow_id {flow_id}: {e}")
            continue
