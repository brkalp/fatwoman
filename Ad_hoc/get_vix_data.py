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

Tickers = ['^VIX']
df0 = yf.download(Tickers, dt(2005,1,1))
df0.to_clipboard()