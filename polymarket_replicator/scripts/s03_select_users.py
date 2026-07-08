"""Step 3 - Select users.

Key logic of the strategy: filter the fetched users and select the best
candidates per category to form the "top Polymarket trader" portfolio whose
trades get replicated.

Filters (config selection.*): min account size, min trades 30d, min accuracy,
max drawdown, min 30d pnl. Score = mean of min-max normalized accuracy,
pnl-over-account and inverted drawdown. Top N users per category; replication
weight within a category is proportional to score.

Output: 03_selected_user_list_YYYYMMDD_xx.csv
"""
import _bootstrap  # noqa: F401
import argparse
import logging
from datetime import datetime, timezone

import pandas as pd

from core.config import load_config
from core.io_utils import build_path, day_stamp, latest_file, read_csv, write_csv

PREFIX = "03_selected_user_list"


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--backtest", action="store_true")
    p.add_argument("--as-of", help="YYYYMMDD stamp used for the output file")
    p.add_argument("--mock", action="store_true")  # accepted for symmetry
    p.add_argument("--input", help="explicit step-2 csv (default: latest)")
    return p.parse_args(argv)


def _norm(series: pd.Series) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(0.5, index=series.index)
    return (series - lo) / (hi - lo)


def select(df: pd.DataFrame, sel_cfg: dict) -> pd.DataFrame:
    """Pure selection logic - also reused by the backtester."""
    mask = (
        (df["account_size"] >= sel_cfg["min_account_size"])
        & (df["n_trades_30d"] >= sel_cfg["min_trades_30d"])
        & (df["accuracy"] >= sel_cfg["min_accuracy"])
        & (df["max_drawdown"] <= sel_cfg["max_drawdown"])
        & (df["total_pnl_30d"] >= sel_cfg["min_total_pnl_30d"])
    )
    passed = df[mask].copy()
    if passed.empty:
        return passed.assign(score=[], weight=[])
    passed["score"] = (
        _norm(passed["accuracy"])
        + _norm(passed["total_pnl_30d"] / passed["account_size"])
        + (1 - _norm(passed["max_drawdown"]))
    ) / 3

    picked = (passed.sort_values("score", ascending=False)
                    .groupby("category", group_keys=False)
                    .head(sel_cfg["users_per_category"])
                    .copy())
    picked["weight"] = picked.groupby("category")["score"].transform(
        lambda s: s / s.sum())
    return picked.sort_values(["category", "score"], ascending=[True, False])


def run(args):
    cfg = load_config()
    as_of = (datetime.strptime(args.as_of, "%Y%m%d").replace(tzinfo=timezone.utc)
             if args.as_of else None)
    src = args.input or latest_file("02_user_data", backtest=args.backtest)
    if src is None:
        raise SystemExit("no step-2 user data file found - run s02_user_data_fetch first")
    df = read_csv(src)
    logging.info("selecting from %d candidates (%s)", len(df), getattr(src, "name", src))

    picked = select(df, cfg["selection"])
    for cat, grp in picked.groupby("category"):
        logging.info("selected %s: %s", cat,
                     ", ".join(f"{r.user_name or r.proxy_wallet[:10]} "
                               f"(score {r.score:.2f}, w {r.weight:.2f})"
                               for r in grp.itertuples()))
    if picked.empty:
        logging.error("selection produced 0 users - filters too tight?")

    out = build_path(PREFIX, day_stamp(as_of), backtest=args.backtest)
    write_csv(picked, out)
    return out


if __name__ == "__main__":
    run(parse_args())
