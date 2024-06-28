import pandas as pd
import os
import numpy as np
from collections import Counter
import seaborn as sns
import matplotlib.pyplot as plt
from fatwoman_dir_setup import VIX_CBOE_scrape_Total

sns.set()

# filename = 'C:\Data\yahoodownload\ZipFutureData\Total\Total.csv'
# F:\fatboy\Scripts_CBOE_Vix\Total
filename = VIX_CBOE_scrape_Total
dfraw = pd.read_csv(filename)['VIX'].drop_duplicates()
df_future_prices = dfraw.pivot(columns=['Futures'], index ='Trade Date', values = 'Settle')
Future_to_expiry_dict = {col:df_future_prices[col].dropna().index.max() for col in df_future_prices.columns}
Expiry_to_future_dict = {df_future_prices[col].dropna().index.max():col for col in df_future_prices.columns}
if max(pd.Series(Future_to_expiry_dict.values()).value_counts()) != 1: print('Multiple expiry error')
df_future_returns = df_future_prices.pct_change()

# form time series of "shortest-rollover futures"
df_shortest_future_returns = {}
df_shortest_future_prices = {}
for datecheck in df_future_prices.index:
    available_futures = pd.DataFrame(df_future_prices.loc[datecheck,:]).dropna()
    min_expiry = available_futures.index.map(Future_to_expiry_dict).min()
    min_expiry_future = Expiry_to_future_dict[min_expiry]
    if min_expiry_future is not np.nan:
        df_shortest_future_returns[datecheck] = -1 * df_future_returns.loc[datecheck,min_expiry_future]
        df_shortest_future_prices[datecheck] = df_future_prices.loc[datecheck,min_expiry_future]
    else:
        df_shortest_future_returns[datecheck] = 0
        df_shortest_future_prices[datecheck] = 0

df_future_prices.max().max() # 72.625
assume_max_vix = 80
assume_current_vix = 30
contract_size = assume_current_vix / assume_max_vix 
contract_sizes = [0,0.1,0.2,0.3,0.5,0.8,contract_size] # ,1,1.5
plt.figure(figsize=(15, 9)) 
df_overall = pd.DataFrame(); info_dict = {}
for size in contract_sizes:
    df_shortest_future_returns = df_shortest_future_returns
    df_Portfolio = pd.DataFrame({'daily_short_returns':df_shortest_future_returns}).dropna() * size
    df_Portfolio = df_Portfolio + 1
    df_Portfolio[size] = df_Portfolio['daily_short_returns'].cumprod()
    df_Portfolio[size].plot()
    df_overall[size] = df_Portfolio[size]
plt.legend(title='Size of portfolio')  # Add legend with a title
plt.xlabel('Time')  # Optionally add x-axis label
plt.ylabel('Cumulative Returns')  # Optionally add y-axis label
plt.title('Portfolio Cumulative Returns by Contract Size')  # Optionally add a title
plt.show()  # Display the plot


def calculate_stats(cumulative_returns):
    total_return = cumulative_returns.iloc[-1] / cumulative_returns.iloc[0] - 1
    first_date, last_date = cumulative_returns.index[0], cumulative_returns.index[-1]
    years = (pd.to_datetime(last_date) - pd.to_datetime(first_date)).days / 365.25
    annual_avg_return = (cumulative_returns.iloc[-1] / cumulative_returns.iloc[0]) ** (1 / years) - 1
    
    daily_returns = cumulative_returns.pct_change().dropna()
    drawdown = cumulative_returns.div(cumulative_returns.cummax()) - 1
    max_drawdown = drawdown.min()
    sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(252)
    
    return {
        'Total Return': total_return,
        'Annual Avg. Return': annual_avg_return,
        'Max Drawdown': max_drawdown,
        'Sharpe Ratio': sharpe_ratio
    }

overall_stats = calculate_stats(df_overall[0.5])




# dfraw = pd.read_csv(filename)
# df2 = dfraw.pivot(columns=['Expiry Month','Futures'], index ='Trade Date', values = 'Settle')
# df2 = df2.rename({col:df2[col].dropna().index.min() for col in df2.columns},axis=1) # replace column names with expiry of each future
# df2_diffs = df2.pct_change()

# # form strategy
# df3 = {}
# for datecheck in df2.index:
#     row = pd.DataFrame(df2.loc[datecheck,:])
#     smallest_future = row.dropna().index.min()
#     if smallest_future is not np.nan:
        
#         df3[datecheck] = -1 * df2_diffs.loc['2020-08-20',:].to_clipboard()
#     else:
#         df3[datecheck] = 0
# df4 = pd.DataFrame({'short_only':df3}).dropna()
# df4.to_clipboard()
# df4 = df4 + 1
# df4['Cumulative'] = df4['short_only'].cumprod()

# recent_changes = pivot_changes.iloc[-2:-1].dropna(axis=1)
# smallest_change_future = recent_changes.idxmin(axis=1)
# selected_value = pivot_changes.loc[recent_changes.index, smallest_change_future]

# impo

# # Selecting the smallest future change from the last two dates
# recent_changes = pivot_changes.iloc[-2:-1].dropna(axis=1)
# smallest_change_future = recent_changes.idxmin(axis=1)
# selected_value = pivot_changes.loc[recent_changes.index, smallest_change_future]

# Outputting the DataFrame with ratios
# print(df_ratios)

# firsttwocols = Expiries[:2]
# df3 = df2[firsttwocols].copy()
# for colindex in range(len(df2.columns)-1): #[:3]
#     # print(colindex, end = '')
#     firstcol = Expiries[colindex] 
#     secondcol= Expiries[colindex + 1]
#     colname = firstcol + '/' + secondcol
#     df3[colname] = ((df2[firstcol] / df2[secondcol]) - 1)
# df3 = df3.drop(firsttwocols, axis = 1)#[:3]
# df3.to_clipboard()
# These have negative trends
# So closer to maturity is closer to VIX, and lower, as it is riskier.
# Short the first and long the second at any given date
# startdates = [df2[col].dropna().index.min() for col in Expiries]
# enddates = [df2[col].dropna().index.max() for col in Expiries]
# short = {dateindex:dateindex if dateindex in enddates else 0 for dateindex in df2.index} # this is always the longest maturity
# # short = {dateindex:dateindex if dateindex in startdates else 0 for dateindex in df2.index} # this is always the longest maturity
# for i in range(len(short)-1):
#     key1 = list(short.keys())[i]
#     key2 = list(short.keys())[i-1]
#     if short[key1] == 0:
#         short[key1] = short[key2]


# dfshortonly = pd.concat([df2_diffs.loc[enddates[i]:enddates[i+1], startdates[i] ] for i in range(len(enddates)-1)[:1]])# index, future
# print(len(startdates),len(df2),len(dfshortonly))