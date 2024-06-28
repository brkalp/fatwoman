""" Created on 06-26-2024 14:13:17 @author: ripintheblue """
import pandas as pd
import os
import numpy as np
from collections import Counter
import seaborn as sns
import matplotlib.pyplot as plt
from fatwoman_dir_setup import Total_data_file, adhoc_fol
sns.set()

# filename = 'C:\Data\yahoodownload\ZipFutureData\Total\Total.csv'
filename = Total_data_file
dfraw = pd.read_csv(filename)
dfraw['Date'] = pd.to_datetime(dfraw['Date'])
dfraw = dfraw.set_index('Date')

# Select assets and create portfolio
portfolio = dfraw[['LongTermBond','SP500']].copy().dropna()
portfolio.loc[:,'port'] = 0
weight_dict = {'LongTermBond':0.6,'SP500':0.4}
assets = list(weight_dict.keys())
for asset in weight_dict: portfolio.loc[:,'port'] = portfolio.loc[:,'port'] + dfraw.loc[:,asset] * weight_dict[asset] 
assets.append('port')

# Calculate Statistics
def calculate_stats(returns): # daily returns
    returns = returns.dropna()
    cumulative_returns = (1 + returns).cumprod()
    total_return = cumulative_returns.iloc[-1] - 1
    max_drawdown = (cumulative_returns.div(cumulative_returns.cummax()) - 1).min()
    years = (returns.index[-1] - returns.index[0]).days / 365.25 # last date - first date
    annual_avg_return = (1 + total_return) ** (1 / years) - 1
    Std_dev = returns.std()
    sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) # assuming risk free rate is 0
    return {
        'Total Return': total_return,
        'Annual Avg. Return': annual_avg_return,
        'Max Drawdown': max_drawdown,
        'Std Dev': Std_dev,
        'Sharpe Ratio': sharpe_ratio
    }

port_daily_rets = portfolio.pct_change()
total_results = pd.DataFrame()
q_results = pd.DataFrame()
y_results = pd.DataFrame()
for asset in assets:
    returns = port_daily_rets[asset]
    total_results[asset] = calculate_stats(returns)
    # Q
    df = pd.DataFrame(returns.resample('Q').apply(calculate_stats))
    df.index = [(str(idx.year) + ' Q' + str(idx.quarter)) for idx in df.index]
    df = df[asset].apply(pd.Series)
    df.columns = pd.MultiIndex.from_product([[asset], df.columns], names=['Asset', 'Statistic'])
    q_results = pd.concat([df,q_results], axis = 1)
    # Y
    df = pd.DataFrame(returns.resample('Y').apply(calculate_stats))
    df.index = [(str(idx.year)) for idx in df.index]
    df = df[asset].apply(pd.Series)
    df.columns = pd.MultiIndex.from_product([[asset], df.columns], names=['Asset', 'Statistic'])
    y_results = pd.concat([df,y_results], axis = 1)

os.chdir(adhoc_fol)
y_results.to_csv('Yearly_stats_tlt_vs_spy.csv')