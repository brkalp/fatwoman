# This will be executed by crontab after markets close and enter market value to flows that didn't get their market value entered.
import yfinance as yf

# from db.flow_db import add_market_val, select_null_market_value
from datetime import datetime, timedelta


# (open-close)*amount, if bullish order made multiply by -1 # TODO: maybe add support for day-trading? this assumes we are the first order
def _calculate_profit(order, amount, open, close):
    pass


def _get_market_values(ticker_name, date):
    start = datetime.strptime(date, "%Y-%m-%d")
    end = start + timedelta(days=1)

    data = yf.download(ticker_name, start=start, end=end, interval="1d",auto_adjust=True)

    if data.empty:
        return None

    data = data.iloc[0]  

    return data["Open"].iloc[0], data["High"].iloc[0], data["Low"].iloc[0], data["Close"].iloc[0]


def _add_values():
    flows = select_null_market_value()
    for flow in flows:
        flow_id = flow["id"]
        ticker = flow["ticker"]
        date = flow["date"]

        open, high, low, close = _get_market_values(ticker, date)

        profit = _calculate_profit()
        add_market_val(flow_id, open, high, low, close, profit)


if __name__ == "__main__":
    open, high, low, close = _get_market_values("AAPL", "2025-10-21")
    # print("\no", open, "\nh", high, "\nl", low, "\nc", close) 
    # will look for flows with missing "market value and add open, high, low, close to market_id. Then calculate profit
