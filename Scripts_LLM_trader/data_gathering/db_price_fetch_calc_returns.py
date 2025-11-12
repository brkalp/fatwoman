""" Created on 10-26-2025 21:25:41 @author: ripintheblue """
import logging

from datetime import datetime
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
import pandas as pd
import sqlite3
import yfinance as yf
from fatwoman_dir_setup import db_trades_name, db_trades, db_strategy_daily_returns_name

try:
    with sqlite3.connect(db_trades) as conn:
        query = f"SELECT * FROM {db_trades_name}" 
        df0 = pd.read_sql_query(query, conn)
        df0['Date'] = pd.to_datetime(df0['Date']).dt.date
        print('Fetched', len(df0), 'rows from database. ticker len:', len(df0['Ticker'].unique()))
        # %% Get price data from yfinance
        dfempty = df0[df0['Open'].isnull() | df0['Close'].isnull()]
        print('Fetched', len(dfempty), 'empty rows from db.  ticker len:', len(dfempty['Ticker'].unique()))
        tickers = df0['Ticker'].unique().tolist()
        # tickers = dfempty['Ticker'].unique().tolist()
        if tickers == []:
            logging.info(r"!!! No missing prices found in database. Exiting. !!!")
            print(r"!!! No missing prices found in database. Exiting. !!!")
            script_end_log()
            exit(0)
        prices = yf.download(tickers, start="2023-01-01", auto_adjust=True)
        print('Fetched', len(prices), 'rows from yfinance. ticker len:', len(prices.columns.get_level_values(1).unique()))
        # prices['date'] = pd.to_datetime(prices['date']).dt.date
        # prices = prices.round(2)#.rename(columns={'Adj Close': 'Close'})
        prices['Close'].fillna(method='ffill')
        # %% Calc pct changes daily
        pct_chg = prices['Close'].pct_change() * 100
        pct_chg.columns = [('Daily_return_pct', c) for c in pct_chg.columns]
        prices_and_returns = pd.concat([prices, pct_chg], axis=1)
        # %% fill dates to handle weekends for testing
        full_range = pd.date_range(prices_and_returns.index.min(),  datetime.today())  # business days is , freq='B'
        prices_and_returns = prices_and_returns.reindex(full_range).ffill()
        # %% reshape and merge into org dataframe
        dfpr = (
            prices_and_returns
            .swaplevel(0, 1, axis=1)
            .sort_index(axis=1)
            .stack(0)
            .reset_index()
            .rename(columns={'level_1': 'Ticker','level_0': 'Date'})
            .round(2).drop(['Volume'], axis=1)
            )
        dfpr['Date'] = pd.to_datetime(dfpr['Date']).dt.date
        # df1 = df0.merge(dfpr, on=['Date', 'Ticker'], how='left')
        df1 = df0.set_index(['Date', 'Ticker'])
        dfpr = dfpr.set_index(['Date', 'Ticker'])
        df1.update(dfpr); df1.reset_index(inplace = True)
        print('After merge, total rows in df1:', len(df1))
        # %% add intraday returns, round profit made
        df1['Intraday_Return'] = ((df1['Close'] - df1['Open']) / df1['Open']).round(4)
        df1['profit_made'] = (df1['Close'] - df1['Open']).round(2)
        # %% save back to db
        df1.to_sql(db_trades_name, conn, if_exists='replace', index=False)
        print('Updated database with prices, daily returns and intraday returns. rowsize:', len(df1),'colsize:', len(df1.columns))
except Exception as e:
    logging.error(f"Error calculating daily returns: {e}")
# %% save second db with strategy returns
try:
    print('Calculating strategy daily returns and saving to table %s...'%db_strategy_daily_returns_name)
    logging.info('Calculating strategy daily returns and saving to table %s...'%db_strategy_daily_returns_name)
    with sqlite3.connect(db_trades) as conn:
        query = f"SELECT * FROM {db_trades_name}" 
        df0 = pd.read_sql_query(query, conn)
        print('Fetched', len(df0), 'rows from database. flow_name len:', len(df0['flow_name'].unique()))
        df2 = df0[['Date','flow_name', 'Intraday_Return']].copy().groupby(['Date','flow_name'])['Intraday_Return'].sum().reset_index()
        df2.rename(columns={'Intraday_Return': 'Strategy_Daily_Return'}, inplace=True)
        df2['Strategy_Daily_Return'] = df2['Strategy_Daily_Return'].round(4)
        df2.to_sql(db_strategy_daily_returns_name, conn, if_exists='replace', index=False)
except Exception as e:
    logging.error(f"Error calculating str returns: {e}")

script_end_log()
#         # %% calculate intraday returns and append back to the df
#         # intraday = prices['Close'] / prices['Open'] - 1    # or prices['Close'] - prices['Open']
#         # intraday.columns = pd.MultiIndex.from_product([['Intraday Return'], intraday.columns])
#         # prices_and_returns = pd.concat([prices.round(2), intraday.round(4)], axis=1)
#         df1['profit_made'] = df1['Close'] - df1['Open']
#         df1['Intraday_Return'] = (df1['Close'] - df1['Open']) / df1['Open']
#         # %% done

        # one time clean up operations
        # df1 = df1.round(2)
        # df1.drop('daily_return', axis=1, inplace=True, errors='ignore')  # remove old daily_return if exists
        # df1['Daily_return_pct'] =''
        # df1['profit_made'] = df1['Close'] - df1['Open']
        # df1.to_sql(db_trades_name, conn, if_exists='replace', index=False)
# # merge: right values overwrite if they exist
# df_updated = df0.merge(px, left_on=['date', 'Ticker'], right_on=['Date', 'Ticker'], how='left')

# df0.rename(columns={'open': 'Open', 'close': 'Close', 'date': 'Date', 'ticker': 'Ticker','low': 'Low','high': 'High'}, inplace=True)  # typo fix
        # df = pd.concat(df_list)
        # df0.to_sql(db_trades_name, conn, if_exists='replace', index=False)
#  delete rows 
# df[4:7]
# df = df.drop(df.index[4:7])
# df.to_sql(db_trades_name, conn, if_exists='replace', index=False)

        # df0.replace({'DYNE': 'DYN'}, inplace=True)  # typo fix
        # df0.to_clipboard()
        # df0.to_sql(db_trades_name, conn, if_exists='replace', index=False)
# # for date_today in df['date'].unique():
# #     print('date_today:', date_today)
# #     df_today = df[df['date'] == date_today].copy()
# #     print('len df_today:', len(df_today))
    
#     df_today['daily_return'] = (df_today['close'] - df_today['open'] ) / df_today['open']
    
#     # daily_return_sum = df_today['daily_return'].sum()
#     print(f"Date: {date_today}, Daily Return Sum: {daily_return_sum:.6f}")
# %%

#     df2 = df[['date', 'daily_return']].copy().groupby('date')['daily_return'].sum().reset_index()
#         df_list = []
#         for ticker in tickers:
#             df_ticker = df1[df1['ticker'] == ticker].copy()
#             df_ticker['daily_return'] = (df_ticker['close'] - df_ticker['open']) / df_ticker['open']
#             df_list.append(df_ticker)