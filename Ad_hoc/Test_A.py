import pandas as pd
import matplotlib.pyplot as plt

POSITION_LIMIT = 1_000_000

# Load files
log = pd.read_csv(r"C:\Users\User\Downloads\logs.csv",delimiter=';')
product = pd.read_csv(r"C:\Users\User\Downloads\product.csv")

# Clean column names just in case
log.columns = [c.strip().lower() for c in log.columns]
product.columns = [c.strip().lower() for c in product.columns]

# Parse timestamp
log["current_timestamp"] = pd.to_datetime(log["current_timestamp"])

# Keep only executed trades, because position changes only when orders are filled
fills = log[log["action"].str.lower() == "filled"].copy()

# Merge with product reference data
df = fills.merge(product, on="product", how="left")

# Standardize text columns
for col in ["side", "asset_type", "option_type"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.lower().str.strip()

# ---------- Net position contribution per trade ----------
# Futures:
# buy  -> +amt
# sell -> -amt
futures_mask = df["asset_type"] == "future"

df["position_change"] = 0.0

df.loc[futures_mask & (df["side"] == "buy"), "position_change"] = df["trade_amt"]
df.loc[futures_mask & (df["side"] == "sell"), "position_change"] = -df["trade_amt"]

# Options, using the formula given in the task:
# -amt if (sell call) or (buy put)
# +amt if (buy call) or (sell put)
options_mask = df["asset_type"] == "option"

df.loc[options_mask & (df["side"] == "sell") & (df["option_type"] == "call"), "position_change"] = -df["trade_amt"]
df.loc[options_mask & (df["side"] == "buy") & (df["option_type"] == "put"), "position_change"] = -df["trade_amt"]
df.loc[options_mask & (df["side"] == "buy") & (df["option_type"] == "call"), "position_change"] = df["trade_amt"]
df.loc[options_mask & (df["side"] == "sell") & (df["option_type"] == "put"), "position_change"] = df["trade_amt"]

# Sort by time
df = df.sort_values("current_timestamp").reset_index(drop=True)

# Position value contribution of each trade
df["position_value_change"] = df["position_change"] * df["underlying_asset_price"]

# Aggregate by timestamp across all products
timeline = (
    df.groupby("current_timestamp", as_index=False)["position_value_change"]
      .sum()
      .sort_values("current_timestamp")
)

# Running total position value
timeline["position_value"] = timeline["position_value_change"].cumsum()

# Check limit breach
timeline["limit_breached"] = timeline["position_value"].abs() > POSITION_LIMIT

# First breach
breach_rows = timeline[timeline["limit_breached"]]
if not breach_rows.empty:
    first_breach_time = breach_rows.iloc[0]["current_timestamp"]
    first_breach_value = breach_rows.iloc[0]["position_value"]
    print("First time position limit was breached:", first_breach_time)
    print("Position value at breach:", first_breach_value)
else:
    print("Position limit was never breached.")

# Show timeline table
print("\nPosition value over time:")
print(timeline)

# Draw chart
plt.figure(figsize=(12, 6))
plt.plot(timeline["current_timestamp"], timeline["position_value"], label="Position Value")
plt.axhline(POSITION_LIMIT, linestyle="--", label="+1,000,000")
plt.axhline(-POSITION_LIMIT, linestyle="--", label="-1,000,000")

if not breach_rows.empty:
    plt.axvline(first_breach_time, linestyle=":", label="First Breach")

plt.title("Position Value Over Time")
plt.xlabel("Time")
plt.ylabel("USD")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()