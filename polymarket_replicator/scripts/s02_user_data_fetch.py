"""Step 2 - User data fetch.

Takes the universe from step 1 and fetches the data needed to judge each
big user: account size, past trades, daily pnl, drawdown, accuracy. Users
appearing in several markets/categories are deduped to their biggest-holding
category, and only the top max_users_per_category by holding are fetched to
keep API load sane.

Output: 02_user_data_YYYYMMDD_xx.csv
"""
import _bootstrap  # noqa: F401
import argparse
import logging
from datetime import datetime, timezone

import pandas as pd

from core.config import load_config
from core.io_utils import build_path, day_stamp, latest_file, read_csv, write_csv
from core.metrics import max_drawdown, total
from core.polymarket_api import get_api

PREFIX = "02_user_data"


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--backtest", action="store_true")
    p.add_argument("--as-of", help="YYYYMMDD historical date for backtesting")
    p.add_argument("--mock", action="store_true")
    p.add_argument("--input", help="explicit step-1 csv (default: latest)")
    return p.parse_args(argv)


def run(args):
    cfg = load_config()
    if args.mock:
        cfg["mock_api"] = True
    as_of = (datetime.strptime(args.as_of, "%Y%m%d").replace(tzinfo=timezone.utc)
             if args.as_of else None)
    api = get_api(cfg, as_of=as_of)

    src = args.input or latest_file("01_polymarket_top_users_by_category",
                                    backtest=args.backtest)
    if src is None:
        raise SystemExit("no step-1 universe file found - run s01_user_fetch first")
    uni = read_csv(src)
    logging.info("reading universe %s (%d rows)", getattr(src, "name", src), len(uni))

    # one row per user: category where his holding is biggest
    per_user = (uni.sort_values("holding_usdc", ascending=False)
                   .drop_duplicates("proxy_wallet"))
    cap = cfg["universe"]["max_users_per_category"]
    per_user = per_user.groupby("category").head(cap)

    rows = []
    for _, u in per_user.iterrows():
        try:
            acct = api.user_account(u["proxy_wallet"])
        except Exception as exc:  # noqa: BLE001 - skip broken users, keep the run
            logging.error("account fetch failed for %s: %s", u["proxy_wallet"], exc)
            continue
        rows.append({
            "proxy_wallet": u["proxy_wallet"],
            "user_name": u["user_name"],
            "category": u["category"],
            "holding_usdc": u["holding_usdc"],
            "account_size": acct["account_size"],
            "n_trades_30d": acct["n_trades_30d"],
            "total_pnl_30d": total(acct["daily_pnl"]),
            "avg_daily_pnl": round(total(acct["daily_pnl"]) / max(len(acct["daily_pnl"]), 1), 2),
            "max_drawdown": max_drawdown(acct["daily_pnl"], acct["account_size"]),
            "accuracy": acct["accuracy"],
        })

    df = pd.DataFrame(rows)
    out = build_path(PREFIX, day_stamp(as_of), backtest=args.backtest)
    write_csv(df, out)
    logging.info("user data fetched for %d users in %d categories",
                 len(df), df["category"].nunique() if len(df) else 0)
    return out


if __name__ == "__main__":
    run(parse_args())
