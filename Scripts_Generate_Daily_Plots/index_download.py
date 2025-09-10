""" Created on 02-02-2025 01:11:47 @author: ripintheblue """
import logging
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import Index_folder, Index_data_file, weights_data_file
import pandas as pd
import time
import os
import yfinance as yf
# https://www.slickcharts.com/sp500
# https://github.com/yfiua/index-constituents?tab=readme-ov-file
import requests
import pandas as pd
from io import StringIO

datestart = dt(2025,1,15)

# BF.B          NaN
# BRK.B         NaN

# def fetch_sp500_tickers():
url = 'https://datahub.io/core/s-and-p-500-companies/r/0.csv'
response = requests.get(url)
data = StringIO(response.text)
df = pd.read_csv(data)
timestamp_format = '%d/%m/%Y'
sp500_tickers = df[['Symbol']].copy()
sp500_tickers.loc[:,'Timestamp'] = dt.now().strftime(timestamp_format)
# sp500_tickers.to_csv(Index_data_file)
sp500_tickers.to_csv(Index_data_file, mode='a', header=False, index=False)

# print(sp500_tickers)
df00 = yf.download(sp500_tickers['Symbol'].to_list(), datestart)
df0 = df00['Adj Close']
# len(df0['Close'].columns)
# len(sp500_tickers)
df1 = df0.copy()
df2 = df1.pct_change()
weights = pd.read_csv(weights_data_file).set_index('Symbol')
script_end_log()

df3 = df2.copy()
for symbol in df2.columns:
    df3[symbol] = df2[symbol] * weights.loc[symbol,'Weight'] # care all symbols must have weights
df_sp_est = df3.sum(axis=1)

# dfx = yf.download('^GSPC', dt(2023,1,15))['Adj Close']
# dfx.to_clipboard()
dfx = yf.download('^GSPC', datestart)['Adj Close']
dfx_r = dfx.pct_change()

# print(df_sp_est)
# print(dfx_r)

ticker_sorted = df3.iloc[-1,:].sort_values(ascending=False).index[:15]
df4 = df3[ticker_sorted].copy().iloc[-10:,:]
df4.plot(kind='bar', figsize=(10,5), title='Top 10 Stocks by Weight in S&P 500', ylabel='Daily Return')
# # Function to download only adjusted close data
# def download_adj_close_data(tickers, start_date, end_date=None):
#     if not end_date:
#         end_date = dt.today().strftime('%Y-%m-%d')  # Default to today's date if no end date is provided
#     data = yf.download(tickers, start=start_date, end=end_date, auto_adjust=True)
#     return data

# # Download data in smaller batches to avoid overwhelming the API
# batch_size = 50  # Size of each batch
# adj_close_data = pd.DataFrame()

# for i in range(0, len(sp500_tickers), batch_size):
#     batch_tickers = sp500_tickers[i:i+batch_size]
#     batch_data = download_adj_close_data(batch_tickers, start_date='2023-01-01')['Close']
#     adj_close_data = pd.concat([adj_close_data, batch_data], axis=1)
# adj_close_data['Close']
# df = yf.download('TSLA', auto_adjust=True)