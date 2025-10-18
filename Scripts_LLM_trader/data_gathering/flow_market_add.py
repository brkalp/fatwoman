# This will be executed by crontab after markets close and enter market value to flows that didn't get their market value entered.
import yfinance as yf
from db.flow_db import add_market_val, select_null_market_value


# (open-close)*amount, if bullish order made multiply by -1 # TODO: maybe add support for day-trading? this assumes we are the first order 
def _calculate_profit(order, amount, open, close):
    pass


def _get_market_values(ticker_name, date):
    open = yf.magic
    high = yf.magic
    low = yf.magic
    close = yf.magic

    return open, high, low, close


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
    _add_values()

    # will look for flows with missing market value and add open, high, low, close to market_id. Then calculate profit
