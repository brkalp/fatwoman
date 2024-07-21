""" Created on 02-22-2024 01:08:09 @author: ripintheblue """
import os
import socket
# import fatwoman_log_setup
import pandas as pd
import time
import os

# %reset -f
# import importlib
# import fatwoman_dir_setup
# importlib.reload(fatwoman_dir_setup)

# Change work_dir accordingly, where 15GB is location with scripts and fatboy is the data loc
# Determine if running on specific platform
# is_platform_pc = socket.gethostname() == 'ripintheblue'
remoteIP = r'F:\\'# remoteIP = r'\\10.0.1.6\\'
work_dir = remoteIP
is_platform_pc = (socket.gethostname() == 'fatwoman') is False
fatwoman_base_path = work_dir + '15GB'   if is_platform_pc else r'/media/fatwoman/15GB'
fatwoman_data_path = work_dir + 'fatboy' if is_platform_pc else r'/media/fatwoman/fatboy'
fatwoman_log_path = os.path.join(fatwoman_data_path, 'logs')

# Portfolio
portfolio_folder = os.path.join(fatwoman_data_path, 'Scripts_Portfolio')
portfolio_Plot  = os.path.join(portfolio_folder, 'Portfolio_loc.png')

# CBOE manual dump
VIX_CBOE_scrape_Total = os.path.join(fatwoman_data_path, 'Scripts_CBOE_Vix', 'Total','Total.csv')

# Daily downloads
YahooDownload_Output_Folder = os.path.join(fatwoman_data_path, 'Scripts_Generate_Daily_Plots')
YahooDownload_Output_File   = os.path.join(YahooDownload_Output_Folder, 'Daily_yahoo_data.csv')
YahooDownload_Ticker_File   = os.path.join(YahooDownload_Output_Folder, 'Tickers.csv')
YahooDownload_Info_File     = os.path.join(YahooDownload_Output_Folder, 'Tickers_and_info.csv')
YahooDownload_Outputs_SEK   = os.path.join(YahooDownload_Output_Folder, 'Daily_yahoo_data_in_SEK.csv')
YahooPlotter_Output_File    = os.path.join(YahooDownload_Output_Folder, 'Daily_yahoo_plot.html')
Total_data_file = YahooDownload_Output_File

# Data Feeds - Scape - Test location
Data_Feed_folder        = os.path.join(fatwoman_base_path, 'Scripts_Data_Feeds')
CBOE_Scrape_Data_File   = os.path.join(Data_Feed_folder, 'CBOE_VIX.csv')
VIX_C_Scrape_Data_File  = os.path.join(Data_Feed_folder, 'Central_VIX.csv')

# Yield Curve
YC_Scripts_Folder   = os.path.join(fatwoman_base_path, 'Scripts_Yield_Curve')
YC_Output_Folder    = os.path.join(fatwoman_data_path, 'Scripts_Yield_Curve')
YC_FRED_Data        = os.path.join(YC_Output_Folder, 'YC_FRED.csv')
YC_Scipy_Plot       = os.path.join(YC_Output_Folder, 'YC_Scipy_Plot.png')
YC_Quantlib_Plot    = os.path.join(YC_Output_Folder, 'YC_Quantlib_Plot.png')
YC_Appended_Plot    = os.path.join(YC_Output_Folder, 'YC_Appended_Plot.png')

# Volatility Surface
Vol_Scripts_Folder = os.path.join(fatwoman_base_path, 'Scripts_Vol_Surface')
Vol_Output_Folder = os.path.join(fatwoman_data_path, 'Scripts_Vol_Surface')

def Optionchain_loc(ticker_symbol = 'AAPL', db_type = 'Latest'):   
    if db_type == 'Latest':
        return os.path.join(Vol_Output_Folder, 'Latest_' + ticker_symbol + '_OptionsChain.csv')
    if db_type == 'Total': 
        return os.path.join(Vol_Output_Folder, 'Total_' + ticker_symbol + '_OptionsChain.csv')

Optionchain_date_cols = ['lastTradeDate', 'Expiration_Date', 'Timestamp']
Optionchain_dtype_dict = {
    'contractSymbol': 'category',
    'strike': float,
    'lastPrice': float,
    'bid': float,
    'ask': float,
    'change': float,
    'percentChange': float,
    'volume': 'Int64', #int,
    'openInterest': 'Int64', #int,
    'impliedVolatility': float,
    'inTheMoney': bool,
    'contractSize': 'category',
    'currency': 'category',
    'Option_Type': 'category'
}

Vol_chain_tickers = [
    'GME',
    'AAPL',
    'NVDA',
    'SPY',
    'TSLA',
    'TLT',
    '^VIX',
    # 'DBC', # Invesco DB Commodity Index Tracking Fund
    # 'GSG' # S&P GSCI
    ]  #'^GSPC' 'EUR=X','USDTRY=X', 'SEK=X'  and GSG
    
def Optionchain_get(ticker_symbol = 'AAPL', db_type = 'Latest'):
    Opt_data_loc = Optionchain_loc(ticker_symbol = ticker_symbol, db_type = db_type)
    Optchain_data = pd.read_csv(Opt_data_loc, dtype = Optionchain_dtype_dict, parse_dates = Optionchain_date_cols)
    return Optchain_data

Vol_all_folder = os.path.join(Vol_Output_Folder, 'Plots', 'all')
Vol_append_fol = os.path.join(Vol_Output_Folder, 'Plots')
def get_vol_plot_dir(ticker_symbol, Vol_append_fol=Vol_append_fol):
    return os.path.join(Vol_append_fol, ticker_symbol + '.png')

# adhoc folder
adhoc_fol = os.path.join(fatwoman_base_path, 'Ad_hoc')

# binance Orderbook saver
binance_Orderbook_Output_Folder = os.path.join(fatwoman_data_path, 'Scripts_Binance')
binance_Orderbook_loc_prefix = os.path.join(binance_Orderbook_Output_Folder, 'binance_order_book_')

# Log file
default_log_file_path = os.path.join(fatwoman_log_path, "Total.txt")
Binance_save_log_path = os.path.join(fatwoman_log_path, "BinanceDownload_output.txt")
Hourly_log_path       = os.path.join(fatwoman_log_path, "Batch_Hourly.txt")
logging_override = {
    'binance_orderbook_save.py' : Binance_save_log_path,
    'CBOE_Scrape.py'            : Hourly_log_path,
    'VIX_Central_Scrape.py'     : Hourly_log_path,
    }

# Screensaver
Screensaver_url_dir     = os.path.join(fatwoman_base_path, 'Scripts_Surfer') # not really used
Screensaver_html_dir    = os.path.join(fatwoman_data_path, 'Scripts_Surfer') # not really used
url_config_BBG              = os.path.join(Screensaver_url_dir, 'urls_bbg.csv')
url_config_yahoo            = os.path.join(Screensaver_url_dir, 'urls_yahoo.csv')
url_configuration_1         = os.path.join(Screensaver_url_dir, 'urls_1.csv')
url_configuration_2         = os.path.join(Screensaver_url_dir, 'urls_2.csv')
firefox_profile1        = r"/home/fatwoman/.mozilla/firefox/tmbcotcq.default-release"
firefox_profile2        = r"/home/fatwoman/.mozilla/firefox/tmbcotcq.default-release2"
surfer_dir_override     = {
    'logs'              : f"file://%s" %default_log_file_path,
    'Daily_Plot_HTML'   : f"file://%s" %YahooPlotter_Output_File,
    'Daily_YC_Appended' : f"file://%s" %YC_Appended_Plot,
    'vol_plot_VIX' : f"file://%s" %get_vol_plot_dir('^VIX'),
    'vol_plot_SPY' : f"file://%s" %get_vol_plot_dir('TLT'),
    'vol_plot_TLT' : f"file://%s" %get_vol_plot_dir('TSLA'),
    'vol_plot_TSLA' : f"file://%s" %get_vol_plot_dir('SPY'),
    'vol_plot_NVDA' : f"file://%s" %get_vol_plot_dir('AAPL'),
    'vol_plot_AAPL' : f"file://%s" %get_vol_plot_dir('NVDA'),
    } # this is the override dictinory for saved files to be visualized in the surfer

# Model
ModelDownload_Output_Folder = os.path.join(fatwoman_data_path, 'Scripts_Model') # quite useless
ModelDownload_Output_Data = os.path.join(ModelDownload_Output_Folder, r'Total_Data.csv') # quite useless

# Get Data
def data_get(TICKER = 'VIX'): # TICKER = 'VIX'
    df = pd.read_csv(YahooDownload_Output_File).set_index('Date')[[TICKER]]
    df = df.loc[df.first_valid_index():]
    return df