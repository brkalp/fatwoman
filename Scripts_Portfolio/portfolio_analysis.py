""" Created on 04-20-2024 02:14:58 @author: ripintheblue """
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import YahooDownload_Output_File, portfolio_Plot
import pandas as pd
import seaborn as sns
sns.set()
import pandas as pd
import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt

# Fix max drawdown
# add gold and maybe oil as natural tail-risk hedges

# Double check sharpe calculation
# Add p500 Vix to the calculations as it is a tradable instrument
# aim of the exercise is to build a portfolio with good statistical metrics but good spare % in gold or bonds for liquidity


def sharpe(weights):
    portfolio_ret = np.dot(weights, mean_rets)
    portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    return [portfolio_ret, portfolio_vol]

def objective(weights):
    portfolio_ret, portfolio_vol = sharpe(weights)
    return -portfolio_ret / portfolio_vol  # Minimizing negative Sharpe ratio maximizes the positive Sharpe ratio

# INPUT = YahooDownload_Output_File
INPUT = YahooDownload_Outputs_SEK
df0 = pd.read_csv(INPUT)
df0['Date'] = pd.to_datetime(df0['Date'])
df0 = df0.reset_index(drop = True).set_index('Date')
# for col in df0.columns: print('%20s: %s' %(col, df0[col].first_valid_index()))
df0 = df0.drop([
    'VXX', 'OMX', 'EU', # Bad data
    'VIX', 'USDRUB', # Not Tradable
    ], axis = 1)
df0 = df0.reset_index()

start_y, end_y = 2007, 2024
pairs = [(year, year+1) for year in range(start_y, end_y,2)]
pairs.insert(0, (start_y, end_y))
loop_lenght = len(pairs)

# Setting up the figure and subplots
horizontal_size_per_pair = 10; hor_size = horizontal_size_per_pair * loop_lenght
Vertical_size_per_plot = 6; Number_of_plots = 5; ver_size =  Vertical_size_per_plot * Number_of_plots
fig, axs = plt.subplots(Number_of_plots, loop_lenght, figsize=(hor_size , ver_size))  # 4x1 grid of subplots, each of len 10, 24

# Starting loop
for index, (start, end) in enumerate(pairs):
    # Slicing base df
    print(f"Iteration {index}: Start year = {start}, End year = {end}", end = '  ')
    start_index = df0[df0['Date'].astype('str').str.contains(str(start))].index[0]
    end_index   = df0[df0['Date'].astype('str').str.contains(str(end))].index[-1]
    df1 = df0[start_index:end_index].reset_index(drop = True).set_index('Date')
    # Filling gaps and cleaning
    df1 = df1.interpolate().dropna()
    # Preparing basic metrics
    df2 = df1.pct_change()
    mean_rets = df2.mean()
    ticker_vol = df2.std()
    tick_sharpe = mean_rets / ticker_vol
    cov_matrix = df2.cov()
    num_assets = len(list(df2.columns))
    # df2.corr()
    # mean_rets.sort_values()

    # max drawdowns
    cumulative_returns = (1 + df2).cumprod()
    running_max = cumulative_returns.cummax()
    drawdowns = (cumulative_returns - running_max) / running_max
    max_drawdown = drawdowns.min()

    opt_results = minimize(
                        objective,
                        num_assets * [1. / num_assets], #init_guess is equal portfolio
                        method = 'SLSQP',
                        bounds = tuple((0, 1) for asset in range(num_assets)),
                        # bounds = tuple((-1, 1) for asset in range(num_assets)),
                        constraints = ({'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1})
                        )
    opt_weights = opt_results.x
    opt_ret, opt_vol = sharpe(opt_weights)
    opt_sharpe = opt_ret / opt_vol
    print('Sharpe: %5.5f, Ret: %3.5f, Vol: %3.5f' %(opt_sharpe, opt_ret, opt_vol))

    # Appending opt portfolio for plotting
    mean_rets['Opt. Port'] = opt_ret
    ticker_vol['Opt. Port'] = opt_vol
    tick_sharpe['Opt. Port'] = opt_sharpe
    max_drawdown['Opt. Port'] = 0
    tickers = list(mean_rets.index)
    opt_weights_2 = np.append(opt_weights, [0])

    # Plot 1: Expected returns per ticker
    axs[0,index].bar(mean_rets.index, mean_rets.values, color='blue')
    axs[0,index].set_xlabel('')
    axs[0,index].set_ylabel('Mean returns (%)')
    axs[0,index].set_title('%s and %s Mean returns per ticker' %(start, end))
    axs[0,index].tick_params(axis='x', rotation=90)
    axs[0,index].set_ylim(-0.0025, 0.002)

    # Plot 2: Volatility per ticker
    axs[1,index].bar(tickers, ticker_vol, color='blue')
    axs[1,index].set_xlabel('')
    axs[1,index].set_ylabel('Volatility per ticker')
    axs[1,index].set_title('Volatility per ticker')
    axs[1,index].tick_params(axis='x', rotation=90)
    axs[1,index].set_ylim(0, 0.035)

    # Plot 3: Sharpe ratios per ticker
    axs[2,index].bar(tickers, tick_sharpe, color='blue')
    axs[2,index].set_xlabel('')
    axs[2,index].set_ylabel('Sharpe ratios')
    axs[2,index].set_title('Sharpe ratios per ticker')
    axs[2,index].tick_params(axis='x', rotation=90)
    axs[2,index].set_ylim(-0.2, 0.2)

    # Plot 4: Ticker Weights Distribution in optimized portfolio
    axs[3,index].bar(tickers, max_drawdown, color='blue')
    axs[3,index].set_xlabel('Ticker Symbol')
    axs[3,index].set_ylabel('Max Drawdown From Top (%)')
    axs[3,index].set_title('Max Drawdown From Top (%)')
    axs[3,index].tick_params(axis='x', rotation=90)
    axs[3,index].set_ylim(-1, 0)

    # Plot 5: Ticker Weights Distribution in optimized portfolio
    axs[4,index].bar(tickers, opt_weights_2, color='blue')
    axs[4,index].set_xlabel('Ticker Symbol')
    axs[4,index].set_ylabel('Weight (%)')
    axs[4,index].set_title('Ticker Weights Distribution in optimized portfolio')
    axs[4,index].tick_params(axis='x', rotation=90)
    

plt.tight_layout()
print('Saving to %s' %portfolio_Plot)
plt.savefig(portfolio_Plot)