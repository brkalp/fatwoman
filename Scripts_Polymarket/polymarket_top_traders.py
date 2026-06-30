""" Created on 30-06-2026 @author: ripintheblue
Scan top traders by volume on Polymarket and save results to a timestamped CSV.

Usage:
    python polymarket_top_traders.py [--window 1d|1w|1m|all] [--limit N] [--out-dir DIR]
"""
import sys
import os
import argparse
import logging
import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _d in ['Scripts_Setup_Logger', 'Scripts_Setup_Dirs']:
    sys.path.insert(0, os.path.join(_ROOT, _d))

try:
    from fatwoman_log_setup import script_end_log
except ImportError:
    def script_end_log(): pass

try:
    from fatwoman_dir_setup import polymarket_dir as _DEFAULT_OUT_DIR
except ImportError:
    _DEFAULT_OUT_DIR = os.path.dirname(os.path.abspath(__file__))

_DATA_BASE = "https://data-api.polymarket.com"

# Fields to include in the CSV and their display order
_COLUMNS = [
    "rank",
    "name",
    "proxyWallet",
    "volume",
    "pnl",
    "percentPnl",
    "numTrades",
]

_RENAME = {
    "proxyWallet":  "wallet",
    "percentPnl":   "pct_pnl",
    "numTrades":    "num_trades",
}


def _fetch_leaderboard(
    session: requests.Session,
    window: str,
    limit: int,
    offset: int = 0,
) -> List[Dict]:
    params: Dict = {
        "window": window,
        "limit":  limit,
        "offset": offset,
        "by":     "volume",
    }
    r = session.get(f"{_DATA_BASE}/leaderboard", params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else data.get("data", [])


def fetch_top_traders(window: str = "1w", limit: int = 100) -> pd.DataFrame:
    """Return a DataFrame of top traders sorted by volume."""
    session = requests.Session()
    session.headers["User-Agent"] = "fatwoman-polymarket/1.0"

    rows: List[Dict] = []
    page_size = min(limit, 100)
    offset = 0

    while len(rows) < limit:
        batch = _fetch_leaderboard(session, window, page_size, offset)
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size

    rows = rows[:limit]

    if not rows:
        logging.warning("Leaderboard returned no data for window=%s", window)
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Keep only known columns that exist; add rank if missing
    present = [c for c in _COLUMNS if c in df.columns]
    if "rank" not in df.columns and present:
        df.insert(0, "rank", range(1, len(df) + 1))
        present = ["rank"] + [c for c in present if c != "rank"]

    df = df[present]
    df = df.rename(columns=_RENAME)

    # Round float columns
    for col in ("volume", "pnl", "pct_pnl"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

    return df


def save_to_csv(df: pd.DataFrame, out_dir: str, window: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"polymarket_top_traders_{window}_{ts}.csv"
    path = os.path.join(out_dir, filename)
    df.to_csv(path, index=False)
    return path


def main():
    parser = argparse.ArgumentParser(description="Polymarket top traders by volume → CSV")
    parser.add_argument("--window",  default="1w",
                        choices=["1d", "1w", "1m", "all"],
                        help="Leaderboard time window (default: 1w)")
    parser.add_argument("--limit",   type=int, default=100,
                        help="Number of traders to fetch (default: 100)")
    parser.add_argument("--out-dir", default=_DEFAULT_OUT_DIR,
                        help="Directory to write the CSV (default: %(default)s)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%H:%M:%S",
    )

    logging.info("Fetching top %d traders | window=%s", args.limit, args.window)

    try:
        df = fetch_top_traders(window=args.window, limit=args.limit)
    except requests.HTTPError as e:
        logging.error("API error: %s", e)
        sys.exit(1)
    except requests.RequestException as e:
        logging.error("Network error: %s", e)
        sys.exit(1)

    if df.empty:
        logging.warning("No traders returned — nothing to write.")
        sys.exit(0)

    path = save_to_csv(df, args.out_dir, args.window)
    logging.info("Saved %d rows → %s", len(df), path)

    # Print top 10 to console
    print(df.head(10).to_string(index=False))

    script_end_log()


if __name__ == "__main__":
    main()
