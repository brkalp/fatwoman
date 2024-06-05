""" Created on 02-22-2024 15:45:32 @author: ripintheblue """
import fatwoman_log_setup
from fatwoman_dir_setup import Vol_Output_Folder
import pandas as pd
import time
import os
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd

# ticker_symbol = 'NVDA'
# ticker_data = yf.Ticker(ticker_symbol)
# data_save_loc = os.path.join(Vol_Output_Folder, ticker_symbol + '_options.csv')

# options_data = [
#     pd.concat([
#         yf.Ticker(ticker_symbol).option_chain(date).calls.assign(Option_Type='Call', Expiration_Date=date),
#         yf.Ticker(ticker_symbol).option_chain(date).puts.assign(Option_Type='Put', Expiration_Date=date)
#         ])
#         for date in ticker_data.options ]

# combined_options_df = pd.concat(options_data).reset_index(drop=True)

# combined_options_df.to_csv(data_save_loc)


ticker_symbol = 'AAPL'
data_save_loc_total = Optionchain_loc(ticker_symbol = ticker_symbol, db_type='Total')
combined_options_df = pd.read_csv(data_save_loc_total)

iv_data = combined_options_df[['Expiration_Date', 'strike', 'Option_Type', 'impliedVolatility']]


# Assuming 'combined_options_df' is your DataFrame and it includes 'strike', 'impliedVolatility', and 'Expiration_Date'
# Convert 'Expiration_Date' to a numerical format (e.g., number of days from a reference point)
iv_data = combined_options_df[['Expiration_Date', 'strike', 'Option_Type', 'impliedVolatility']].copy()
iv_data['Expiration_Date'] = pd.to_datetime(iv_data['Expiration_Date'])
reference_date = pd.to_datetime('today')
iv_data['Days_to_Expiry'] = (iv_data['Expiration_Date'] - reference_date).dt.days

# Initialize a 3D plot
fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(111, projection='3d')

# Plot implied volatility for calls and puts, using Days_to_Expiry as the third axis
for option_type in ['Call', 'Put']:
    subset = iv_data[iv_data['Option_Type'] == option_type]
    ax.scatter(subset['strike'], subset['Days_to_Expiry'], subset['impliedVolatility'], label=option_type, s=20)

# Set labels and title
ax.set_xlabel('Strike Price ($)')
ax.set_ylabel('Days to Expiry')
ax.set_zlabel('Implied Volatility')
ax.set_title('NVIDIA Options Implied Volatility Landscape')

# Remove the legend to keep the plot clean
# ax.legend()  # Comment or remove this line to exclude the legend

plt.show()
