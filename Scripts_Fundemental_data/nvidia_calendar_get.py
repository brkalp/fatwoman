import yfinance as yf

# Get the ticker object for NVIDIA
nvidia = yf.Ticker("NVDA")

# Fetch the earnings calendar
earnings_calendar = nvidia.calendar

# Display the earnings announcement dates
print(earnings_calendar)
# {'Dividend Date': datetime.date(2024, 12, 27), 'Ex-Dividend Date': datetime.date(2024, 9, 12), 'Earnings Date': [datetime.date(2025, 2, 26)], 'Earnings High': 0.95377, 'Earnings Low': 0.82, 'Earnings Average': 0.84583, 'Revenue High': 42145820000, 'Revenue Low': 37500000000, 'Revenue Average': 38125473110}


nvidia = yf.Ticker("NVDA")

# Fetch the earnings data
earnings = nvidia.earnings

# Fetch the quarterly financials
quarterly_financials = nvidia.quarterly_financials

# Display the dates when quarterly financials were reported
print(quarterly_financials.columns)