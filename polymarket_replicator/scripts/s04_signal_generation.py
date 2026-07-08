"""Step 4 - Signal generation (hourly).

Replicates trades of the selected users into our own trade plan:
- fetches each selected user's trades over the lookback window,
- position sizing per trader: copy_fraction = trade_usdc / trader account,
  my_notional = equity * category_allocation * user_weight * copy_fraction
  * 100, capped per market, dropped below min ticket,
- checks the latest trade plan and skips signals already generated (dedupe),
- when a user has dropped out of the index, emits close signals for every
  position we copied from him,
- labels every signal with its reason: user_open_trade, user_close_trade,
  user_out_of_index.

Writes two files:
  04_users_trade_list_YYYYMMDDHHMM_xx.csv  (raw trades of the users)
  04_trade_plan_YYYYMMDDHHMM_xx.csv        (our sized, deduped plan)
"""
import _bootstrap  # noqa: F401
import hashlib
import logging
from datetime import timedelta

import pandas as pd

from core.cli import make_parser, parse_as_of
from core.config import load_config
from core.io_utils import (build_path, latest_file, load_state, minute_stamp,
                           read_csv, write_csv)
from core.polymarket_api import get_api

TRADES_PREFIX = "04_users_trade_list"
PLAN_PREFIX = "04_trade_plan"

PLAN_COLUMNS = ["signal_id", "ts", "reason", "proxy_wallet", "user_name",
                "category", "condition_id", "question", "side", "outcome",
                "signal_price", "user_usdc_size", "my_notional_usdc"]


def parse_args(argv=None):
    return make_parser(__doc__).parse_args(argv)


def _signal_id(*parts) -> str:
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:16]


def _size_signal(trade, user, cfg) -> float:
    port = cfg["portfolio"]
    alloc = port["category_allocation"].get(user["category"], 0.1)
    copy_fraction = trade["usdc_size"] / max(user["account_size"], 1.0)
    notional = (port["account_equity"] * alloc * user["weight"]
                * copy_fraction * port.get("copy_scale", 100))
    return round(min(notional, port["max_position_per_market"]), 2)


def run(args):
    cfg = load_config()
    if args.mock:
        cfg["mock_api"] = True
    as_of = parse_as_of(args.as_of)
    api = get_api(cfg, as_of=as_of)
    stamp = minute_stamp(as_of)

    sel_file = latest_file("03_selected_user_list", backtest=args.backtest)
    if sel_file is None:
        raise SystemExit("no selected user list - run the daily steps 1-3 first")
    index_users = read_csv(sel_file)
    logging.info("index %s: %d users", sel_file.name, len(index_users))

    # dedupe base: signal ids already in the latest plan
    prev_plan_file = latest_file(PLAN_PREFIX, backtest=args.backtest)
    prev_ids = set()
    if prev_plan_file is not None:
        prev_ids = set(read_csv(prev_plan_file)["signal_id"].astype(str))
        logging.info("dedupe against %s (%d signals)", prev_plan_file.name, len(prev_ids))

    since = api.now() - timedelta(minutes=cfg["signal"]["lookback_minutes"])
    logging.info("replication window: %s -> %s (%d min lookback)",
                 since.strftime("%m-%d %H:%M"), api.now().strftime("%m-%d %H:%M"),
                 cfg["signal"]["lookback_minutes"])
    raw_trades, plan = [], []
    skipped_dupes = skipped_small = 0

    for _, user in index_users.iterrows():
        try:
            trades = api.user_activity(user["proxy_wallet"], since)
        except Exception as exc:  # noqa: BLE001
            logging.error("activity fetch failed for %s: %s", user["proxy_wallet"], exc)
            continue
        for t in trades:
            raw_trades.append({**t, "proxy_wallet": user["proxy_wallet"],
                               "user_name": user["user_name"],
                               "category": user["category"]})
            sid = _signal_id(user["proxy_wallet"], t["condition_id"],
                             t["side"], t["trade_id"])
            if sid in prev_ids:
                skipped_dupes += 1
                continue
            notional = _size_signal(t, user, cfg)
            if notional < cfg["portfolio"]["min_ticket_usdc"]:
                skipped_small += 1
                continue
            plan.append({
                "signal_id": sid,
                "ts": t["ts"],
                "reason": "user_open_trade" if t["side"] == "BUY" else "user_close_trade",
                "proxy_wallet": user["proxy_wallet"],
                "user_name": user["user_name"],
                "category": user["category"],
                "condition_id": t["condition_id"],
                "question": t["question"],
                "side": t["side"],
                "outcome": t["outcome"],
                "signal_price": t["price"],
                "user_usdc_size": t["usdc_size"],
                "my_notional_usdc": notional,
            })

    # users we hold copies from but who are no longer in the index -> close
    # (live-account state is irrelevant when backtesting)
    copied = {} if args.backtest else load_state("copied_positions", {})
    index_wallets = set(index_users["proxy_wallet"])
    for wallet, positions in copied.items():
        if wallet in index_wallets:
            continue
        for cond, pos in positions.items():
            if pos.get("shares", 0) <= 0:
                continue
            sid = _signal_id(wallet, cond, "CLOSE", stamp[:8])  # 1 close/day max
            if sid in prev_ids:
                continue
            price = api.market_price(cond)
            plan.append({
                "signal_id": sid,
                "ts": api.now().isoformat(),
                "reason": "user_out_of_index",
                "proxy_wallet": wallet,
                "user_name": pos.get("user_name", ""),
                "category": pos.get("category", "Other"),
                "condition_id": cond,
                "question": pos.get("question", ""),
                "side": "SELL",
                "outcome": pos.get("outcome", ""),
                "signal_price": price,
                "user_usdc_size": 0.0,
                "my_notional_usdc": round(pos["shares"] * price, 2),
            })
            logging.info("user %s out of index -> closing %s", wallet[:10], cond[:12])

    trades_df = pd.DataFrame(raw_trades)
    plan_df = pd.DataFrame(plan, columns=PLAN_COLUMNS)
    write_csv(trades_df, build_path(TRADES_PREFIX, stamp, backtest=args.backtest))
    plan_path = build_path(PLAN_PREFIX, stamp, backtest=args.backtest)
    if plan_path.exists():
        # same-minute rerun: merge so not-yet-executed signals are never lost
        plan_df = (pd.concat([read_csv(plan_path), plan_df], ignore_index=True)
                     .drop_duplicates("signal_id")[PLAN_COLUMNS])
    write_csv(plan_df, plan_path)
    logging.info("signals: %d in plan (%d user trades seen, %d dupes skipped, "
                 "%d below min ticket)", len(plan_df), len(trades_df),
                 skipped_dupes, skipped_small)
    for reason, grp in plan_df.groupby("reason"):
        logging.info("plan %-18s: %3d signals, %9.2f usdc notional",
                     reason, len(grp), grp["my_notional_usdc"].sum())
    return plan_path


if __name__ == "__main__":
    run(parse_args())
