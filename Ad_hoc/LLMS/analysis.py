"""
Created on 06-19-2026 15:59:56
@author: ripintheblue
"""
import os
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from pathlib import Path

from fatwoman_dir_setup import LLM_data_path, db_trades_name, db_trades, db_strategy_daily_returns_name, adhoc_fol
os.chdir(os.path.join(adhoc_fol, 'LLMS'))

SIDE_SIGN = {"long": 1, "short": -1, "neutral": 0}

TICKER_FIX = {
    # --- renamed / re-listed equities ---
    'CHK': 'EXE',          # Chesapeake Energy -> Expand Energy
    'SQ': 'XYZ',           # Square -> Block Inc
    'GPS': 'GAP',          # Gap Inc ticker change
    'PARAA': 'PSKY',       # Paramount -> Paramount Skydance
    'TSMC': 'TSM',          # use the US ADR ticker
    # --- delisted / acquired, no live equivalent ---
    'PXD': None,            # Pioneer Natural Resources, absorbed into COP
    'WORK': None,           # Slack, delisted (acquired by Salesforce)
    'HES': None,            # Hess, acquired by Chevron 2025
    'SCHN': None,           # Schnitzer Steel -> Radius Recycling -> delisted 2025
    'LACX': None,           # unclear / illiquid, drop
    # --- Swedish (Stockholm) tickers needing class-share suffix ---
    'VOLCAR': 'VOLCAR-B.ST',
    'SWEC': 'SWEC-B.ST',
    'SSAB': 'SSAB-B.ST',
    'NIBE': 'NIBE-B.ST',
    'SAAB': 'SAAB-B.ST',
    'SAAB.B': 'SAAB-B.ST',
    'SAABB': 'SAAB-B.ST',
    'HUFV': 'HUFV-A.ST',
    'ATCO': 'ATCO-A.ST',    # Atlas Copco (not Atlas Corp)
    'SCAQ': 'SCA-B.ST',
    'SKFB.ST': 'SKF-B.ST',
    'BOL': 'BOL.ST',
    'VOLV': 'VOLV-B.ST',
    'HEXA': 'HEXA-B.ST',
    'EQTAB.ST': 'EQT.ST',
    'SKLGF': 'SKA-B.ST',    # Skanska, US OTC -> Stockholm listing
    # --- other European equities ---
    'BT.A': 'BT-A.L',       # BT Group, London
    # --- indices -> Yahoo index symbols ---
    'FTSE100': '^FTSE', 'FTSE': '^FTSE',
    'NIKKEI': '^N225', 'NIKKEI225': '^N225', 'N225': '^N225',
    'HANGSENG': '^HSI', 'HSI': '^HSI',
    'KOSPI200': '^KS11',
    'CAC40': '^FCHI',
    'NIFTY50': '^NSEI', 'NIFTY': '^NSEI',
    'US500': '^GSPC',
    'INDU': '^DJI', 'DJI': '^DJI',
    'VIX': '^VIX',
    'SX7E': None,            # no direct Yahoo proxy, drop
    # --- futures -> Yahoo continuous-contract symbols ---
    'ES_F': 'ES=F',
    'NQ_F': 'NQ=F', 'NQH26': 'NQ=F',
    'CLH26': 'CL=F', 'CL_F': 'CL=F', 'CL1': 'CL=F', 'WTI/CL1': 'CL=F',
    'ZB': 'ZB=F',
    'BRN=F': 'BZ=F',
    # --- FX pairs -> Yahoo "=X" format ---
    'AUDUSD': 'AUDUSD=X', 'AUD/USD': 'AUDUSD=X',
    'USDSEK': 'USDSEK=X', 'USD/SEK': 'USDSEK=X',
    'USDCHF': 'USDCHF=X', 'CHFUSD': 'USDCHF=X',  # CHFUSD: inverse, no direct =X
    'USD/MXN': 'USDMXN=X',
    'EUR/JPY': 'EURJPY=X',
    'EUR/USD': 'EURUSD=X', 'EURUSD': 'EURUSD=X', 'FXEUSD': 'EURUSD=X',
    'ZARUSD': 'USDZAR=X',   # inverse, no direct ZARUSD=X
    'USDJPY': 'USDJPY=X', 'USD/JPY': 'USDJPY=X',
    'USD/IDR': 'USDIDR=X',
    'GBPUSD': 'GBPUSD=X', 'GBP/USD': 'GBPUSD=X',
    'NZDUSD': 'NZDUSD=X',
    'CHFJPY': 'CHFJPY=X',
    'BTCUSD': 'BTC-USD', 'BTC/USD': 'BTC-USD',
    # --- commodities ---
    'XAU=USD': 'GC=F', 'XAU': 'GC=F',
    'XAUUSD': 'XAUUSD=X',
    'XAGUSD': 'XAGUSD=X',
    'COPPER': 'HG=F',
    'NGAS': 'NG=F',
    'USOIL': 'CL=F',
    # --- garbage / placeholder ---
    'TICKER': None,
}


def apply_ticker_fix(df):
    """Map raw tickers to Yahoo-resolvable symbols; tickers mapped to None are
    kept in the dataframe but will yield NaN prices/pnl (no live equivalent)."""
    df["ticker_raw"] = df["ticker"]
    df["ticker"] = df["ticker"].map(lambda t: TICKER_FIX.get(t, t))
    return df


def open_close_5d(price_df, date):
    """Return (open, close, close_after_5_trading_days) for a given date, or (None, None, None)."""
    if price_df.empty or date not in price_df.index:
        return None, None, None
    idx = price_df.index.get_loc(date)
    open_px = price_df["Open"].iloc[idx]
    close_px = price_df["Close"].iloc[idx]
    fwd_idx = idx + 5
    close_5d = price_df["Close"].iloc[fwd_idx] if fwd_idx < len(price_df) else None
    return open_px, close_px, close_5d


def strategy_stats(df, pnl_col):
    """Per-strategy: cumulative (compounded) pnl series, total pnl, max drawdown
    (with date and that day's pnl), accuracy."""
    results = {}
    for strat, g in df.dropna(subset=[pnl_col]).groupby("strategy"):
        g = g[g["side"] != "neutral"]
        if g.empty:
            continue
        # equal-weight portfolio: each ticker held that day gets 1/n of the book
        daily_pct = g.groupby("date")[pnl_col].mean().sort_index()
        daily_ret = daily_pct / 100
        equity = (1 + daily_ret).cumprod()
        running_max = equity.cummax()
        drawdown = equity / running_max - 1
        max_dd_date = drawdown.idxmin()
        max_dd = drawdown.loc[max_dd_date] * 100
        max_dd_day_pnl = daily_pct.loc[max_dd_date]
        total = (equity.iloc[-1] - 1) * 100
        accuracy = (g[pnl_col] > 0).mean() * 100
        results[strat] = {
            "cum_series": (equity - 1) * 100,  # cumulative pnl %, reinvested
            "total_pnl": total,
            "max_drawdown": max_dd,
            "max_drawdown_date": max_dd_date,
            "max_drawdown_day_pnl": max_dd_day_pnl,
            "accuracy_pct": accuracy,
            "n_trades": len(g),
        }
    return results


def plot_strategies(results, title, outpath):
    plt.figure(figsize=(11, 6))
    for strat, r in results.items():
        plt.plot(r["cum_series"].index, r["cum_series"].values, label=strat)
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Cumulative PnL (%)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()


def print_summary(results, label):
    print(f"\n=== {label} ===")
    for strat, r in results.items():
        print(
            f"{strat:18s} total_pnl={r['total_pnl']:8.2f}%  "
            f"max_drawdown={r['max_drawdown']:8.2f}% (on {r['max_drawdown_date'].date()}, "
            f"day_pnl={r['max_drawdown_day_pnl']:.2f}%)  "
            f"accuracy={r['accuracy_pct']:6.2f}%  "
            f"n_trades={r['n_trades']}"
        )


# ---------------------------------------------------------------------------
# script body
# ---------------------------------------------------------------------------
in_path = Path("recs and daily merged.csv")  # change filename here if needed

df = pd.read_csv(in_path, sep=";")
df["date"] = pd.to_datetime(df["date"])
df["side"] = df["side"].str.lower()
df = apply_ticker_fix(df)

tickers = sorted(t for t in df["ticker"].unique() if t is not None)
start, end = df["date"].min(), df["date"].max()

print(f"Fetching prices for {len(tickers)} tickers from {start.date()} to {end.date()}...")

# buffer end date forward so "close after 5 trading days" has data near the last rec date
data = yf.download(
    tickers,
    start=start - pd.Timedelta(days=5),
    end=end + pd.Timedelta(days=20),
    group_by="ticker",
    auto_adjust=False,
    progress=True,
    threads=True,
)

prices = {}
for t in tickers:
    try:
        sub = data[t][["Open", "Close"]].dropna()
        sub.index = pd.to_datetime(sub.index)
        prices[t] = sub
    except (KeyError, Exception):
        prices[t] = pd.DataFrame(columns=["Open", "Close"])

opens, closes, closes5, pnl_day, pnl_5d = [], [], [], [], []
for _, row in df.iterrows():
    sign = SIDE_SIGN.get(row["side"], 0)
    o, c, c5 = open_close_5d(prices.get(row["ticker"], pd.DataFrame()), row["date"])
    opens.append(o)
    closes.append(c)
    closes5.append(c5)
    pnl_day.append(sign * (c - o) / o * 100 if o not in (None, 0) and c is not None else None)
    pnl_5d.append(sign * (c5 - o) / o * 100 if o not in (None, 0) and c5 is not None else None)

df["open"] = opens
df["close"] = closes
df["close_after_5_days"] = closes5
df["pnl_pct_morning_to_evening"] = pnl_day
df["pnl_pct_morning_to_5_days"] = pnl_5d

out_csv = in_path.with_name(f"{in_path.stem}_with_pnl.csv")
df.to_csv(out_csv, sep=";", index=False)
print(f"Wrote {out_csv}")

res_evening = strategy_stats(df, "pnl_pct_morning_to_evening")
res_5day = strategy_stats(df, "pnl_pct_morning_to_5_days")

print_summary(res_evening, "Morning -> Evening close")
print_summary(res_5day, "Morning -> Close after 5 days")

plot_strategies(res_evening, "Cumulative PnL: Morning->Evening", in_path.with_name("cum_pnl_evening.png"))
plot_strategies(res_5day, "Cumulative PnL: Morning->5 Days", in_path.with_name("cum_pnl_5day.png"))
print("Saved cum_pnl_evening.png and cum_pnl_5day.png")