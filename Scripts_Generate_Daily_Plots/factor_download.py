""" Created on 12-27-2025 23:11:45 @author: ripintheblue """
import logging
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log


# Build a DataFrame of main style factors (Market, Size, Value, Quality, Investment)
# Source: Fama-French 5 Factors (open, research-grade)

import io, zipfile, requests, re
import pandas as pd

URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip"

r = requests.get(URL, timeout=60)
z = zipfile.ZipFile(io.BytesIO(r.content))
csv = [n for n in z.namelist() if n.lower().endswith(".csv")][0]

raw = z.read(csv).decode("latin1").splitlines()
data_rows = [l for l in raw if re.match(r"^\d{8},", l)]

df = pd.read_csv(
    io.StringIO("\n".join(data_rows)),
    header=None,
    names=["Date", "Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]
)

df["Date"] = pd.to_datetime(df["Date"], format="%Y%m%d")

df = df.rename(columns={
    "Mkt-RF": "Market",
    "SMB": "Size",
    "HML": "Value",
    "RMW": "Quality",
    "CMA": "Investment",
})

# convert percent to decimal
factors = df.set_index("Date")[["Market", "Size", "Value", "Quality", "Investment"]] / 100.0

# cum_factors = (1 + factors).cumprod()
# print(cum_factors.tail())
print(factors.tail())
df.to_clipboard()
# import io, zipfile, requests, re
# import pandas as pd

# URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip"

# r = requests.get(URL, timeout=60)
# z = zipfile.ZipFile(io.BytesIO(r.content))
# csv = [n for n in z.namelist() if n.lower().endswith(".csv")][0]

# # raw = z.read(csv_name).decode("latin1").splitlines()
# # lines = [l for l in raw if len(l) > 8 and l[:8].isdigit()]
# raw = z.read(csv).decode("latin1").splitlines()
# data_rows = [l for l in raw if re.match(r"^\d{6},", l)]

# df = pd.read_csv(
#     io.StringIO("\n".join(data_rows)),
#     header=None,
#     names=["Date", "Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]
# )

# df["Date"] = pd.to_datetime(df["Date"], format="%Y%m%d")
# # Canonical factor set
# df = df.rename(columns={
#     "Mkt-RF": "Market",
#     "SMB": "Size",
#     "HML": "Value",
#     "RMW": "Quality",
#     "CMA": "Investment",
# })

# # Example: cumulative factor returns
# cum_factors = (1 + factors).cumprod()

# print(factors.tail())
# print(cum_factors.tail())


