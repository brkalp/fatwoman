""" Created on 03-12-2024 15:58:01 @author: ripintheblue """
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import YahooDownload_Output_File, data_get, YahooDownload_Output_Folder
import pandas as pd
import time
import os
import numpy as np
import seaborn as sns
sns.set()

# VIX = pd.read_csv(YahooDownload_Output_File, index = 'Date')[['VIX']]
data = data_get('VIX')
data['Return'] = data['VIX'].pct_change()
data['State'] = np.where(data['Return'] > 0, 'Up', 'Down')

# Calculate transition probabilities
# transition_counts = data['State'].value_counts(normalize=True)
transition_matrix = pd.crosstab(data['State'], data['State'].shift(1), normalize='columns')

print("Transition Probabilities:")
print(transition_matrix)

# Forecasting with Markov Chain
def forecast_next_day(current_state):
    if current_state not in ['Up', 'Down']:
        raise ValueError("Invalid state. Choose 'Up' or 'Down'.")
    probabilities = transition_matrix[current_state]
    next_state = np.random.choice(probabilities.index, p=probabilities.values)
    return next_state

# Example usage
current_state = 'Up'
next_day_forecast = forecast_next_day(current_state)
print(f"Forecast for the next day given the market is {current_state} today: {next_day_forecast}")

script_end_log()