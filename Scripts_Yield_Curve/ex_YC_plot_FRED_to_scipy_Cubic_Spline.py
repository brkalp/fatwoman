""" Created on 03-09-2024 05:11:28 @author: ripintheblue """
# pip install fredapi
# pip install scipy
from scipy.interpolate import CubicSpline
import numpy as np
import matplotlib.pyplot as plt
from fredapi import Fred
import pandas as pd
from fatwoman_api_setup import FRED_Key
fred = Fred(api_key=FRED_Key)

# Series IDs for Treasury yields
series_ids = {
    '1M': 'DGS1MO',
    '3M': 'DGS3MO',
    '6M': 'DGS6MO',
    '1Y': 'DGS1',
    '2Y': 'DGS2',
    '3Y': 'DGS3',
    '5Y': 'DGS5',
    '7Y': 'DGS7',
    '10Y': 'DGS10',
    '20Y': 'DGS20',
    '30Y': 'DGS30'
}

yields = {}
maturities_numeric = []
for maturity, series_id in series_ids.items():
    series_data = fred.get_series(series_id)
    yields[maturity] = series_data.iloc[-1]
    # Convert maturity to numeric value (months)
    if maturity.endswith('M'):
        maturities_numeric.append(int(maturity[:-1]))
    elif maturity.endswith('Y'):
        maturities_numeric.append(int(maturity[:-1]) * 12)

# Interpolating using Cubic Spline
cs = CubicSpline(maturities_numeric, list(yields.values()))

# Generate more points for a smooth curve
xnew = np.linspace(min(maturities_numeric), max(maturities_numeric), 300)
ynew = cs(xnew)

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(maturities_numeric, list(yields.values()), 'o', label='Original Data')
plt.plot(xnew, ynew, '-', label='Cubic Spline Interpolation')
plt.title(f"Interpolated U.S. Treasury Yield Curve - {pd.to_datetime('today').strftime('%Y-%m-%d')}")
plt.xlabel('Maturity (Months)')
plt.ylabel('Yield (%)')
plt.legend()
plt.grid(True)
plt.show()

