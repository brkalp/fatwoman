""" Created on 11-30-2025 05:39:45 @author: ripintheblue """
import pandas as pd
import os
os.chdir(os.path.join(adhoc_fol, 'LLMS'))
# --- Load source files ---
df1 = pd.read_csv('cleaned_recs.csv', sep=';')                 # longeq, longall, short
df2 = pd.read_csv('DAILY_LLM_log_concat.csv')                  # source for daily_top5 + daily_sentiment

# --- cleaned_recs.csv: 3 strategies, side derived from strategy name ---
df1 = df1.rename(columns={'strategy': 'strategy_raw'})
df1['side'] = df1['strategy_raw'].map({'short': 'short', 'longeq': 'long', 'longall': 'long'})
df1['strategy'] = df1['strategy_raw']
df1['confidence'] = pd.NA
out1 = df1[['date', 'time', 'strategy', 'ticker', 'side', 'confidence', 'reasoning']]

# --- DAILY_LLM_log_concat.csv: split into daily_top5 and daily_sentiment ---
base = df2.copy()

top5 = base.copy()
top5['strategy'] = 'daily_top5'
top5['side'] = 'long'                                          # always long the picked tickers
top5['time'] = pd.NA
top5['reasoning'] = pd.NA
top5 = top5[['date', 'time', 'strategy', 'ticker', 'side', 'confidence', 'reasoning']]

sent = base.copy()
sent['strategy'] = 'daily_sentiment'
sent['side'] = sent['tendency'].map({'bullish': 'long', 'bearish': 'short', 'neutral': 'neutral'})
sent['time'] = pd.NA
sent['reasoning'] = pd.NA
sent = sent[['date', 'time', 'strategy', 'ticker', 'side', 'confidence', 'reasoning']]

# --- Merge all 5 strategies on shared columns ---
merged = pd.concat([out1, top5, sent], ignore_index=True)
merged['date'] = pd.to_datetime(merged['date']).dt.date
merged = merged.sort_values(['date', 'strategy', 'ticker']).reset_index(drop=True)

merged.to_csv('recs and daily merged.csv', sep=';', index=False)
print(merged['strategy'].value_counts())