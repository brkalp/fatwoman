""" Created on 07-14-2024 13:56:56 @author: ripintheblue """
#https://helda.helsinki.fi/server/api/core/bitstreams/0e2e2bc3-dd56-4117-a70e-6df43600a326/content
#https://media.licdn.com/dms/document/media/D561FAQFfJXAbAxweZQ/feedshare-document-pdf-analyzed/0/1718689555586?e=1721865600&v=beta&t=Jpo5dGTx80ZbLmyw945Wdqchay3TqY0MGHGhF6kdZVo
import logging
import pandas as pd
import time
import os
import seaborn as sns
from itables import show
import quantstats as qs
from fatwoman_dir_setup import Total_data_file, adhoc_fol, data_get
import numpy as np

qs.extend_pandas() # extends pandas 
os.chdir(adhoc_fol)


# load data and prep
dfc = pd.concat([data_get('VIX'), data_get('SP500')], axis=1)
dfc['VIX_ret'] = dfc['VIX'].pct_change()
dfc['SP500_ret'] = dfc['SP500'].pct_change()
dfc = dfc.dropna()

# generate signals
dfc['Vix_dir']      = dfc['VIX_ret'].apply(lambda x: 1 if x > 0 else 0)
dfc['sp500_dir']    = dfc['SP500_ret'].apply(lambda x: 1 if x > 0 else 0)
dfc['Vix_dir_roll']   = dfc['Vix_dir'].rolling(2).sum()
dfc['sp500_dir_roll'] = dfc['sp500_dir'].rolling(2).sum()
dfc = dfc.drop(['Vix_dir','sp500_dir', ], axis=1)
dfc['sum_to_signal'] = dfc['Vix_dir_roll'] + dfc['sp500_dir_roll']
dfc['signal'] = (dfc['sum_to_signal']  > 3).astype(int)
print("amount of signals %i" %(len(dfc[dfc['signal']==1])))
dfc['pos'] = dfc['signal'].shift(1) + dfc['signal'].shift(2) - dfc['signal'].shift(3) - dfc['signal'].shift(4)

# zoom in multiple signals
max_value = dfc['pos'].max()
min_value = dfc['pos'].min()
print('max pos %i, min pos %i' %(max_value, min_value))
print('max pos loc %s, min pos loc %s' % (dfc['pos'].idxmax(), dfc['pos'].idxmin()))
max_pos_indices = dfc[dfc['pos'] == max_value].index.tolist()
min_pos_indices = dfc[dfc['pos'] == min_value].index.tolist()
print('Max pos indices:', max_pos_indices)
print('Min pos indices:', min_pos_indices)

# calc pnl on sp500
dfc['500_pnl'] = dfc['SP500_ret'] * dfc['pos']
dfc['500_pnl'] = dfc['500_pnl'].fillna(0)
dfc['500_cpnl'] = dfc['500_pnl'].cumsum()
# dfc['500_cpnl'].plot()
# calc pnl on vix
dfc['VIX_pnl'] = dfc['VIX_ret'] * dfc['pos']
dfc['VIX_pnl'] = dfc['VIX_pnl'].fillna(0)
dfc['VIX_cpnl'] = dfc['VIX_pnl'].cumsum()
# dfc['VIX_cpnl'].plot()

has_infinity = np.isinf(dfc).any().any()
print("Contains infinite values:", has_infinity)

show(dfc)
stratname = 'long-short vix with sp500 and vix signals'
dfc.index = pd.to_datetime(dfc.index)
# if dfc.index.tz is None: dfc.index = dfc.index.tz_localize('UTC')
qs.reports.html(dfc['VIX_pnl'], benchmark=dfc['SP500_ret'], download_filename = '%s tearsheet.html' %stratname, output = '%s.html'%stratname, title = stratname)

# dfc['Vix_signal'] = (dfc['Vix_dir'].rolling(2).sum() > 2).astype(int)
# dfc['sp500_signal'] = (dfc['sp500_dir'].rolling(2).sum() > 2).astype(int)

# dfc['Vix_signal']   = dfc['Vix_dir_roll'].apply(lambda x: 1 if x > 2 else 0)
# dfc['sp500_signal'] = dfc['sp500_dir_roll'].apply(lambda x: 1 if x > 2 else 0)

# dfc["daily_return_direction"] = np.nan
# dfc.loc[dfc["VIX_ret"]>0,"daily_return_direction"] = 1
# dfc.loc[dfc["VIX_ret"]<0,"daily_return_direction"] = -1
