""" Created on 02-08-2024 04:18:57 @author: ripintheblue """
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import YahooDownload_Output_Folder
import logging
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
import socket
import os

sns.set()
sns.set_style("darkgrid")

os.chdir(YahooDownload_Output_Folder)

df = pd.read_csv('Total_Data.csv').set_index('Date')['VIX']
df.index = pd.to_datetime(df.index)

# \\192.168.0.28\fatwoman\15GB\ModelScripts\Output_Folder

def generate_forecasts(dfx, forecast_steps):
    forecast_steps = 1
    p, d, q = 4, 1, 2
    model = ARIMA(dfx.values, order=(p, d, q))
    fit_model = model.fit()
    forecast = fit_model.forecast(steps=forecast_steps)
    # forecast_index = pd.date_range(start=dfx.index[-1], periods=forecast_steps + 1, inclusive='right')
    # forecast_index = pd.date_range(start=dfx.index[-1], periods=forecast_steps, closed='right')
    forecast_index = pd.date_range(start=dfx.index[-1] + pd.Timedelta(days=1), periods=forecast_steps)
    forecast = pd.Series(forecast, index = forecast_index)
    return forecast



forecasts = pd.Series(dtype='float64')
for i in range(-15,2):
    j = i - 1
    forecast_point = i
    available_data = j
    df2 = df1.iloc[:j] if not j == 0 else df1
    forecast_steps = 1
    forecasts = pd.concat([forecasts, generate_forecasts(df2, forecast_steps)])

# Plotting
plt.figure(figsize=(10, 6))
df1.plot(color='blue', label='Actual VIX')

# Ensure the forecast plotting aligns correctly with the actual data
# forecasts = forecasts.reindex(df1.index, method='nearest')  # Align forecasts with actual data index for plotting
forecasts.plot(color='red', marker='o', label='Forecasted VIX') #linestyle='-', 
plt.legend()
plt.show()



import matplotlib.pyplot as plt

# Assuming df1 (actual data) and forecasts are already defined

# Calculate model errors for dates where forecasts are available
# Align forecasts with the actual data for error calculation
# forecast_aligned = forecasts.reindex(df1.index, method='nearest')
model_errors = df1 - forecast_aligned

# Setup the figure and axes for subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

# Plotting the actual VIX and forecasted VIX on the first subplot
ax1.plot(df1.index, df1, color='blue', marker='o', linestyle='-', label='Actual VIX')
ax1.plot(forecasts.index, forecasts, 'ro', label='Forecasted VIX', linestyle='None')  # Only dots for forecasts
ax1.legend()
ax1.set_title('Actual vs Forecasted VIX')

# Plotting model errors on the second subplot
ax2.plot(model_errors.index, model_errors, color='purple', marker='o', linestyle='-', label='Model Errors')
ax2.axhline(y=0, color='black', linestyle='--')  # Add a horizontal line at 0 for reference
ax2.legend()
ax2.set_title('Model Errors')

plt.tight_layout()  # Adjust layout to not overlap
plt.show()

script_end_log()