""" Created on 11-30-2025 05:39:45 @author: ripintheblue """
import logging
# import fatwoman_log_setup
# from fatwoman_log_setup import script_end_log
import pandas as pd
import time
import os
from fatwoman_dir_setup import LLM_data_path, db_trades_name, db_trades, db_strategy_daily_returns_name, adhoc_fol

folder = os.path.join(LLM_data_path, 'Archive')

# read all the files that has "summarizer" in its name, recursively in folders, append into a dataframe with two columns: full file path, content
data = []
for root, dirs, files in os.walk(folder):
    for file in files:
        if "summarizer" in file:
            full_path = os.path.join(root, file)
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            data.append({'file_path': full_path, 'content': content})
dataframe = pd.DataFrame(data)
# create a column for the filename only
dataframe['file_name'] = dataframe['file_path'].apply(lambda x: os.path.basename(x))
# create a column for the last folder name only
dataframe['folder_name'] = dataframe['file_path'].apply(lambda x: os.path.basename(os.path.dirname(x)))
# create three new columns from the column "content" by extracting the values for "ticker", "tendency", "confidence" from the content which is in json format
import json
dataframe['ticker'] = dataframe['content'].apply(lambda x: json.loads(x).get('ticker', ''))
dataframe['tendency'] = dataframe['content'].apply(lambda x: json.loads(x).get('tendency', ''))
dataframe['confidence'] = dataframe['content'].apply(lambda x: json.loads(x).get('confidence', ''))

df2 = dataframe[['folder_name', 'ticker', 'tendency', 'confidence']]
df2.to_clipboard(index=False)

df2 = df2.copy()
df2['date'] = pd.to_datetime(df2['folder_name'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
df2['strategy'] = 'DAILYAPICALL'
df2.to_csv(os.path.join(adhoc_fol,'LLMS', 'DAILY_LLM_log_concat.csv'), index=False)

# %%
import sqlite3
with sqlite3.connect(db_trades) as conn:
    query = f"SELECT * FROM {db_trades_name}" 
    dfdb = pd.read_sql_query(query, conn)
    dfdb.sort_values(by='Date', inplace=True)

dfdb.to_clipboard(index=False) # database is corrupt, missing dates and etc..