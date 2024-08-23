""" Created on 03-09-2024 05:11:28 @author: ripintheblue """
# pip install fredapi
import logging
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import YC_FRED_Data, YCFRED_Scrape_timestamp_format
from fredapi import Fred
from datetime import datetime as dt
import socket
import matplotlib
if socket.gethostname() != 'ripintheblue': matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from fatwoman_api_setup import FRED_Key
fred = Fred(api_key=FRED_Key)

# Series IDs for Treasury yields
series_ids = {
    '1M': 'DGS1MO',
    '3M': 'DGS3MO',
    '6M': 'DGS6MO',
    '1Y': 'DGS1',
    '2Y': 'DGS2',
    '3Y': 'DGS3',
    '5Y': 'DGS5',
    '7Y': 'DGS7',
    '10Y': 'DGS10',
    '20Y': 'DGS20',
    '30Y': 'DGS30'
}

df_yields = pd.DataFrame(columns=['Maturity', 'Rate', 'Maturity_Months'])
print('Starting Download')
logging.info('Starting Download')

for maturity, series_id in series_ids.items():
    series_data = fred.get_series(series_id)
    last_rate = series_data.iloc[-1]  # Fetch the last rate, ie the most recent date
    if maturity.endswith('M'):
        maturity_months = int(maturity[:-1])
    elif maturity.endswith('Y'):
        maturity_months = int(maturity[:-1]) * 12
    new_data = pd.DataFrame({'Maturity': [maturity], 'Rate': [last_rate], 'Maturity_Months': [maturity_months]})
    df_yields = pd.concat([df_yields, new_data], ignore_index=True)
df_yields['Maturity_Years'] = df_yields['Maturity_Months'] / 12

# Save to CSV
logging.info('Saving to %s' % YC_FRED_Data)
print('Saving to %s' % YC_FRED_Data)
df_yields['Timestamp'] = dt.now().strftime(YCFRED_Scrape_timestamp_format)
# df_yields.to_csv(YC_FRED_Data, index=False)
df_yields.to_csv(YC_FRED_Data, mode='a', sep=',', header=not os.path.exists(YC_FRED_Data), index=False)

script_end_log()



# to get historical data
# import pandas as pd
# from fredapi import Fred


# # Retrieve historical data for the 10-year Treasury yield
# series_id = 'DGS10'
# historical_data = fred.get_series(series_id)

# # Convert the data to a pandas DataFrame for further analysis
# df_historical = pd.DataFrame(historical_data, columns=['10Y Treasury Yield'])

# # Print the DataFrame
# print(df_historical)
