""" Created on 02-22-2024 15:45:32 @author: ripintheblue """
import logging
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import Optionchain_loc, Vol_Output_Folder, Optionchain_dtype_dict, Vol_chain_tickers, Optionchain_date_cols
import pandas as pd
import time
import os
import yfinance as yf
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
sns.set()

plot_limits = {
    'SPY':  {'high':2, 'low': 0.75},
    'TSLA': {'high':3, 'low': 0.5},
    '^VIX': {'high':5, 'low': 0.5},
    'DBC':  {'high':2, 'low': 0.5},
    'GSG':  {'high':2, 'low': 0.5},
    'AAPL': {'high':2, 'low': 0.5},
    'NVDA': {'high':2, 'low': 0.5},
    'TLT':  {'high':2, 'low': 0.5},
}

for ticker_symbol in Vol_chain_tickers:#[:1]:
    # Get data
    data_save_loc_total = Optionchain_loc(ticker_symbol = ticker_symbol, db_type='Latest')
    ticker_data = pd.read_csv(data_save_loc_total, dtype=Optionchain_dtype_dict)
    ticker_data['Expiration_Date'] = pd.to_datetime(ticker_data['Expiration_Date'], format='mixed')

    # Filter Data
    ticker_data = ticker_data [ticker_data['impliedVolatility'] > 0.1]
    iv_data_raw = ticker_data[['Expiration_Date', 'strike', 'Option_Type', 'impliedVolatility', 'inTheMoney']] #'volume'
    iv_data = iv_data_raw

    # Base Variables
    # y_ticks = [x / 100 for x in range(0, 450, 50)]  # IV
    if len(ticker_data['Timestamp'].unique())>1: print('Duplicate timestamp found'); logging.info('Duplicate timestamp found')
    timestamp = pd.to_datetime(ticker_data['Timestamp'], format='mixed').max().strftime('%Y%m%d')
    
    # Main loop
    counter = 0
    for expiration_date in iv_data['Expiration_Date'].unique()[:4]:#
        print('Ticker: %5s, Timestamp: %s, Counter, %s, Maturity %s' %(ticker_symbol, timestamp, counter, expiration_date))
        
        # Loop Variables
        dte = (expiration_date - datetime.now()).days
        counter = counter + 1
        save_loc = os.path.join(Vol_Output_Folder, 'Plots', ticker_symbol + timestamp + '-' + str(counter)) # + '_' +str(vol) + '.jpg'
        
        # Prepare Data
        current_expiration_data = iv_data[iv_data['Expiration_Date'] == expiration_date]
        midpoint = (
            current_expiration_data[current_expiration_data['inTheMoney'] & (current_expiration_data['Option_Type']=='Call')]['strike'].max() +
            current_expiration_data[current_expiration_data['inTheMoney'] & (current_expiration_data['Option_Type']=='Put')]['strike'].min()
        ) / 2
        low  = midpoint * plot_limits[ticker_symbol]['low']
        high = midpoint * plot_limits[ticker_symbol]['high']
        # print(midpoint)
        current_expiration_data = current_expiration_data[(current_expiration_data['strike'] > low) & (current_expiration_data['strike'] < high)]
        calls_data = current_expiration_data[current_expiration_data['Option_Type'] == 'Call']
        puts_data = current_expiration_data[current_expiration_data['Option_Type'] == 'Put']

        # Plotting
        plt.figure(figsize=(12, 8))
        plt.plot(calls_data['strike'], calls_data['impliedVolatility'], marker='o', linestyle='none', label=f'Calls {expiration_date}')
        plt.plot(puts_data['strike'], puts_data['impliedVolatility'], marker='x', linestyle='none', label=f'Puts {expiration_date}')
        plt.axvline(midpoint, color='red', linestyle='--', linewidth=2, label='Midpoint %s' %midpoint)  # Highlighting the midpoint
        plt.title('dte %s - %s Options IV by Strike with Maturity %s, ' %(dte, ticker_symbol, expiration_date))
        plt.xlabel('Strike Price, assume ($)')
        plt.ylabel('Implied Volatility')
        # plt.yticks(y_ticks)
        plt.legend()
        plt.savefig(save_loc)
        plt.close()
        # plt.show()

script_end_log()

    # vol = 0
    # vols = [0, 3, 5, 10]
    # for vol in vols:
    #     # vol = 5
    #     iv_data = 
    # 3[iv_data_raw['volume'] > vol]

    # ticker_data = ticker_data [ticker_data['inTheMoney']]
    # ticker_data = ticker_data[ticker_data['volume'] > vol]
    
    # save_loc = os.path.join(Vol_Output_Folder, 'Plots',ticker_symbol + expiration_date ) # + '_' +str(vol) + '.jpg'
    
    # for date_col in Optionchain_date_cols: ticker_data[date_col] = pd.to_datetime(ticker_data[date_col], format='mixed')
    # print('Latest date in file is %s' %ticker_data['Timestamp'].max())
    


# ticker_symbol = 'NVDA'
# ticker_symbol = 'AAPL'
# ticker_symbol = 'SPY'
