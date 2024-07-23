""" Created on 07-23-2024 01:24:04 @author: ripintheblue """
import logging
import pandas as pd
import time
import os
import seaborn as sns
from fatwoman_dir_setup import CBOE_Scrape_Data_File, VIX_Scrape_folder
import ace_tools_open as tools

sns.set()
df0 = pd.read_csv(CBOE_Scrape_Data_File)
df0['Timestamp'] = pd.to_datetime(df0['Timestamp'])
df0['Settlement'].replace('-', '',inplace=True)
df0['Settlement'] = pd.to_numeric(df0['Settlement'])
df0.set_index('Timestamp', inplace=True)

df1 = df0.pivot(index='Timestamp', columns ='Maturity', values='Settlement')
tools.display_dataframe_to_user(name="Random DataFrame", dataframe=df1)
result = df0.groupby([df0.index.date,'Maturity'])['Settlement'].std()

df0.to_clipboard()