""" Created on 02-22-2024 01:08:09 @author: ripintheblue """
import os
import socket
# import fatwoman_log_setup
import pandas as pd
import time
import os

# %reset -f #forcefully resets the namespace by clearing all the variables, imported modules, and user-defined functions without asking for confirmation.
# import importlib
# import fatwoman_dir_setup
# importlib.reload(fatwoman_dir_setup)

# sys env variables / os.path.dirname('os.path.realpath(__file__)') /
# os.environ # pytonpath is here

if socket.gethostname() == 'ripintheblue':
    remoteIP = r'z:\\' # remoteIP = r'\\10.0.1.6\\'
    fatwoman_base_path = remoteIP + '15GB'
    fatwoman_data_path = remoteIP + 'fatboy'
if socket.gethostname() == 'fatwoman':
    fatwoman_base_path = r'/media/fatwoman/15GB'
    fatwoman_data_path = r'/media/fatwoman/fatboy'
if socket.gethostname() == 'Apollo-13':
    fatwoman_base_path = r'C:\Users\deniz\PycharmProjects\alp'
    fatwoman_data_path = r'C:\Users\deniz\PycharmProjects\fatboy'
if 'fatwoman_base_path' not in locals(): print('Data paths not defined for this machine!')
fatwoman_log_path = os.path.join(fatwoman_data_path, 'logs')

# LLM
LLM_data_path               = os.path.join(fatwoman_data_path, 'Scipts_LLM_trader')
LLM_data_path_finnhub_file  = os.path.join(LLM_data_path, 'news_FinnHub.csv')
LLM_flow1_response_file     = os.path.join(LLM_data_path, 'LLM_flow1_response_file.csv') # full response
LLM_flow1_order_file        = os.path.join(LLM_data_path, 'LLM_flow1_order_file.csv') # only tickers and buy sell
# LLM_config_path           = os.path.join(fatwoman_data_path, 'Scipts_LLM_trader')

# Avanza Scrape
avanza_data_path    = os.path.join(fatwoman_data_path, 'Scripts_Avanza_Scrape')
avanza_config_file  = os.path.join(fatwoman_base_path, 'Scripts_Avanza_Scrape', 'website_list.csv')

# Portfolio
portfolio_folder = os.path.join(fatwoman_data_path, 'Scripts_Portfolio')
portfolio_Plot  = os.path.join(portfolio_folder, 'Portfolio_loc.png')

# Daily downloads
YahooDownload_Output_Folder = os.path.join(fatwoman_data_path, 'Scripts_Generate_Daily_Plots')
YahooDownload_Output_File   = os.path.join(YahooDownload_Output_Folder, 'Daily_yahoo_data.csv')
YahooDownload_Ticker_File   = os.path.join(YahooDownload_Output_Folder, 'Tickers.csv')
YahooDownload_Info_File     = os.path.join(YahooDownload_Output_Folder, 'Tickers_and_info.csv')
YahooDownload_Outputs_SEK   = os.path.join(YahooDownload_Output_Folder, 'Daily_yahoo_data_in_SEK.csv')
YahooPlotter_Output_File    = os.path.join(YahooDownload_Output_Folder, 'Daily_yahoo_plot.html')
Total_data_file = YahooDownload_Output_File

# Index Constituents
Index_folder = YahooDownload_Output_Folder
Index_data_file   = os.path.join(Index_folder, 'sp500_index_cons.csv')
weights_data_file = os.path.join(Index_folder, 'sp500_index_cons_weight.csv')
# portfolio_Plot  = os.path.join(portfolio_folder, 'Portfolio_loc.png')

# Data Feeds - Scape Data location
VIX_Scrape_folder        = os.path.join(fatwoman_data_path, 'Scripts_VIX_Scrape') # need this to set download dir
CBOE_Scrape_Data_File   = os.path.join(VIX_Scrape_folder, 'CBOE_VIX.csv')
VIX_C_Scrape_Data_File  = os.path.join(VIX_Scrape_folder, 'Central_VIX.csv')
CBOE_Plotter_Output_File   = os.path.join(VIX_Scrape_folder, 'CBOE_Plotter_Output_File.html')
CBOE_Scrape_timestamp_format = '%d/%m/%Y'
YCFRED_Scrape_timestamp_format = '%d/%m/%Y'

# Yield Curve
YC_Scripts_Folder   = os.path.join(fatwoman_base_path, 'Scripts_Yield_Curve')
YC_Output_Folder    = os.path.join(fatwoman_data_path, 'Scripts_Yield_Curve')
YC_FRED_Data        = os.path.join(YC_Output_Folder, 'YC_FRED.csv')
YC_Scipy_Plot       = os.path.join(YC_Output_Folder, 'YC_Scipy_Plot.png')
YC_Quantlib_Plot    = os.path.join(YC_Output_Folder, 'YC_Quantlib_Plot.png')
YC_Appended_Plot    = os.path.join(YC_Output_Folder, 'YC_Appended_Plot.png')
YC_Fred_Hist_Plot   = os.path.join(YC_Output_Folder, 'YC_Fred_Hist_Plot.html')

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

# Log files
default_log_file_path = os.path.join(fatwoman_log_path, "Total.txt")
Binance_save_log_path = os.path.join(fatwoman_log_path, "BinanceDownload_output.txt")
Hourly_log_path       = os.path.join(fatwoman_log_path, "Batch_Hourly.txt")
Avanza_log_path       = os.path.join(avanza_data_path, "Avanza_Scraper.txt")
logging_override = {
    'binance_orderbook_save' : Binance_save_log_path,
    # 'CBOE_Scrape'            : Hourly_log_path,
    'VIX_Central_Scrape'     : Hourly_log_path,
    'avanzaDataScraping'     : Avanza_log_path, # avanza in different folder
    }
logging_import_ignore = [ # ignore the setup log if this is the importer
    'binance_orderbook_save'
    ]


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
    'Daily_Plot_yahoo'   : f"file://%s" %YahooPlotter_Output_File,
    'Daily_Plot_CBOE'   : f"file://%s" %CBOE_Plotter_Output_File,
    'Daily_Plot_YC' : f"file://%s" %YC_Appended_Plot,
    'Daily_Plot_YC_hist' : f"file://%s" %YC_Fred_Hist_Plot,
    'vol_plot_VIX' : f"file://%s" %get_vol_plot_dir('^VIX'),
    'vol_plot_SPY' : f"file://%s" %get_vol_plot_dir('TLT'),
    'vol_plot_TLT' : f"file://%s" %get_vol_plot_dir('TSLA'),
    'vol_plot_TSLA' : f"file://%s" %get_vol_plot_dir('SPY'),
    'vol_plot_NVDA' : f"file://%s" %get_vol_plot_dir('AAPL'),
    'vol_plot_AAPL' : f"file://%s" %get_vol_plot_dir('NVDA'),
    } # this is the override dictionary for saved files to be visualized in the surfer

# Model
ModelDownload_Output_Folder = os.path.join(fatwoman_data_path, 'Scripts_Model') # quite useless
ModelDownload_Output_Data = os.path.join(ModelDownload_Output_Folder, r'Total_Data.csv') # quite useless

# Get Data
def data_get(TICKER = 'VIX'): # TICKER = 'VIX'
    df = pd.read_csv(YahooDownload_Output_File).set_index('Date')[[TICKER]]
    df = df.loc[df.first_valid_index():]
    return df
