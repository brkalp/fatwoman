""" Created on 05-10-2026 15:29:41 @author: Denizyalimyilmaz """
import logging
import fatwoman_log_setup
from fatwoman_api_setup import ALPACA_KEY_2 as API_KEY, ALPACA_SECRET_2 as API_SECRET
from fatwoman_dir_setup import LLM_data_path
from fatwoman_log_setup import script_end_log
import pandas as pd 
import glob
import os
from pathlib import Path
import json

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest
from alpaca.data.requests import StockLatestTradeRequest
from alpaca.data.historical import StockHistoricalDataClient

TOTAL_AMOUNT_TO_INVEST = 50000
AMOUNT_TO_INVEST_PER_STOCK = TOTAL_AMOUNT_TO_INVEST / 5  # Assuming TOTAL_AMOUNT_TO_INVEST is defined in api_init.py

PAPER = True
TICKER_LOC = os.path.join(LLM_data_path, "LLM_v0_Adviser_for_top5_latest_response.txt")
trading_client = TradingClient(API_KEY, API_SECRET, paper=PAPER)
trading_client.close_all_positions()

# files = glob.glob(os.path.join(LLM_data_path, "LLM_v1_summarizer*.txt"))
files = [str(f) for f in Path(TICKER_LOC).parent.glob("*summarizer*.txt")]
df = pd.DataFrame([json.loads(Path(f).read_text()) for f in files])

# df = df[df["tendency"] == "bullish"]  # Filter for bullish stocks only, as we are placing buy orders
# current_price = trading_client.get_stock_latest_trade(StockLatestTradeRequest(symbol_or_symbols="AAPL"))["AAPL"].price
data_client = StockHistoricalDataClient(API_KEY, API_SECRET)

for item in df.itertuples():
    ticker = item.ticker
    # Define side based on tendency
    if item.tendency == "bullish":
        side = OrderSide.BUY
        qty = AMOUNT_TO_INVEST_PER_STOCK / data_client.get_stock_latest_trade(StockLatestTradeRequest(symbol_or_symbols=ticker))[ticker].price
    elif item.tendency == "bearish":
        side = OrderSide.SELL
        qty = round(AMOUNT_TO_INVEST_PER_STOCK / data_client.get_stock_latest_trade(StockLatestTradeRequest(symbol_or_symbols=ticker))[ticker].price)
    else:
        logging.error(f"Invalid tendency: {item.tendency}")
        continue
    print(f"Attempting {ticker}, tendency={item.tendency}, confidence={item.confidence}, with qty = {qty}")
    try:
        buy_order = MarketOrderRequest(
            symbol=ticker,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY,
        )
        submitted_order = trading_client.submit_order(order_data=buy_order)

        print(f"Order succesfully submitted for {ticker}")
        logging.info(f"Order succesfully submitted for {ticker}")

    except Exception as e:
        print(f"An error occurred while placing the buy order for {ticker}: {e}")
        logging.error(f"An error occurred while placing the buy order for {ticker}: {e}")
  
# trading_client = TradingClient(API_KEY, API_SECRET, paper=PAPER)

# TOTAL_AMOUNT_TO_INVEST = 10000  # Define the total amount you want to invest across all stocks
# AMOUNT_TO_INVEST_PER_STOCK = TOTAL_AMOUNT_TO_INVEST / len(TICKERS)  # Assuming TOTAL_AMOUNT_TO_INVEST is defined in api_init.py
 
# for TICKER in TICKERS:  
#     print(f"Attempting {TICKER}")
#     try:
#         buy_order = MarketOrderRequest(
#             symbol=TICKER,
#             notional=AMOUNT_TO_INVEST_PER_STOCK,
#             side=OrderSide.BUY,
#             time_in_force=TimeInForce.DAY,
#         )
#         submitted_order = trading_client.submit_order(order_data=buy_order)
#         print(f"Buy order succesfully submitted for {TICKER}")
#         logging.info(f"Buy order succesfully submitted for {TICKER}")

#     except Exception as e:
#         print(f"An error occurred while placing the buy order for {TICKER}: {e}")
#         logging.error(f"An error occurred while placing the buy order for {TICKER}: {e}")

# script_end_log() """