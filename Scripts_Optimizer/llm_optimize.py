""" Created on 10-31-2025 18:46:48 @author: ripintheblue """
import logging
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
import pandas as pd
import time
import os
import seaborn as sns
from fatwoman_dir_setup import LLM_data_path

import glob
import json
# import cvxpy as cp
import yfinance as yf
import numpy as np
files = glob.glob(os.path.join(LLM_data_path, "*summ*.txt"))

rows = []
for file in files:
    with open(file, "r") as f:
        data = json.loads(f.read())
        rows.append(data)
df = pd.DataFrame(rows)
if df.empty: raise ValueError("No *summ*.txt files found in LLM_data_path")

tickers = df['ticker'].unique().tolist()
data = yf.download(tickers, start="2022-01-01", auto_adjust=True)
data = data['Close'].dropna(how='all')
rets = data.pct_change().dropna()

mu      = rets.mean() * 252
Sigma   = rets.cov()  * 252

def mv_opt(mu, Sigma, target_ret):
    invS = np.linalg.pinv(Sigma.values)
    ones = np.ones(len(mu))

    A = ones @ invS @ ones
    B = ones @ invS @ mu.values
    C = mu.values @ invS @ mu.values
    D = A*C - B**2

    lam = (C - B*target_ret) / D
    gam = (A*target_ret - B) / D
    w = lam * (invS @ ones) + gam * (invS @ mu.values)
    return pd.Series(w, index=mu.index)

target_ret = mu.mean()
w = mv_opt(mu, Sigma, target_ret)
print(w, w.sum())

script_end_log()