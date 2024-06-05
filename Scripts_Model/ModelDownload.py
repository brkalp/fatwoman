""" Created on 02-08-2024 03:18:57 @author: ripintheblue """
import fatwoman_log_setup 
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import ModelDownload_Output_Data
import logging
from datetime import date
import pandas as pd
import yfinance as yf
from datetime import datetime as dt
import socket
import os

# Output_Folder = r'\\192.168.0.28\fatwoman\15GB\Scripts_Model\Output_Folder\\' if socket.gethostname() == 'ripintheblue' else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Output_Folder') + '/'
#\\192.168.0.28\fatwoman\15GB\EOD_scripts

#STOCKS  = {'^GSPC':'SP500', '^DJI':'DowJones', '^IXIC':'Nasdaq', '^MID':'MidCap', '^SP600':'SmallCap'}# Stock indexes: Growth and value
#FOREIGN = {'XU100.IS':'BIST','^OMX':'OMX','^GDAXI':'DAX','^FCHI':'CAC','000001.SS':'Shangai','^N225':'NIKK','RTSI.ME':'RTSI','IEUR':'EU'}
#BONDS   = {'TLT':'LongTermBond','IEF':'TreasuryBond'} #,'^SP500BDT':'CorporateBonds','TIPS': 'Bonds'
#CURR    = {'GBP=X':'USDGBP','USDTRY=X':'USDTRY','DKK=X':'USDDKK', 'SEK=X':'USDSEK', 'EUR=X':'USDEUR','RUB=X':'USDRUB','JPY=X':'USDJPY', 'USDCNY=X':'USDCNY'} # Currencies
VOLS    = {'^VIX':'VIX', 'VXX':'VXX'}

TICKERS = {**VOLS}
# TICKERS = {**STOCKS, **FOREIGN, **BONDS, **CURR, **VOLS}
Tickers = list(TICKERS.keys())

df0 = pd.DataFrame(yf.download(Tickers, dt(1990,1,1))['Adj Close']).reindex(columns=list(TICKERS.keys())).rename(columns = TICKERS).round(9)

# print(yf.Ticker('aapl').news)

# Printing the data
print('Printing %s' % dt.now())
if any(df0.columns.duplicated()):
    print('Problem: duplicate column names!!! Quiting!')
    raise Exception("Stopping the notebook at this cell.")

#else:
#    for col in df0.columns:
#        printloc = Output_Folder + r'%s.csv'%col
#        print(printloc)
#        df0[col].to_csv(printloc)

logging.info('Saving to %s' %ModelDownload_Output_Data)
print('Saving to %s' %ModelDownload_Output_Data)
df0.to_csv(ModelDownload_Output_Data)

print('Printing Done')
# logging.info("Script %s Finished" %os.path.basename(__file__))
script_end_log()