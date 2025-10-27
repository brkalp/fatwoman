""" Created on 10-26-2025 21:25:41 @author: ripintheblue """
import logging
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
import pandas as pd
import sqlite3

with sqlite3.connect(r'Z:\15GB\Scripts_LLM_trader\db\flow.db') as conn:
    query = "SELECT * FROM flow" 
    df = pd.read_sql_query("SELECT * FROM flow", conn)
    try:
        df['daily_return'] = (df['close'] - df['open'] ) / df['open']
        df.to_sql('flow', conn, if_exists='replace', index=False)
    except Exception as e:
        logging.error(f"Error calculating daily returns: {e}")

df2 = df[['date', 'daily_return']].copy().groupby('date')['daily_return'].sum().reset_index()

# # for date_today in df['date'].unique():
# #     print('date_today:', date_today)
# #     df_today = df[df['date'] == date_today].copy()
# #     print('len df_today:', len(df_today))
    
#     df_today['daily_return'] = (df_today['close'] - df_today['open'] ) / df_today['open']
    
#     # daily_return_sum = df_today['daily_return'].sum()
#     print(f"Date: {date_today}, Daily Return Sum: {daily_return_sum:.6f}")