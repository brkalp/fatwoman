"""Step 6 - PnL reporter.

Goes through the (paper) account and prints/reports:
- current positions vs expected (what today's trade plans wanted vs what
  actually filled),
- open orders,
- pnl total and split by category (realized + unrealized),
- fills vs actuals from the step-5 execution files: average slippage in bps
  and fill rate.

Sends the summary to the *pnl* telegram channel (separate from trades) and
writes 06_report_YYYYMMDDHHMM_xx.csv in long (section,key,value) format.
"""
import _bootstrap  # noqa: F401
import argparse
import logging

import pandas as pd

from core.config import load_config
from core.io_utils import (build_path, data_dir, load_state, minute_stamp,
                           read_csv, write_csv)
from core.polymarket_api import get_api
from core.telegram_client import send

PREFIX = "06_report"


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mock", action="store_true")
    return p.parse_args(argv)


def _todays_files(prefix, stamp):
    return sorted(data_dir().glob(f"{prefix}_{stamp[:8]}*.csv"))


def run(args):
    cfg = load_config()
    if args.mock:
        cfg["mock_api"] = True
    api = get_api(cfg)
    stamp = minute_stamp()
    rows = []

    account = load_state("paper_account", None)
    if account is None:
        logging.info("no paper account yet - nothing to report")
        return None

    prices = {c: api.market_price(c) for c in account["positions"]}

    # --- positions vs expected -------------------------------------------
    expected = {}
    for f in _todays_files("04_trade_plan", stamp):
        for r in read_csv(f).itertuples():
            sign = 1 if r.side == "BUY" else -1
            expected[r.condition_id] = (expected.get(r.condition_id, 0.0)
                                        + sign * r.my_notional_usdc)
    logging.info("--- positions (actual vs expected from today's plans) ---")
    for cond in sorted(set(account["positions"]) | set(expected)):
        pos = account["positions"].get(cond)
        actual = round(pos["shares"] * prices.get(cond, pos["avg_price"]), 2) if pos else 0.0
        exp = round(max(expected.get(cond, 0.0), 0.0), 2)
        name = (pos or {}).get("question", cond[:16])
        logging.info("pos %-45s actual %8.2f expected %8.2f diff %8.2f",
                     str(name)[:45], actual, exp, actual - exp)
        rows.append({"section": "positions", "key": str(name)[:60],
                     "value": actual, "expected": exp})

    # --- open orders -------------------------------------------------------
    for o in account["open_orders"]:
        logging.info("open order: %s %s %.2fsh lim %.3f",
                     o["side"], o["condition_id"][:12], o["shares"], o["limit_price"])
        rows.append({"section": "open_orders",
                     "key": f"{o['side']} {o['condition_id'][:12]}",
                     "value": o["shares"], "expected": o["limit_price"]})

    # --- pnl total and per category ---------------------------------------
    unreal_by_cat = {}
    for cond, pos in account["positions"].items():
        upnl = pos["shares"] * (prices.get(cond, pos["avg_price"]) - pos["avg_price"])
        unreal_by_cat[pos["category"]] = unreal_by_cat.get(pos["category"], 0.0) + upnl
    realized_by_cat = account.get("realized_by_category", {})
    total_pnl = account["realized_pnl"] + sum(unreal_by_cat.values())
    equity = account["cash"] + sum(
        p["shares"] * prices.get(c, p["avg_price"])
        for c, p in account["positions"].items())

    rows.append({"section": "pnl", "key": "total", "value": round(total_pnl, 2),
                 "expected": None})
    rows.append({"section": "pnl", "key": "equity", "value": round(equity, 2),
                 "expected": account["equity_start"]})
    logging.info("pnl total %.2f (realized %.2f) | equity %.2f vs start %.2f",
                 total_pnl, account["realized_pnl"], equity, account["equity_start"])
    for cat in sorted(set(unreal_by_cat) | set(realized_by_cat)):
        cat_pnl = unreal_by_cat.get(cat, 0.0) + realized_by_cat.get(cat, 0.0)
        logging.info("pnl %-12s %8.2f", cat, cat_pnl)
        rows.append({"section": "pnl_by_category", "key": cat,
                     "value": round(cat_pnl, 2), "expected": None})

    # --- fills vs actuals: slippage + fill rate ----------------------------
    execs = [read_csv(f) for f in _todays_files("05_execution", stamp)]
    slip_bps, fill_rate = None, None
    if execs:
        ex = pd.concat(execs, ignore_index=True)
        filled = ex[ex["status"] == "FILLED"]
        attempted = ex[ex["status"].isin(["FILLED", "OPEN"])]
        if len(filled):
            slip_bps = round(filled["slippage_bps"].astype(float).mean(), 1)
        if len(attempted):
            fill_rate = round(len(filled) / len(attempted), 3)
        logging.info("fills today: %d/%d (fill rate %s), avg slippage %s bps",
                     len(filled), len(attempted), fill_rate, slip_bps)
    rows.append({"section": "execution", "key": "avg_slippage_bps",
                 "value": slip_bps, "expected": 0})
    rows.append({"section": "execution", "key": "fill_rate",
                 "value": fill_rate, "expected": 1})

    df = pd.DataFrame(rows, columns=["section", "key", "value", "expected"])
    out = build_path(PREFIX, stamp)
    write_csv(df, out)

    cat_lines = [f"  {r['key']}: {r['value']:+.2f}" for r in rows
                 if r["section"] == "pnl_by_category"]
    send("\n".join([
        f"PnL report {stamp}",
        f"equity {equity:.2f} (start {account['equity_start']:.2f})",
        f"pnl total {total_pnl:+.2f} | realized {account['realized_pnl']:+.2f}",
        "by category:", *cat_lines,
        f"open orders: {len(account['open_orders'])}",
        f"fill rate {fill_rate} | avg slippage {slip_bps} bps",
    ]), "pnl")
    return out


if __name__ == "__main__":
    run(parse_args())
