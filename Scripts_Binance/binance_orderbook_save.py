# Created on 02-28-2024 03:58:58 @author: ripintheblue
from fatwoman_dir_setup import binance_Orderbook_loc_prefix, Binance_save_log_path
from fatwoman_api_setup import Binance_Secret, Binance_Key
from binance.client import Client
import pandas as pd
from datetime import datetime as dt
import os
# import fatwoman_log_setup
import logging

# print('Binance download %s' % dt.now())
client = Client(api_key=Binance_Secret, api_secret=Binance_Key)

def get_order_book(symbol, limit=15):
    order_book = client.get_order_book(symbol=symbol, limit=limit)
    bids = order_book['bids']
    asks = order_book['asks']
    return bids, asks

def process_order_book(bids, asks):
    bids_df = pd.DataFrame(bids, columns=['price', 'quantity']).assign(type='bid')
    asks_df = pd.DataFrame(asks, columns=['price', 'quantity']).assign(type='ask')
    order_book_df = pd.concat([bids_df, asks_df], axis=0).reset_index(drop=True).sort_values(['price'])
    order_book_df['timestamp'] = dt.now().strftime('%Y-%m-%d %H:%M:%S')
    return order_book_df

def save_order_book_to_csv(order_book_df, file_full_path):
    file_exists = os.path.exists(file_full_path)
    order_book_df.to_csv(file_full_path, mode='a', sep=',', header=not file_exists, index=False)
# ImportError: cannot import name 'binance_orderbook_loc_prefix' from 'fatwoman_dir_setup' (/media/fatwoman/15GB/Scripts_Setup_Dirs/fatwoman_dir_setup.py)
ticker = "BTCUSDT"
bids, asks = get_order_book(ticker)
file_full_path = binance_Orderbook_loc_prefix + ticker + ".csv"

order_book_df = process_order_book(bids, asks)
save_order_book_to_csv(order_book_df, file_full_path)
