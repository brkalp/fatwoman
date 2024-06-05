""" Created on 03-09-2024 05:35:53 @author: ripintheblue """
import QuantLib as ql
import matplotlib.pyplot as plt
import numpy as np

calculation_date = ql.Date(9, 3, 2024)
ql.Settings.instance().evaluationDate = calculation_date
day_count = ql.ActualActual(ql.ActualActual.ISDA)
calendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond)
interpolation = ql.Linear()
compounding = ql.Compounded
compounding_frequency = ql.Annual

# Define market data
rates = [(1/12, 0.5), (3/12, 0.55), (6/12, 0.6), (1, 0.65), (2, 0.7), (3, 0.75), (5, 1.0), (7, 1.25), (10, 1.5), (20, 2.0), (30, 2.5)]
spot_dates = [calculation_date + ql.Period(int(maturity * 12), ql.Months) for maturity, _ in rates]
spot_rates = [rate / 100.0 for _, rate in rates]

# Construct the spot curve
spot_curve = ql.ZeroCurve(spot_dates, spot_rates, day_count, calendar, interpolation, compounding, compounding_frequency)
spot_curve_handle = ql.YieldTermStructureHandle(spot_curve)

# Fetching the zero rate for a specific time
date_175 = calculation_date + ql.Period(175, ql.Months)
rate_175 = spot_curve_handle.zeroRate(date_175, day_count, compounding, compounding_frequency, True).rate()

print(f"Zero rate at month 175: {rate_175:.4%}")

# Plotting
times = [0] + [spot_curve.timeFromReference(sd) for sd in spot_dates]
rates = [rate_175] + [spot_curve_handle.zeroRate(sd, day_count, compounding, compounding_frequency, True).rate() for sd in spot_dates]

plt.figure(figsize=(10, 6))
plt.plot(times, rates, marker='o', label="Spot Rates")
plt.scatter(spot_curve.timeFromReference(date_175), rate_175, color='red', label="Month 175")
plt.title("Spot Rate Curve with Interpolated Value at Month 175")
plt.xlabel("Time (Years)")
plt.ylabel("Zero Rate (%)")
plt.legend()
plt.grid(True)
plt.show()
