""" Created on 02-22-2024 15:38:22 @author: ripintheblue """
import fatwoman_log_setup
from fatwoman_dir_setup import ModelDownload_Output_Folder
import pandas as pd
import os
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from scipy.optimize import minimize
from datetime import datetime

def black_scholes_call(S, K, T, r, sigma):
    d1 = (np.log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

def implied_volatility(option_price, S, K, T, r): # returns implied volatility
    objective_function = lambda sigma: (black_scholes_call(S, K, T, r, sigma) - option_price)**2
    result = minimize(objective_function, 0.2, bounds=[(0.01, 3)])
    return result.x[0]

ticker = 'NVDA'
data = yf.Ticker(ticker)

hist = data.history(period="1y")
expiry_date = '2024-05-15'
calls = data.option_chain(expiry_date).calls

# Assuming risk-free rate as 0.01 for simplification
r = 0.01
S = hist['Close'][-1]  # Current stock price

# Time to maturity
current_date = datetime.now()
expiry_date_dt = datetime.strptime(expiry_date, "%Y-%m-%d")
T = (expiry_date_dt - current_date).days / 365.0  # Time to maturity in years

# Calculate implied volatilities
ivs = [implied_volatility(mp, S, K, T, r) for mp, K in zip(calls['lastPrice'], calls['strike'])]

# Plotting
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

ax.scatter(calls['strike'], [T]*len(calls), ivs, c='r', marker='o')

ax.set_xlabel('Strike Price')
ax.set_ylabel('Time to Expiry')
ax.set_zlabel('Implied Volatility')

plt.show()
