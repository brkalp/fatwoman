""" Created on 03-09-2024 05:12:03 @author: ripintheblue """
import pandas as pd
import matplotlib.pyplot as plt

# historical rates
# https://home.treasury.gov/interest-rates-data-csv-archive

# Correct URL for the yield curve data
data_url = 'https://home.treasury.gov/system/files/276/yield-curve-rates-1990-2023.csv'

# Read data from the URL
try:
    data = pd.read_csv(data_url)

    # Filter for the most recent data
    latest_data = data.iloc[0]

    # Extract maturities and their corresponding yields
    maturities = latest_data.index[1:]  # Assuming the first column is 'Date'
    yields = latest_data.values[1:]

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(maturities, yields, marker='o')
    plt.title('U.S. Treasury Yield Curve')
    plt.xlabel('Maturity')
    plt.ylabel('Yield (%)')
    plt.xticks(rotation=45)  # Rotate maturity labels for better readability
    plt.grid(True)
    plt.show()

except Exception as e:
    print(f"An error occurred: {e}")
