""" Created on 06-28-2024 14:13:09 @author: ripintheblue """
import logging
# import fatwoman_log_setup
# from fatwoman_log_setup import script_end_log
import pandas as pd
import time
import os
import seaborn as sns
from fatwoman_dir_setup import Total_data_file, adhoc_fol
import matplotlib.pyplot as plt
sns.set()
os.chdir(adhoc_fol)

filename = Total_data_file
dfraw = pd.read_csv(filename)
dfraw['Date'] = pd.to_datetime(dfraw['Date'])
dfraw = dfraw.set_index('Date')

# tickers = ['SP500', 'LongTermBond'] # 'LongTermBond', 'OMX',
tickers = ['SP500'] # 'LongTermBond', 'OMX',
df = dfraw[tickers].copy()
df = df[df.index.year > 2006]

# append vix strat
df_short_front_vix = pd.read_csv('Short_Front_VIX_0.2.csv')
date_col_name = df_short_front_vix.columns[0]
df_short_front_vix[date_col_name] = pd.to_datetime(df_short_front_vix[date_col_name])
df_short_front_vix = df_short_front_vix.set_index(date_col_name)
df_short_front_vix = df_short_front_vix.rename({'0.2':'vixfront_short_02'},axis=1)
df = pd.concat([df,df_short_front_vix],axis = 1)
df.to_clipboard()
tickers.append('vixfront_short_02')

# create a series of yearly returns
def get_yearly_returns(df, ticker):
    temp_df = df[[ticker]].copy()
    temp_df['Year'] = pd.to_datetime(temp_df.index.values).year
    temp_df['Daily_chg'] = temp_df[ticker].pct_change()
    if ticker == 'VIX': temp_df['Daily_chg'] = temp_df['Daily_chg'] * -0.1
    temp_df['Daily_Ret'] = temp_df['Daily_chg'] + 1
    temp_df['Y_cumprod'] = temp_df.groupby('Year')['Daily_Ret'].apply('cumprod')
    yearly_rets = temp_df[['Y_cumprod']].rename({'Y_cumprod':ticker},axis=1)
    return yearly_rets 

# create a dataframe of yearly returns
df_plot = pd.DataFrame(index = df.index)
for ticker in tickers:
    df_plot[ticker] = get_yearly_returns(df[[ticker]], ticker)
df_plot['Year'] = pd.to_datetime(df_plot.index.values).year
df_plot = df_plot.reset_index()

# plotting
plt.figure(figsize=(20, 8))
colors = sns.color_palette('tab10', n_colors=len(tickers))
ticker_colors = dict(zip(tickers, colors))
legend_list = []
for ticker in tickers:
    unique_years = df_plot['Year'].unique()
    for year in unique_years[::-1]:
        yearly_data = df_plot[df_plot['Year'] == year]
        if not yearly_data.isna().all()[ticker]: #yearly_data.empty: 
            ticker_label = ticker if ticker not in legend_list else ""
            if ticker not in legend_list: legend_list.append(ticker)
            sns.lineplot(data=yearly_data, x='index', y=ticker, label=ticker_label, color=ticker_colors[ticker])
            plt.axvline(x=yearly_data['index'].max(), color='gray', linestyle='--', linewidth=0.8)
plt.title(f'{tickers}')
plt.ylabel('Cumulative Returns')
plt.legend(title='Ticker', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
# plt.savefig('Yearly_perf_plot_SP500_vs_TLT.png')
# plt.savefig('Yearly_perf_plot_SP500_vs_short_front_vix.png')
plt.show()

# plt.figure(figsize=(20, 8))
# for ticker in tickers:  # Replace or adjust these ticker names based on your DataFrame
#     sns.lineplot(data=df_plot, x='Date', y=ticker, label=ticker)  # Creating a line plot for each ticker
# plt.title(f'{tickers}')
# plt.ylabel('Cumulative Returns')
# plt.legend(title='Year', bbox_to_anchor=(1.05, 1), loc='upper left')
# plt.show()


# # Plot using FacetGrid to create one subplot per year
# total_years = len(df_plot['Year'].drop_duplicates())
# g = sns.FacetGrid(df_plot, col="Year", col_wrap=total_years, height=4)
# g.map_dataframe(sns.lineplot, x='Year', y='SP500', label='SP500')
# g.map_dataframe(sns.lineplot, x='Year', y='LongTermBond', label='LongTermBond')
# g.add_legend()
# g.set_titles("Year: {col_name}")
# plt.show()
# Plotting each ticker