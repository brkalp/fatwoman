""" Created on 02-22-2024 15:45:32 @author: ripintheblue """
import fatwoman_log_setup
import logging
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import Optionchain_loc, Vol_Output_Folder, Optionchain_dtype_dict, Vol_all_folder, Vol_append_fol, get_vol_plot_dir
from fatwoman_dir_setup import Optionchain_dtype_dict, Vol_chain_tickers, Optionchain_date_cols
import pandas as pd
import time
import os
import glob
import yfinance as yf
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import matplotlib.image as mpimg
sns.set()

# Settings
tickers_to_plot = Vol_chain_tickers#[0:5]
L_x_mat = 3 # first x maturities
L_x_days = 5 # Last x days data

# IV limits to plot, distance from midpoint price
plot_IV_limits_dict = {
    'SPY':  {'high':2, 'low': 0.75},
    'TSLA': {'high':3, 'low': 0.5},
    '^VIX': {'high':5, 'low': 0.5},
    }
limit_default = {'high':2, 'low': 0.5}

# vol filter, data cleanup
default_vol_filter = 5
override_vol_filter_dict = {
    '^VIX':  1
    }

logging.info('Plotting: %s, Last days %s' %(tickers_to_plot,L_x_days))
Vol_all_folder = os.path.join(Vol_Output_Folder, 'Plots', 'all')
Vol_append_fol = os.path.join(Vol_Output_Folder, 'Plots')
ts_format = '%Y-%m-%d' # prints on title and some boolean checks
legend_ts_format = '%d'
Last_x_days_trade = 7
plotsize = (10, 6)

# big loop for tickers
for ticker_symbol in tickers_to_plot:
    # Get data
    data_save_loc_total = Optionchain_loc(ticker_symbol = ticker_symbol, db_type='Total')
    ticker_data = pd.read_csv(data_save_loc_total, dtype=Optionchain_dtype_dict, engine = 'python')
    for date_col in Optionchain_date_cols: ticker_data[date_col] = pd.to_datetime(ticker_data[date_col], format='mixed')
    ticker_data['lastTradeDate']


    # Filter Data
    top_three_timestamps = ticker_data['Timestamp'].sort_values().unique()[-L_x_days:] # take latest L_x_days days data per option
    ticker_data = ticker_data[ticker_data['Timestamp'].isin(top_three_timestamps)]
    ticker_data = ticker_data[ticker_data['impliedVolatility'] > 0.1]
    ticker_data = ticker_data[ticker_data['Expiration_Date'] > ticker_data['Timestamp']]
    ticker_data = ticker_data[ticker_data['lastTradeDate'] >= (pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=Last_x_days_trade))]
    # ticker_data['lastTradeDate'].apply(type).value_counts()
    ticker_data = ticker_data[ticker_data['volume'] >= override_vol_filter_dict.get(ticker_symbol,default_vol_filter)]
    iv_data = ticker_data[['contractSymbol', 'lastPrice', 'lastTradeDate', 'impliedVolatility','Timestamp','strike', 'Option_Type', 
        'Expiration_Date', 'inTheMoney']] #'volume'

    # Base Variables
    timestamp = ticker_data['Timestamp'].max().strftime(ts_format)
    
    # Second Loop for Maturities
    counter = 0
    selected_maturities = iv_data['Expiration_Date'].sort_values().unique()
    selected_maturities = selected_maturities[selected_maturities > datetime.now()]
    selected_maturities = selected_maturities[:L_x_mat] # filter DTE's here
    for maturity_date in selected_maturities: 
        print('Ticker: %5s, MaxTimestamp on file: %s, Counter, %s, Maturity %s' %(ticker_symbol, timestamp, counter, maturity_date))
        
        # Loop Variables
        dte = (maturity_date - datetime.now()).days
        counter = counter + 1
        save_loc = os.path.join(Vol_all_folder, ticker_symbol + '-' + str(counter)) # + '_' +str(vol) + '.jpg'
        
        # Prepare Data
        dfm = iv_data[iv_data['Expiration_Date'] == maturity_date] # dfm
        callflag = dfm['Option_Type']=='Call'
        inthemoneyflag = dfm['inTheMoney']
        maxiv = dfm[inthemoneyflag & callflag]['strike'].max()
        miniv = dfm[inthemoneyflag & (callflag == False)]['strike'].min()
        midpoint = (miniv + maxiv) / 2
        plot_limits = plot_IV_limits_dict.get(ticker_symbol,limit_default)
        low  = midpoint * plot_limits['low']
        high = midpoint * plot_limits['high']
        # dfm = dfm[inthemoneyflag]
        dfm = dfm[(dfm['strike'] > low) & (dfm['strike'] < high)]

        # Color map using timestamps
        unq_ts = dfm['Timestamp'].unique().strftime(ts_format)
        s_frac = 0.3  # start_fraction- Skip the first 30% of the color map
        color_map_calls = {ts:plt.get_cmap('Blues')(s_frac + (i / len(unq_ts)) * (1 - s_frac)) for i, ts in enumerate(unq_ts)}
        color_map_puts = {ts:plt.get_cmap('Reds')(s_frac + (i / len(unq_ts)) * (1 - s_frac)) for i, ts in enumerate(unq_ts)}

        # Plot in each loop
        legend_labels = {}
        plt.figure(figsize=plotsize)
        for option_type in ['Call','Put']:
            prev_iv_data = {}
            dfm_type = dfm[dfm['Option_Type'] == option_type]
            color_map = color_map_calls if option_type == 'Call' else color_map_puts
            if option_type == 'Call': color_map = color_map_calls
            if option_type == 'Put': color_map = color_map_puts
            for idx, row in dfm_type.iterrows():
                # Get Variables
                strike, iv, contractSymbol, iv_timestamp = [row[k] for k in ['strike', 'impliedVolatility', 'contractSymbol', 'Timestamp']]
                # Get Marker
                first_iv = contractSymbol not in prev_iv_data
                last_iv = timestamp == iv_timestamp.strftime(ts_format) # to make all non-last ones 'x'
                marker = '.' if first_iv or not last_iv or iv == prev_iv_data[contractSymbol] else '^' if iv > prev_iv_data[contractSymbol] else 'v'
                prev_iv_data[contractSymbol] = iv
                markersize = 7 if marker == '^' or marker == 'v' else 5
                # Set Legend Label and color
                label = ('%s %s' %(option_type[0], iv_timestamp.strftime(legend_ts_format)))
                color = color_map[iv_timestamp.strftime(ts_format)]
                if label not in legend_labels: legend_labels[label] = ('x', color)
                plt.plot(strike, iv, marker=marker, linestyle='none', color=color, label=label, markersize=markersize)
        handles = [plt.Line2D([], [], color=color, marker=marker, linestyle='none', markersize=10, label=label) for label, (marker, color) in legend_labels.items()]
        plt.legend(handles=handles, borderaxespad=1, framealpha=1, shadow=True, fancybox=True, loc="lower right")
        plt.axvline(midpoint, color='red', linestyle='--', linewidth=2, label='Midpoint %s' %midpoint)  # Highlighting the midpoint
        plt.title('%s at %s on %s - dte %s - Maturity %s' %(ticker_symbol, midpoint, timestamp, dte, maturity_date.strftime(ts_format)))
        plt.xlabel('Strike Price, assume ($)')
        plt.ylabel('Implied Volatility')
        # plt.yticks(y_ticks)
        plt.tight_layout()
        plt.savefig(save_loc)
        plt.close()

# Append Plots
print('Starting Append')
timestamp_today = datetime.now().strftime(ts_format)
for ticker_symbol in tickers_to_plot:
    # Find Plots
    search_pattern = os.path.join(Vol_all_folder, f'{ticker_symbol}*.png')
    png_files = glob.glob(search_pattern)
    
    # Append and save
    fig, axs = plt.subplots(len(png_files),1)
    for ax, img_path in zip(axs, png_files):
        # print('Reading %s' %img_path)
        # logging.info('Reading %s' %img_path)
        img = mpimg.imread(img_path)
        ax.imshow(img)
        ax.axis('off')  # Hide axes ticks

    plt.tight_layout()
    save_loc_main = get_vol_plot_dir(Vol_append_fol = Vol_append_fol, ticker_symbol= ticker_symbol)
    print('Saving %s' %save_loc_main)
    # logging.info('Saving %s' %save_loc_main)
    plt.savefig(save_loc_main, bbox_inches='tight', dpi=300)
    plt.close()

script_end_log()

    # vol = 0
    # vols = [0, 3, 5, 10]
    # for vol in vols:
    #     # vol = 5
    #     iv_data = 
    # 3[iv_data_raw['volume'] > vol]

    # y_ticks = [x / 100 for x in range(0, 450, 50)]  # IV

    # ticker_data = ticker_data [ticker_data['inTheMoney']]
    # ticker_data = ticker_data[ticker_data['volume'] > vol]
    
    # save_loc = os.path.join(Vol_Output_Folder, 'Plots',ticker_symbol + expiration_date ) # + '_' +str(vol) + '.jpg'
    
    # for date_col in Optionchain_date_cols: ticker_data[date_col] = pd.to_datetime(ticker_data[date_col], format='mixed')
    # print('Latest date in file is %s' %ticker_data['Timestamp'].max())
    
                
                # print(f"Contract name: {row['contractSymbol']}, CP: {option_type}, Strike: {strike}, IV: {iv}, timestamp: {iv_timestamp}, Previous IV: {prev_iv_data.get(strike, 'N/A')}, Marker: {marker}")


# ticker_symbol = 'NVDA'
# ticker_symbol = 'AAPL'
# ticker_symbol = 'SPY'
            # plt.plot(dfm_type['strike'], dfm_type['impliedVolatility'], marker='o', linestyle='none', label=f'%s %s' %(option_type, maturity_date))

                # first_iv_check = contractSymbol not in prev_iv_data
                # marker = 'x' if first_iv_check or iv == prev_iv_data[contractSymbol] else '^' if iv > prev_iv_data[contractSymbol] else 'v'
            
        #     for idx, row in option_data.iterrows():
        #         strike = row['strike']
        #         iv = row['impliedVolatility']
        #         marker = '^' if (strike in prev_iv_data and iv > prev_iv_data[strike]) else 'v'  # Up arrow for increase, down arrow for decrease
                
        #         # Color by timestamp
        #         timestamp_color = {1: 'blue', 2: 'green', 3: 'red'}  # Define your timestamp-color mapping as needed
        #         color = timestamp_color[timestamp]
                
        #         plt.plot(strike, iv, marker=marker, linestyle='none', color=color, label=f'{option_type} {expiration_date}')
        #         prev_iv_data[strike] = iv  # Update previous data for next comparison

        # # Midpoint and labels as before, modified to fit new structure if needed

        # plt.title(f'IV for {ticker_symbol} expiring on {expiration_date}')
        # plt.xlabel('Strike Price')
        # plt.ylabel('Implied Volatility')
        # plt.legend()
        # plt.show()