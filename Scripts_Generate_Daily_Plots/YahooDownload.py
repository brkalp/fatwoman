""" Created on Wed Jan  1 21:40:55 2022 @author: ripintheblue """
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import YahooDownload_Output_File, YahooDownload_Ticker_File
import logging
from datetime import date
import pandas as pd
import yfinance as yf
from datetime import datetime as dt
import socket
import os

# YahooDownload_Output_Folder = r'\\192.168.0.28\fatwoman\15GB\EOD_scripts\Output_Folder\\' if socket.gethostname() == 'ripintheblue' else os.path.dirname(os.path.abspath(__file__)) + '//Output_Folder//'

VOLS    = {'^VIX':'VIX', 'GC=F':'Gold', 'SI=F':'Silver'} #, '^VVIX':'VVIX'
STOCKS  = {'^GSPC':'SP500', '^DJI':'DowJones', '^IXIC':'Nasdaq', '^MID':'MidCap', '^SP600':'SmallCap', 'ACWI':'Global',} #Stock indexes: Growth and value  'EEM ':'Emerging_Markets' // GSPC is the index and SPY is the ETF
BONDS   = {'TLT':'LongTermBond','IEF':'TreasuryBond'} #,'^SP500BDT':'CorporateBonds','TIPS': 'Bonds'
CMDTY   = {'^BCOM':'BBG Commodity', '^SPGSCI':'SP GSCI'} # also ETFs DBC and GSG
CURR    = {'GBP=X':'USDGBP','USDTRY=X':'USDTRY','DKK=X':'USDDKK', 'SEK=X':'USDSEK', 'EUR=X':'USDEUR','RUB=X':'USDRUB','JPY=X':'USDJPY', 'USDCNY=X':'USDCNY'} # Currencies
FOREIGN = {'^OMX':'OMX','XU100.IS':'BIST','IEUR':'EU','^GDAXI':'DAX','^N225':'NIKK','000001.SS':'Shangai',} # 'RTSI.ME':'RTSI', ,'^FCHI':'CAC'

TICKERS = {**VOLS}
TICKERS = {**VOLS, **STOCKS, **BONDS, **CMDTY, **CURR, **FOREIGN}
Tickers = list(TICKERS.keys())

# Ticker list
print('Saving Tickers to %s' %YahooDownload_Ticker_File[-30:])
logging.info('Saving Tickers to %s' %YahooDownload_Ticker_File[-30:])
df_Tickers = pd.DataFrame.from_dict({'Yahoo_Ticker': Tickers,'Ticker': list(TICKERS.values())})
df_Tickers.to_csv(YahooDownload_Ticker_File, index = None)

# Download
print('Downloading: %s' %Tickers)
# Tickers = ['^VIX']
df0 = yf.download(Tickers, dt(2005,1,1), auto_adjust=False)['Adj Close']
df1 = df0.reindex(columns=list(TICKERS.keys())).rename(columns = TICKERS).round(9)
# df0 = pd.DataFrame(yf.download(Tickers, dt(2023,1,1))['Adj Close']).reindex(columns=list(TICKERS.keys())).rename(columns = TICKERS).round(9)

print('Saving to %s' %YahooDownload_Output_File[-40:])
logging.info('Saving to %s' %YahooDownload_Output_File[-40:])

if any(df1.columns.duplicated()):
    print('Problem: duplicate column names!!! Quiting!')
    raise Exception("Stopping the notebook at this cell.")
df1.to_csv(YahooDownload_Output_File)  
print('Saving Done')
size_mb = os.path.getsize(YahooDownload_Output_File) / (1024 * 1024)
last_modified_time = dt.fromtimestamp(os.path.getmtime(YahooDownload_Output_File))
print('Size in MB %3.3f, Last modified: %s' %(size_mb,last_modified_time))
logging.info('Size in MB %3.3f, Last modified: %s'%(size_mb,last_modified_time))
#else:
#    for col in df1.columns:
#        printloc = YahooDownload_Output_Folder + r'%s.csv'%col
#        print(printloc)
#        df1[col].to_csv(printloc)
script_end_log()