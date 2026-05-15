""" Created on 05-10-2026 15:29:41 @author: Denizyalimyilmaz """
import logging
import fatwoman_log_setup
from fatwoman_api_setup import ALPACA_KEY as API_KEY, ALPACA_SECRET as API_SECRET
from fatwoman_dir_setup import LLM_data_path
from fatwoman_log_setup import script_end_log
import pandas as pd
import time
import os

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

PAPER = True
trading_client = TradingClient(API_KEY, API_SECRET, paper=PAPER)
TICKER_LOC = os.path.join(LLM_data_path, "LLM_v0_Adviser_for_top5_latest_response.txt")
TICKERS = [ticker.split()[0] for ticker in pd.read_csv(TICKER_LOC, header=None).values[0]]

TOTAL_AMOUNT_TO_INVEST = 10000  # Define the total amount you want to invest across all stocks
AMOUNT_TO_INVEST_PER_STOCK = TOTAL_AMOUNT_TO_INVEST / len(TICKERS)  # Assuming TOTAL_AMOUNT_TO_INVEST is defined in api_init.py

# request = StockLatestTradeRequest( symbol_or_symbols="AAPL"
# trade = client.get_stock_latest_trade(request)
# price = trade["AAPL"].price

for TICKER in TICKERS:  
    print(f"Attempting {TICKER}")
    try:
        buy_order = MarketOrderRequest(
            symbol=TICKER,
            notional=AMOUNT_TO_INVEST_PER_STOCK,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )
        submitted_order = trading_client.submit_order(order_data=buy_order)
        print(f"Buy order succesfully submitted for {TICKER}")
        logging.info(f"Buy order succesfully submitted for {TICKER}")

    except Exception as e:
        print(f"An error occurred while placing the buy order for {TICKER}: {e}")
        logging.error(f"An error occurred while placing the buy order for {TICKER}: {e}")

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
 