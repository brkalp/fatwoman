
import pandas as pd
import yfinance as yf
from datetime import datetime as dt
# https://www.mordorintelligence.com/industry-reports/turkey-construction-market
# https://www.trade.gov/country-commercial-guides/turkey-construction-reconstruction
# https://news-files.foreks.com/attachment/1705388805569_YKYEquityStrategyJan24160120241.pdf
# https://www.sekeryatirim.com.tr/English/Research/ResearchReportFile/63641/Seker%20Invest_2024_Equity_Strategy.pdf
# https://www.sekeryatirim.com.tr/English/Research/ResearchReportFile/62391/recommendation-list-25.12.24.pdf
Tickers = [
    # index
    'XU100.IS',
    # # cimento
    'CIMSA.IS',
    'AKCNS.IS',
    'AFYON.IS',
    'KONYA.IS',
    'NUHCM.IS',
    # # insaat
    'ENKAI.IS',
    'ICTSF',
    'TKFEN.IS',
    'NUGYO.IS',
    'LMKDC.IS',
    # # demir celik
    'KRDMD.IS',
    'ISDMR.IS',
    'IZMDC.IS',
    'KOCMT.IS',
    'RGYAS.IS'
    ]
# df0 = yf.download(Tickers, dt(2005,1,1))['Adj Close']


# Dictionaries to store each type of financial data as a DataFrame
financials_dfs = {}
balance_sheets_dfs = {}
cash_flows_dfs = {}

for ticker in Tickers:
    stock = yf.Ticker(ticker)
    # Attempt to fetch financial data
    try:
        # Get financials, balance sheet, and cash flow
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow

        # Convert to DataFrame and store in the respective dictionary
        financials_dfs[ticker] = pd.DataFrame(financials)
        balance_sheets_dfs[ticker] = pd.DataFrame(balance_sheet)
        cash_flows_dfs[ticker] = pd.DataFrame(cash_flow)

    except ValueError:
        print(f"Failed to fetch data for {ticker}")
