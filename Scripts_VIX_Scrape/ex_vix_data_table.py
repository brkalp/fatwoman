""" Created on 07-23-2024 01:24:04 @author: ripintheblue """
import logging
import pandas as pd
import time
import os
import seaborn as sns
from fatwoman_dir_setup import CBOE_Scrape_Data_File, VIX_Scrape_folder
import ace_tools_open as tools
sns.set()

current_timestamp_format = '%d/%m/%Y' # excel 02/07/2024
# wanted_timestamp_format = '%Y-%m-%d'
df0 = pd.read_csv(CBOE_Scrape_Data_File)
df0['Timestamp'] = pd.to_datetime(df0['Timestamp'], format = current_timestamp_format)
df0.set_index('Timestamp', inplace=True)
result = df0.groupby([df0.index.date,'Maturity'])['Settlement'].std() # nan since data is cleaned and now is daily
# tools.display_dataframe_to_user(name="Random DataFrame", dataframe=df1)
# df0.to_clipboard()

dfvc = pd.read_csv(VIX_C_Scrape_Data_File)
dfvc['Timestamp'] = pd.to_datetime(dfvc['Timestamp'], format = current_timestamp_format)

# df1 = df0.pivot(index='Timestamp', columns ='Maturity', values='Settlement')

# df0['Settlement'].replace('-', '',inplace=True)
# df0['Settlement'] = pd.to_numeric(df0['Settlement'])

# df0 = pd.read_csv(CBOE_Scrape_Data_File)
# df0.to_csv(CBOE_Scrape_Data_File, index=False)
# excel_timestamp_format = '%d/%m/%Y %H:%M'
# df0['Timestamp'] = pd.to_datetime(df0['Timestamp'], format = excel_timestamp_format)