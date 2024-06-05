""" Created on 02-22-2024 15:45:32 @author: ripintheblue """
import fatwoman_log_setup
from fatwoman_dir_setup import ModelDownload_Output_Folder
import pandas as pd
import time
import os
import yfinance as yf
import pandas as pd
import seaborn as sns
sns.set()

ticker_symbol = 'NVDA'
ticker_data = yf.Ticker(ticker_symbol)

# selected_expiries = ticker_data.options
selected_expiries = ticker_data.options[0:3]

options_data = [
    pd.concat([
        yf.Ticker(ticker_symbol).option_chain(date).calls.assign(Option_Type='Call', Expiration_Date=date),
        yf.Ticker(ticker_symbol).option_chain(date).puts.assign(Option_Type='Put', Expiration_Date=date)
        ])
        for date in selected_expiries ]

combined_options_df = pd.concat(options_data).reset_index(drop=True)

iv_data = combined_options_df[['Expiration_Date', 'strike', 'Option_Type', 'impliedVolatility']]

plt.figure(figsize=(14, 8))

for expiration_date in iv_data['Expiration_Date'].unique():
    current_expiration_data = iv_data[iv_data['Expiration_Date'] == expiration_date]
    calls_data = current_expiration_data[current_expiration_data['Option_Type'] == 'Call']
    puts_data = current_expiration_data[current_expiration_data['Option_Type'] == 'Put']
    plt.plot(calls_data['strike'], calls_data['impliedVolatility'], marker='o', linestyle='none', label=f'Calls {expiration_date}')
    plt.plot(puts_data['strike'], puts_data['impliedVolatility'], marker='x', linestyle='none', label=f'Puts {expiration_date}')

plt.title('NVIDIA Options Implied Volatility by Strike Price')
plt.xlabel('Strike Price ($)')
plt.ylabel('Implied Volatility')
plt.legend()
plt.show()
