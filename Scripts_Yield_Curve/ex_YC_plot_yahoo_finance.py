""" Created on 03-09-2024 05:11:47 @author: ripintheblue """
import yfinance as yf
import matplotlib.pyplot as plt

# Define the tickers for Treasury yields of different maturities
# These tickers are for illustrative purposes and may need to be updated
tickers = {
    '1M': '^IRX',  # 13 Week
    '5Y': '^FVX',  # 5-year Treasury yield, using 2Y as a placeholder
    '10Y': '^TNX',  # 10-year Treasury yield
    '30Y': '^TYX'   # 30-year Treasury yield
}

# Fetch the latest yields
yields = {}
for maturity, ticker in tickers.items():
    try:
        # Fetch data
        bond = yf.Ticker(ticker)
        hist = bond.history(period="1d")
        
        # Get the last close price, which represents the yield
        last_close = hist['Close'].iloc[-1]
        yields[maturity] = last_close
    except Exception as e:
        print(f"Failed to fetch data for {maturity}: {e}")

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(list(yields.keys()), list(yields.values()), marker='o')
plt.title('Today\'s U.S. Treasury Yield Curve')
plt.xlabel('Maturity')
plt.ylabel('Yield (%)')
plt.grid(True)
plt.show()
