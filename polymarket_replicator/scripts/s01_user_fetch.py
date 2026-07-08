"""Step 1 - User fetch.

Fetches a big universe of traders from Polymarket: per category the biggest
10 markets plus markets of the 100 biggest events, then harvests the top 100
holders of each market.

Backtest mode (--backtest --as-of YYYYMMDD) back-calculates the available
user set: holders are filtered to wallets that already had activity on or
before as_of, so later joiners never enter a historical universe (lookahead).
The holder snapshot itself is current-day, which leaves a survivorship
caveat - logged on every backtest run.

Output: 01_polymarket_top_users_by_category_YYYYMMDD_xx.csv
"""
import _bootstrap  # noqa: F401
import argparse
import logging
from datetime import datetime, timezone

import pandas as pd

from core.config import load_config
from core.io_utils import build_path, day_stamp, write_csv
from core.polymarket_api import CATEGORIES, get_api

PREFIX = "01_polymarket_top_users_by_category"


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--backtest", action="store_true")
    p.add_argument("--as-of", help="YYYYMMDD historical date for backtesting")
    p.add_argument("--mock", action="store_true", help="force offline mock api")
    return p.parse_args(argv)


def run(args):
    cfg = load_config()
    if args.mock:
        cfg["mock_api"] = True
    as_of = (datetime.strptime(args.as_of, "%Y%m%d").replace(tzinfo=timezone.utc)
             if args.as_of else None)
    api = get_api(cfg, as_of=as_of)
    uni = cfg["universe"]

    markets, seen = [], set()
    for cat in CATEGORIES:
        markets += [m for m in api.top_markets(cat, uni["top_markets_per_category"])]
    for m in api.top_events(uni["top_events"]):
        markets.append(m)
    markets = [m for m in markets
               if m["condition_id"] not in seen and not seen.add(m["condition_id"])]
    logging.info("universe: %d unique markets across %d categories",
                 len(markets), len(CATEGORIES))

    rows = []
    for m in markets:
        try:
            holders = api.market_holders(m["condition_id"], uni["holders_per_market"])
        except Exception as exc:  # noqa: BLE001 - one bad market must not kill the run
            logging.error("holders failed for %s: %s", m["condition_id"], exc)
            continue
        for rank, h in enumerate(holders, 1):
            rows.append({
                "category": m["category"],
                "condition_id": m["condition_id"],
                "question": m["question"],
                "proxy_wallet": h["proxy_wallet"],
                "user_name": h["user_name"],
                "holding_usdc": h["holding_usdc"],
                "holder_rank": rank,
            })

    df = pd.DataFrame(rows)
    if args.backtest and as_of is not None:
        logging.warning("backtest universe: filtering holders to wallets active "
                        "on or before %s (survivorship caveat: holder snapshot "
                        "is current-day)", args.as_of)
        active = {
            w for w in df["proxy_wallet"].unique()
            if api.wallet_active_before(w, as_of)
        }
        df = df[df["proxy_wallet"].isin(active)]

    out = build_path(PREFIX, day_stamp(as_of), backtest=args.backtest)
    write_csv(df, out)
    logging.info("universe users: %d unique wallets", df["proxy_wallet"].nunique())
    return out


if __name__ == "__main__":
    run(parse_args())
