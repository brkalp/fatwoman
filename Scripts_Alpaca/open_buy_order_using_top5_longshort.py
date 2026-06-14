""" Created on 05-10-2026 15:29:41 @author: Denizyalimyilmaz """
import logging
import fatwoman_log_setup
from fatwoman_api_setup import ALPACA_KEY_3 as API_KEY, ALPACA_SECRET_3 as API_SECRET
from fatwoman_dir_setup import LLM_data_path
from fatwoman_log_setup import script_end_log
import pandas as pd
import os

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest

PAPER = True
trading_client = TradingClient(API_KEY, API_SECRET, paper=PAPER)
data_client = StockHistoricalDataClient(API_KEY, API_SECRET)

TICKER_LOC = os.path.join(LLM_data_path, "LLM_v0_Adviser_for_top5_short_latest_response.txt")
TICKERS = [ticker.split()[0] for ticker in pd.read_csv(TICKER_LOC, header=None).values[0]]

TOTAL_AMOUNT_TO_INVEST = 50000
AMOUNT_PER_TRADE = TOTAL_AMOUNT_TO_INVEST / len(TICKERS)

for TICKER in TICKERS:
    print(f"Attempting short {TICKER}")
    try:
        trade_request = StockLatestTradeRequest(symbol_or_symbols=TICKER)
        latest_trade = data_client.get_stock_latest_trade(trade_request)
        price = latest_trade[TICKER].price

        qty = int(AMOUNT_PER_TRADE / price)

        if qty < 1:
            print(f"Skipping {TICKER} - price {price:.2f} exceeds ${AMOUNT_PER_TRADE} budget")
            logging.warning(f"Skipping {TICKER} - price {price:.2f} exceeds position limit")
            continue

        sell_order = MarketOrderRequest(
            symbol=TICKER,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        submitted_order = trading_client.submit_order(order_data=sell_order)
        print(f"Short order submitted for {TICKER} - qty: {qty} @ ~{price:.2f} = ~${qty*price:.2f}")
        logging.info(f"Short order submitted for {TICKER} - qty: {qty} @ ~{price:.2f}")

    except Exception as e:
        print(f"Error placing short order for {TICKER}: {e}")
        logging.error(f"Error placing short order for {TICKER}: {e}")

script_end_log()


# def place_sell_order():
#     sell_order = MarketOrderRequest(
#         symbol=TICKER,
#         qty=1,
#         side=OrderSide.SELL,
#         time_in_force=TimeInForce.DAY,
#     )

#     submitted_order = trading_client.submit_order(order_data=sell_order)
#     print("Sell order submitted:")
#     type(submitted_order)
#     print(type(submitted_order))

# def place_buy_order():
# if __name__ == "__main__":
#     place_buy_order()
    # Uncomment this aft  er you hold shares you want to sell.
    # place_sell_order()
 