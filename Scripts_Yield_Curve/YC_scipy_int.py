""" Created on 03-09-2024 06:21:18 @author: ripintheblue """
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import YC_FRED_Data, YC_Scipy_Plot
from scipy.interpolate import CubicSpline
import numpy as np
import pandas as pd
import socket
import matplotlib
if socket.gethostname() != 'ripintheblue': matplotlib.use('Agg')
import matplotlib.pyplot as plt
import time
import os
import seaborn as sns
sns.set()

print('Reading data from %s' % YC_FRED_Data)
rates_pd = pd.read_csv(YC_FRED_Data)
maturities_months = list(rates_pd['Maturity_Months'].values)
rates = list(rates_pd['Rate'].values)

# Interpolating using Cubic Spline
cs = CubicSpline(maturities_months, rates)

# Generate more points for a smooth curve
xnew = np.linspace(min(maturities_months), max(maturities_months), 300)
ynew = cs(xnew)

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(maturities_months, rates, 'o', label='Original Data')
plt.plot(xnew, ynew, '-', label='Cubic Spline Interpolation')
plt.title(f"Scipy: Interpolated U.S. Treasury Yield Curve - {pd.to_datetime('today').strftime('%Y-%m-%d')}")
plt.xlabel('Maturity (Months)')
plt.ylabel('Yield (%)')
plt.legend()
plt.grid(True)
print('Saving to %s' % YC_Scipy_Plot)
plt.savefig(YC_Scipy_Plot)
plt.show()
  
script_end_log()