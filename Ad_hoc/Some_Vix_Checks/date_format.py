""" Created on 07-30-2024 01:07:26 @author: ripintheblue """
import pandas as pd
# download dir https://www.cboe.com/tradable_products/vix/vix_historical_data/
# https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv
filedir = r'F:\15GB\Ad_hoc\Some_Vix_Checks\CBOE_VIX_History (2).csv'
targetdir = r'F:\15GB\Ad_hoc\Some_Vix_Checks\CBOE_VIX_History_clean.csv'
df0 = pd.read_csv(filedir)
timestamp_format = '%m/%d/%Y'
df0['DATE'] = pd.to_datetime(df0['DATE'], format=timestamp_format) 
df0.to_csv(targetdir, index=False)
