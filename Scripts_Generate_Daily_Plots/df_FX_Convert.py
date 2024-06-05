""" Created on 04-21-2024 01:19:43 @author: ripintheblue """
import logging
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import YahooDownload_Info_File, YahooDownload_Output_File, YahooDownload_Outputs_SEK
import pandas as pd
import time
import os
import seaborn as sns
sns.set()

print('Reading %s'%YahooDownload_Output_File)
logging.info('Reading %s'%YahooDownload_Output_File)
df0 = pd.read_csv(YahooDownload_Output_File)
df0['Date'] = pd.to_datetime(df0['Date'])
df0 = df0.set_index('Date')

yf_Info = pd.read_csv(YahooDownload_Info_File)[[
    'Ticker',
    'Yahoo_Ticker',
    'currency',
    'quoteType',
    ]]
currencies = yf_Info[yf_Info['quoteType'] == 'CURRENCY']

home_currency = 'SEK'
home_currency_ticker = currencies[currencies['currency'] == home_currency]['Ticker']
home_currency_df = df0[home_currency_ticker]

# setting up FX history
# could use the yfinance data, but unclear which method is better
# Timing Differences: Exchange rates can fluctuate frequently due to market dynamics. Small timing differences in the data retrieval can lead to variations.
# Market Depth and Liquidity: Currency pairs like USD/SEK and GBP/USD might have different trading volumes and liquidity compared to a less commonly traded pair like SEK/GBP. 
print('Setting up new FX time series')
df_fx = pd.DataFrame(index = df0.index)
for index, (currency_ticker, currency_name) in currencies[['Ticker', 'currency']].iterrows():
    if currency_name == 'SEK': currency_name = 'USD'
    foreign_to_home = currency_name + home_currency
    print(' - %6s - '%foreign_to_home)
    if currency_name != 'USD':
       df_fx[foreign_to_home] = home_currency_df['USDSEK'] / df0[currency_ticker]
    else:
       df_fx[foreign_to_home] = home_currency_df['USDSEK']
df_fx['SEKSEK'] = 1
default_fx_dates = df_fx.index
complete_fx_dates = pd.date_range(min(default_fx_dates), max(default_fx_dates), freq='D')
df_fx = df_fx.reindex(complete_fx_dates)
df_fx = df_fx.interpolate()

print('Starting Conversion of time series')
# logging.info('Starting Conversion of time series')
df1 = pd.DataFrame()
df2 = pd.DataFrame()
for ticker in df0.columns:
    print('%15s' %(ticker), end = '')
    # logging.info('Will convert: %15s' %(ticker))
    df1[ticker] = df0[ticker]
    ticker_info_row = yf_Info[yf_Info['Ticker'] == ticker]
    currency_ticker = ticker_info_row['currency'].values[0]
    target_ticker = currency_ticker + home_currency
    print(':%4s mapped to %s' %(currency_ticker,target_ticker))
    df2[ticker] = (df1[ticker] * df_fx[target_ticker]).dropna().round(4)
df2.index.name = 'Date'

print('Saving to %s' %YahooDownload_Outputs_SEK)
logging.info('Saving to %s' %YahooDownload_Outputs_SEK)
df2.to_csv(YahooDownload_Outputs_SEK)
script_end_log()