""" Created on 11-30-2025 05:39:45 @author: ripintheblue """
import logging
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
import pandas as pd
import time
import os
from fatwoman_dir_setup import LLM_data_path, db_trades_name, db_trades, db_strategy_daily_returns_name

folder = os.path.join(LLM_data_path, 'Archive')

# read all the files that has "summarizer" in its name, recursively in folders, append into a dataframe with two columns: full file path, content
data = []
root, dirs, _ = next(os.walk(folder))
dirs.sort()
paths = [os.path.join(root, d) for d in dirs]

for path in paths:
    files = os.listdir(path)
    for file in files:
        if "summarizer" in file:
            full_path = os.path.join(path, file)
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
# dataframe = dataframe.sort_values(by='folder_name')
df2 = dataframe[['folder_name', 'ticker', 'tendency', 'confidence']]
df2.to_clipboard(index=False)

import sqlite3
with sqlite3.connect(db_trades) as conn:
    query = f"SELECT * FROM {db_trades_name}" 
    dfdb = pd.read_sql_query(query, conn)

dfdb.to_clipboard(index=False)

# try:
#     with sqlite3.connect(db_trades) as conn:
#         query = f"SELECT * FROM {db_trades_name}" 
#         df0 = pd.read_sql_query(query, conn)
