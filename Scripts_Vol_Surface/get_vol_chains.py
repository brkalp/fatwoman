""" Created on 05-15-2024 18:41:04 @author: ripintheblue """
import logging
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import Vol_Output_Folder, Optionchain_loc, Optionchain_dtype_dict, Optionchain_date_cols, Vol_chain_tickers
import pandas as pd
import time
import os
import seaborn as sns
import yfinance as yf
import argparse

if __name__ == "__main__":
    print('Starting %s'%Vol_chain_tickers)
    logging.info('Starting %s'%Vol_chain_tickers)
    for ticker_symbol in Vol_chain_tickers:
        print('Starting %s' %ticker_symbol)
        # logging.info('Starting %s' %ticker_symbol)
        ticker_data = yf.Ticker(ticker_symbol)
        options_data = [ pd.concat([
                yf.Ticker(ticker_symbol).option_chain(date).calls.assign(Option_Type='Call', Expiration_Date=date),
                yf.Ticker(ticker_symbol).option_chain(date).puts.assign(Option_Type='Put', Expiration_Date=date)
                ]) for date in ticker_data.options
                ]
        print('Download Done for %s' %ticker_symbol)
        # logging.info('Download Done for %s' %ticker_symbol)
        date_today = time.strftime("%d/%m/%Y")
        combined_options_df = pd.concat(options_data).reset_index(drop=True).assign(Timestamp=date_today)
        # for date_col in Optionchain_date_cols: combined_options_df[date_col] = pd.to_datetime(combined_options_df[date_col], format='mixed').dt.strftime('%d/%m/%Y')
        combined_options_df['Expiration_Date'] = pd.to_datetime(combined_options_df['Expiration_Date']).dt.strftime('%d/%m/%Y')
        df_len = len(combined_options_df)

        # Latest, to csv
        data_save_loc = Optionchain_loc(ticker_symbol = ticker_symbol, db_type='Latest') # os.path.join(Vol_Output_Folder, 'Latest_' + ticker_symbol + '_OptionsChain.csv')
        # logging.info('Saving %4i to %s' %(df_len, data_save_loc))
        print('Saving %4i to %s' %(df_len, data_save_loc))
        combined_options_df.to_csv(data_save_loc, index=False)

        # Total
        data_save_loc_total = Optionchain_loc(ticker_symbol = ticker_symbol, db_type='Total') # os.path.join(Vol_Output_Folder, 'Total_' + ticker_symbol + '_OptionsChain.csv')
        
        # Check if it is a new ticker
        try:  
            tail_total_header = pd.read_csv(data_save_loc_total, nrows=0, dtype=Optionchain_dtype_dict, parse_dates=Optionchain_date_cols)
        except FileNotFoundError as e:
            logging.info('New ticker at %s' %(data_save_loc_total))
            print('New ticker at %s' %(data_save_loc_total))
            combined_options_df.to_csv(data_save_loc_total, index=False)
            tail_total_header = pd.read_csv(data_save_loc_total, nrows=0, dtype=Optionchain_dtype_dict, parse_dates=Optionchain_date_cols)

        # Check last rows to skip duplicate entries
        total_rows = sum(1 for _ in open(data_save_loc_total)) - 1
        skip_rows = max(0, total_rows - df_len)
        tail_total = pd.read_csv(data_save_loc_total, skiprows = skip_rows, engine='python')
        tail_total.columns = tail_total_header.columns

        # printing df: do not append to total if timestamp has duplicate dates
        duplicate_rows = date_today in tail_total['Timestamp'].drop_duplicates().to_string()
        if duplicate_rows:
            logging.info('Skipping Duplicate date at %s' %(data_save_loc_total))
            print('Skipping, Duplicate date at %s' %(data_save_loc_total))
        else: 
            # logging.info('Saving %4i to %s' %(df_len, data_save_loc_total))
            print('Saving %4i to %s' %(df_len, data_save_loc_total))
            combined_options_df.to_csv(data_save_loc_total, mode='a', header=False, index=False)
    script_end_log()

# for column, dtype in dtype_dict.items(): tail_total[column] = tail_total[column].astype(dtype)



# def parse_arguments():
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--ticker", action="store_true")
    # return parser.parse_args()
# args = parse_arguments()
# if args.ticker:
#     for ticker_symbol in ticker_list:



    # date_cols = ['lastTradeDate', 'Expiration_Date', 'Timestamp']
    
    # dtype_dict = {
    #     'contractSymbol': 'category',
    #     'strike': float,
    #     'lastPrice': float,
    #     'bid': float,
    #     'ask': float,
    #     'change': float,
    #     'percentChange': float,
    #     'volume': 'Int64', #int,
    #     'openInterest': 'Int64', #int,
    #     'impliedVolatility': float,
    #     'inTheMoney': bool,
    #     'contractSize': 'category',
    #     'currency': 'category',
    #     'Option_Type': 'category'
    # }

    # Vol_chain_tickers = [
    #     'AAPL',
    #     'NVDA',
    #     'SPY',
    #     'TSLA',
    #     'TLT',
    #     '^VIX',
    #     'DBC', # Invesco DB Commodity Index Tracking Fund
    #     'GSG' # S&P GSCI
    #     ]  #'^GSPC' 'EUR=X','USDTRY=X', 'SEK=X'  and GSG