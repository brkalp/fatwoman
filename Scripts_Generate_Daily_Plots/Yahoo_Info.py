""" Created on 04-21-2024 00:39:38 @author: ripintheblue """
import logging
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import YahooDownload_Ticker_File, YahooDownload_Info_File
import pandas as pd
import time
import os
import seaborn as sns
sns.set()

import yfinance as yf
print('Reading %s' %YahooDownload_Ticker_File)
df0 = pd.read_csv(YahooDownload_Ticker_File)
Tickers = df0['Yahoo_Ticker']#[:5]#[[2]]

extended_info = {}
data_list = []
print('Starting ')
for ticker in Tickers:
    print('Getting info for %s' %ticker)
    ticker_data = {'Yahoo_Ticker': ticker}
    yf_data = yf.Ticker(ticker).info
    ticker_data.update(yf_data)
    data_list.append(ticker_data)

data_list = pd.DataFrame(data_list)
data_list = data_list.drop(['priceHint', 'previousClose', 'open',
       'dayLow', 'dayHigh', 'regularMarketPreviousClose', 'regularMarketOpen',
       'regularMarketDayLow', 'regularMarketDayHigh', 'fiftyTwoWeekLow',
       'fiftyTwoWeekHigh', 'fiftyDayAverage', 'twoHundredDayAverage',
       'symbol', 'underlyingSymbol','firstTradeDateEpochUtc','uuid',
       'trailingPegRatio', 'phone', 'longBusinessSummary',
       'volume', 'regularMarketVolume',
       'averageVolume', 'averageVolume10days', 'averageDailyVolume10Day',
       'bid', 'ask', 'bidSize', 'askSize', 'totalAssets', 'navPrice',
       'category', 'ytdReturn', 'beta3Year', 'fundFamily', 'fundInceptionDate',
       'legalType', 'threeYearAverageReturn', 'fiveYearAverageReturn',
       'trailingPE', 'yield', 'forwardPE', 'trailingAnnualDividendRate',
       'trailingAnnualDividendYield'
       ], axis = 1) # gmtOffSetMilliseconds is about timezones

print('Saving to %s' %YahooDownload_Info_File)
logging.info('Saving to %s' %YahooDownload_Info_File)
data_list = pd.merge(data_list,df0).set_index(('Ticker'))
data_list.to_csv(YahooDownload_Info_File)
script_end_log()
