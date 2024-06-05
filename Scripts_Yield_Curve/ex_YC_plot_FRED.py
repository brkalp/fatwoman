""" Created on 03-09-2024 05:11:28 @author: ripintheblue """
# pip install fredapi
from fredapi import Fred
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

yields = {}
dates = []
for maturity, series_id in series_ids.items():
    # Fetch the series and then take the last observation
    series_data = fred.get_series(series_id)
    last_observation_date = series_data.index[-1]
    dates.append(last_observation_date)
    yields[maturity] = series_data.iloc[-1]

# Assuming all series have the same last observation date, which should be checked
latest_date = dates[0].strftime('%Y-%m-%d') if dates else "Unknown Date"

plt.figure(figsize=(10, 6))
plt.plot(list(yields.keys()), list(yields.values()), marker='o')
plt.title(f'Today\'s U.S. Treasury Yield Curve - {latest_date}')
plt.xlabel('Maturity')
plt.ylabel('Yield (%)')
plt.grid(True)
plt.show()
