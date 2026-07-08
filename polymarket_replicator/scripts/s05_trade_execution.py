"""Step 5 - Hourly trade execution.

Executes the newest trade plan from step 4:
- HALT file check (touch HALT in the project root to stop all trading),
- max orders per hour limit, dry-run option (config or --dry-run),
- risk management: max total notional and max allocation per category,
- limit orders with a slippage buffer, DAY time-in-force; paper mode
  simulates fills against the current market price (an unfillable limit
  stays OPEN and expires with the day),
- logs trades and position sizes via logging.info, sends the order summary
  to the trades telegram channel,
- records fills in 05_execution_YYYYMMDDHHMM_xx.csv for the pnl reporter and
  updates the paper account + copied-positions state.

Live CLOB execution is intentionally not wired: mode=live logs an error and
behaves like dry run until keys and py-clob-client are added.
"""
import _bootstrap  # noqa: F401
import argparse
import logging

import pandas as pd

from core.config import load_config
from core.io_utils import (build_path, data_dir, load_state, minute_stamp,
                           read_csv, save_state, write_csv)
from core.paths import HALT_FILE
from core.polymarket_api import get_api
from core.telegram_client import send

PREFIX = "05_execution"

EXEC_COLUMNS = ["signal_id", "ts", "reason", "category", "condition_id",
                "question", "side", "outcome", "order_type", "tif",
                "signal_price", "limit_price", "fill_price", "shares",
                "notional_usdc", "status", "slippage_bps", "proxy_wallet"]


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--mock", action="store_true")
    return p.parse_args(argv)


def _category_notionals(account, prices):
    by_cat, total = {}, 0.0
    for cond, pos in account["positions"].items():
        notional = pos["shares"] * prices.get(cond, pos["avg_price"])
        by_cat[pos["category"]] = by_cat.get(pos["category"], 0.0) + notional
        total += notional
    return total, by_cat


def _apply_fill(account, copied, sig, shares, fill_price):
    """Book a paper fill into the account and per-source-user copy state."""
    cond, cat = sig["condition_id"], sig["category"]
    pos = account["positions"].get(cond)
    if sig["side"] == "BUY":
        cost = shares * fill_price
        account["cash"] -= cost
        if pos:
            new_shares = pos["shares"] + shares
            pos["avg_price"] = (pos["avg_price"] * pos["shares"] + cost) / new_shares
            pos["shares"] = new_shares
        else:
            account["positions"][cond] = {
                "shares": shares, "avg_price": fill_price, "category": cat,
                "question": sig["question"], "outcome": sig["outcome"],
                "source_wallet": sig["proxy_wallet"], "user_name": sig["user_name"],
            }
        cp = copied.setdefault(sig["proxy_wallet"], {}).setdefault(cond, {
            "shares": 0.0, "category": cat, "question": sig["question"],
            "outcome": sig["outcome"], "user_name": sig["user_name"]})
        cp["shares"] += shares
    else:  # SELL
        if not pos:
            return
        closed = min(shares, pos["shares"])
        account["cash"] += closed * fill_price
        realized = closed * (fill_price - pos["avg_price"])
        account["realized_pnl"] += realized
        account["realized_by_category"][cat] = (
            account["realized_by_category"].get(cat, 0.0) + realized)
        pos["shares"] -= closed
        if pos["shares"] <= 1e-9:
            del account["positions"][cond]
        cp = copied.get(sig["proxy_wallet"], {}).get(cond)
        if cp:
            cp["shares"] = max(0.0, cp["shares"] - closed)
            if cp["shares"] <= 1e-9:
                copied[sig["proxy_wallet"]].pop(cond, None)


def run(args):
    cfg = load_config()
    if args.mock:
        cfg["mock_api"] = True
    ex = cfg["execution"]
    dry_run = args.dry_run or ex["dry_run"]
    if cfg["mode"] not in ("paper",) and not dry_run:
        logging.error("mode=%s live execution not implemented - forcing dry run "
                      "(add py-clob-client + keys to go live)", cfg["mode"])
        dry_run = True

    if HALT_FILE.exists():
        logging.error("HALT file present at %s - no orders will be sent", HALT_FILE)
        send("EXECUTION HALTED - HALT file present, no orders sent", "trades")
        return None

    # catch up over the recent plans (not just the newest) so an hour where
    # execution was skipped or died doesn't orphan its signals
    plan_files = sorted(data_dir().glob("04_trade_plan_*.csv"))[-24:]
    if not plan_files:
        logging.info("no trade plan found - nothing to execute")
        return None
    plan = pd.concat([read_csv(f) for f in plan_files], ignore_index=True)
    plan = plan.drop_duplicates("signal_id")

    executed = load_state("executed_signals", [])
    plan = plan[~plan["signal_id"].astype(str).isin(set(executed))]
    if plan.empty:
        logging.info("all plans up to %s fully executed already - nothing to do",
                     plan_files[-1].name)
        return None
    logging.info("executing %d new signals from %d plan files up to %s (dry_run=%s)",
                 len(plan), len(plan_files), plan_files[-1].name, dry_run)

    api = get_api(cfg)
    stamp = minute_stamp()
    hour_state = load_state("orders_this_hour", {"hour": "", "count": 0})
    if hour_state["hour"] != stamp[:10]:
        hour_state = {"hour": stamp[:10], "count": 0}

    account = load_state("paper_account", {
        "cash": cfg["portfolio"]["account_equity"],
        "equity_start": cfg["portfolio"]["account_equity"],
        "positions": {}, "realized_pnl": 0.0, "realized_by_category": {},
        "open_orders": [],
    })
    copied = load_state("copied_positions", {})
    # DAY orders: anything still open from earlier hours expires now
    expired = [o for o in account["open_orders"] if o["ts"][:8] < stamp[:8]]
    account["open_orders"] = [o for o in account["open_orders"] if o["ts"][:8] >= stamp[:8]]
    for o in expired:
        logging.info("day order expired unfilled: %s %s", o["side"], o["condition_id"][:12])

    prices = {c: api.market_price(c) for c in plan["condition_id"].unique()}
    total_notional, by_cat = _category_notionals(account, prices)
    buffer = ex["limit_slippage_bps"] / 10_000.0

    results = []
    for _, sig in plan.iterrows():
        status, fill_price, shares = "SKIPPED", None, 0.0
        market = prices[sig["condition_id"]]
        limit_price = round(sig["signal_price"] * (1 + buffer if sig["side"] == "BUY"
                                                   else 1 - buffer), 4)
        notional = float(sig["my_notional_usdc"])

        if hour_state["count"] >= ex["max_orders_per_hour"]:
            status = "SKIPPED_MAX_ORDERS"
        elif sig["side"] == "BUY":
            # risk caps apply to new exposure only
            cat_room = ex["max_category_notional"] - by_cat.get(sig["category"], 0.0)
            total_room = ex["max_total_notional"] - total_notional
            allowed = max(0.0, min(notional, cat_room, total_room))
            if allowed < cfg["portfolio"]["min_ticket_usdc"]:
                status = "SKIPPED_RISK_CAP"
                logging.info("risk cap: %s %s notional %.0f -> room %.0f",
                             sig["category"], sig["condition_id"][:12], notional, allowed)
            else:
                notional = round(allowed, 2)
                shares = round(notional / limit_price, 2)
                if market <= limit_price:
                    status, fill_price = "FILLED", market
                else:
                    status = "OPEN"
        else:  # SELL
            held = account["positions"].get(sig["condition_id"], {}).get("shares", 0.0)
            if held <= 0:
                status = "SKIPPED_NO_POSITION"
            else:
                shares = round(min(held, notional / max(sig["signal_price"], 0.01)), 2)
                if sig["reason"] == "user_out_of_index":
                    shares = held  # full exit
                if market >= limit_price:
                    status, fill_price = "FILLED", market
                else:
                    status = "OPEN"

        if dry_run and status in ("FILLED", "OPEN"):
            status = "DRY_RUN"

        if status == "FILLED":
            _apply_fill(account, copied, sig, shares, fill_price)
            total_notional, by_cat = _category_notionals(account, prices)
            hour_state["count"] += 1
        elif status == "OPEN":
            account["open_orders"].append({
                "signal_id": sig["signal_id"], "ts": stamp, "side": sig["side"],
                "condition_id": sig["condition_id"], "limit_price": limit_price,
                "shares": shares, "category": sig["category"],
            })
            hour_state["count"] += 1

        slippage_bps = (round((fill_price - sig["signal_price"])
                              / sig["signal_price"] * 10_000 *
                              (1 if sig["side"] == "BUY" else -1), 1)
                        if fill_price else None)
        logging.info("order %s %s %.2f sh @ lim %.3f (sig %.3f) -> %s%s",
                     sig["side"], sig["condition_id"][:12], shares, limit_price,
                     sig["signal_price"], status,
                     f" fill {fill_price:.3f}" if fill_price else "")
        results.append({
            "signal_id": sig["signal_id"], "ts": stamp, "reason": sig["reason"],
            "category": sig["category"], "condition_id": sig["condition_id"],
            "question": sig["question"], "side": sig["side"],
            "outcome": sig["outcome"], "order_type": ex["order_type"],
            "tif": ex["time_in_force"], "signal_price": sig["signal_price"],
            "limit_price": limit_price, "fill_price": fill_price,
            "shares": shares, "notional_usdc": round(shares * (fill_price or limit_price), 2),
            "status": status, "slippage_bps": slippage_bps,
            "proxy_wallet": sig["proxy_wallet"],
        })
        executed.append(str(sig["signal_id"]))

    if not dry_run:
        save_state("paper_account", account)
        save_state("copied_positions", copied)
        save_state("orders_this_hour", hour_state)
    save_state("executed_signals", executed[-5000:])

    df = pd.DataFrame(results, columns=EXEC_COLUMNS)
    out = build_path(PREFIX, stamp)
    write_csv(df, out)

    filled = df[df["status"] == "FILLED"]
    logging.info("execution done: %d filled, %d open, %d skipped/dry",
                 len(filled), (df["status"] == "OPEN").sum(),
                 len(df) - len(filled) - (df["status"] == "OPEN").sum())
    if len(df):
        lines = [f"Orders {stamp} (v{out.stem.split('_')[-1]}, dry={dry_run}):"]
        lines += [f"{r.side} {str(r.question)[:40]} {r.shares}sh @ {r.limit_price} "
                  f"[{r.status}] ({r.reason})" for r in df.itertuples()]
        send("\n".join(lines), "trades")
    return out


if __name__ == "__main__":
    run(parse_args())
