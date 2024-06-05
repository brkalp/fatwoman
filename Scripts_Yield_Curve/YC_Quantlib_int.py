""" Created on 03-09-2024 05:35:53 @author: ripintheblue """
#pip install seaborn
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import YC_FRED_Data, YC_Quantlib_Plot
import QuantLib as ql
import socket
import matplotlib
if socket.gethostname() != 'ripintheblue': matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import socket
sns.set()

# Set the settings
calculation_date = ql.Date(9, 3, 2024)
ql.Settings.instance().evaluationDate = calculation_date
day_count = ql.ActualActual(ql.ActualActual.ISDA)
calendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond)
interpolation = ql.Linear()
compounding = ql.Compounded
compounding_frequency = ql.Annual

print('Reading data from %s' % YC_FRED_Data)
rates_pd = pd.read_csv(YC_FRED_Data)
rates = rates_pd[['Maturity_Years', 'Rate']].values.tolist()

# Turn the rates into a QuantLib format
spot_dates = [calculation_date + ql.Period(int(maturity * 12), ql.Months) for maturity, _ in rates]
spot_rates = [rate / 100.0 for _, rate in rates]

# Construct the spot curve
spot_curve = ql.ZeroCurve(spot_dates, spot_rates, day_count, calendar, interpolation, compounding, compounding_frequency)
spot_curve_handle = ql.YieldTermStructureHandle(spot_curve)

# Fetching the zero rate for a specific time - 175 months
date_175 = calculation_date + ql.Period(175, ql.Months)
rate_175 = spot_curve_handle.zeroRate(date_175, day_count, compounding, compounding_frequency, True).rate()

print(f"Zero rate at month 175: {rate_175:.4%}")

# Plotting
times = [spot_curve.timeFromReference(sd) for sd in spot_dates]
rates = [spot_curve_handle.zeroRate(sd, day_count, compounding, compounding_frequency, True).rate() for sd in spot_dates]

plt.figure(figsize=(10, 6))
plt.plot(times, rates, marker='o', label="Spot Rates")
plt.scatter(spot_curve.timeFromReference(date_175), rate_175, color='red', label="Month 175")
plt.title("Quantlib: Spot Rate Curve with Interpolated Value at Month 175:%s" %rate_175)
plt.xlabel("Time (Years)")
plt.ylabel("Zero Rate (%)")
plt.legend()
plt.grid(True)
print('Saving to %s' % YC_Quantlib_Plot)
plt.savefig(YC_Quantlib_Plot)
plt.show()
script_end_log()