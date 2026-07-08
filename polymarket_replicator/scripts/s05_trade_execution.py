"""Step 5 - Hourly trade execution.

Executes pending signals from the recent step-4 trade plans:
- HALT file check (touch HALT in the project root to stop all trading),
- retries still-open limit orders from earlier runs against the current
  market before placing anything new,
- max orders per hour limit, dry-run option (config or --dry-run; dry runs
  never consume signals or touch state),
- risk management: max total notional and max allocation per category
  (open orders reserve budget too) plus a cash constraint,
- limit orders with a slippage buffer, DAY time-in-force; paper mode
  simulates fills against the current market price,
- signal lifecycle: FILLED / OPEN (day order, retried hourly, expires next
  day) are final; SKIPPED_MAX_ORDERS, SKIPPED_RISK_CAP and SKIPPED_NO_CASH
  stay pending and retry next hour until the signal is older than
  execution.signal_max_age_hours, at which point it EXPIREs,
- logs trades and position sizes via logging.info, sends the order summary
  to the trades telegram channel,
- records fills in 05_execution_YYYYMMDDHHMM_xx.csv for the pnl reporter and
  updates the paper account + copied-positions state.

Live CLOB execution is intentionally not wired: mode=live logs an error and
behaves like dry run until keys and py-clob-client are added.
"""
import _bootstrap  # noqa: F401
import logging
from datetime import datetime, timedelta, timezone

import pandas as pd

from core.cli import make_parser
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

# statuses that consume the signal; the SKIPPED_* rate/risk/cash statuses
# stay pending and are retried on the next hourly run
FINAL_STATUSES = {"FILLED", "OPEN", "SKIPPED_NO_POSITION", "EXPIRED"}

SIG_KEYS = ["signal_id", "reason", "category", "condition_id", "question",
            "side", "outcome", "signal_price", "proxy_wallet", "user_name"]


def parse_args(argv=None):
    return make_parser(__doc__).parse_args(argv)


def _exposure(account, prices):
    """Current notional per category and total - open positions valued at
    market, plus open orders reserving their limit notional."""
    by_cat, total = {}, 0.0
    for cond, pos in account["positions"].items():
        notional = pos["shares"] * prices.get(cond, pos["avg_price"])
        by_cat[pos["category"]] = by_cat.get(pos["category"], 0.0) + notional
        total += notional
    for o in account["open_orders"]:
        if o["side"] == "BUY":
            notional = o["shares"] * o["limit_price"]
            by_cat[o["category"]] = by_cat.get(o["category"], 0.0) + notional
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


def _exec_row(sig, stamp, ex, limit_price, fill_price, shares, status):
    slippage_bps = (round((fill_price - sig["signal_price"])
                          / sig["signal_price"] * 10_000
                          * (1 if sig["side"] == "BUY" else -1), 1)
                    if fill_price else None)
    return {
        "signal_id": sig["signal_id"], "ts": stamp, "reason": sig["reason"],
        "category": sig["category"], "condition_id": sig["condition_id"],
        "question": sig["question"], "side": sig["side"],
        "outcome": sig["outcome"], "order_type": ex["order_type"],
        "tif": ex["time_in_force"], "signal_price": sig["signal_price"],
        "limit_price": limit_price, "fill_price": fill_price,
        "shares": shares,
        "notional_usdc": round(shares * (fill_price or limit_price or 0), 2),
        "status": status, "slippage_bps": slippage_bps,
        "proxy_wallet": sig["proxy_wallet"],
    }


def _retry_open_orders(account, copied, api, ex, stamp, results):
    """Re-check earlier OPEN day orders against the market; fill or keep."""
    still_open = []
    for o in account["open_orders"]:
        sig = o.get("sig")
        if sig is None:  # order from an old state format - keep until expiry
            still_open.append(o)
            continue
        px = api.market_price(o["condition_id"])
        fillable = px <= o["limit_price"] if o["side"] == "BUY" else px >= o["limit_price"]
        if fillable:
            _apply_fill(account, copied, sig, o["shares"], px)
            logging.info("open order filled on retry: %s %s %.2fsh @ %.3f "
                         "(lim %.4f, placed %s)", o["side"], o["condition_id"][:12],
                         o["shares"], px, o["limit_price"], o["ts"])
            results.append(_exec_row(sig, stamp, ex, o["limit_price"], px,
                                     o["shares"], "FILLED"))
        else:
            still_open.append(o)
    account["open_orders"] = still_open


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

    api = get_api(cfg)
    stamp = minute_stamp()
    now = datetime.now(timezone.utc)
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

    # DAY orders: anything still open from an earlier day expires now
    expired_orders = [o for o in account["open_orders"] if o["ts"][:8] < stamp[:8]]
    account["open_orders"] = [o for o in account["open_orders"]
                              if o["ts"][:8] >= stamp[:8]]
    for o in expired_orders:
        logging.info("day order expired unfilled: %s %s %.2fsh lim %.4f",
                     o["side"], o["condition_id"][:12], o["shares"], o["limit_price"])

    results = []
    if not dry_run:
        _retry_open_orders(account, copied, api, ex, stamp, results)

    if plan.empty and not results:
        logging.info("no pending signals and no open-order fills - nothing to do "
                     "(%d plan files checked)", len(plan_files))
        return None
    logging.info("pending: %d signals from %d plan files up to %s "
                 "(dry_run=%s, orders this hour so far: %d/%d)",
                 len(plan), len(plan_files),
                 plan_files[-1].name, dry_run, hour_state["count"],
                 ex["max_orders_per_hour"])

    prices = {c: api.market_price(c) for c in plan["condition_id"].unique()}
    total_notional, by_cat = _exposure(account, prices)
    buffer = ex["limit_slippage_bps"] / 10_000.0
    max_age = timedelta(hours=ex.get("signal_max_age_hours", 3))

    for _, row in plan.iterrows():
        # native python types: sig is embedded in json state for open orders
        sig = {k: (row[k].item() if hasattr(row[k], "item") else row[k])
               for k in SIG_KEYS}
        status, fill_price, shares = "SKIPPED", None, 0.0
        market = prices[sig["condition_id"]]
        limit_price = round(sig["signal_price"] * (1 + buffer if sig["side"] == "BUY"
                                                   else 1 - buffer), 4)
        notional = float(row["my_notional_usdc"])
        sig_age = now - datetime.fromisoformat(str(row["ts"]))

        if sig_age > max_age:
            status = "EXPIRED"
            logging.info("signal expired (%.1fh old > %.0fh): %s %s",
                         sig_age.total_seconds() / 3600,
                         max_age.total_seconds() / 3600,
                         sig["side"], sig["condition_id"][:12])
        elif hour_state["count"] >= ex["max_orders_per_hour"]:
            status = "SKIPPED_MAX_ORDERS"  # pending - retried next hour
        elif sig["side"] == "BUY":
            # risk caps + cash constrain new exposure only
            cat_room = ex["max_category_notional"] - by_cat.get(sig["category"], 0.0)
            total_room = ex["max_total_notional"] - total_notional
            allowed = max(0.0, min(notional, cat_room, total_room))
            if allowed < cfg["portfolio"]["min_ticket_usdc"]:
                status = "SKIPPED_RISK_CAP"  # pending - room may free up
                logging.info("risk cap: %s %s notional %.0f -> room %.0f "
                             "(cat %.0f/%.0f, total %.0f/%.0f)",
                             sig["category"], sig["condition_id"][:12], notional,
                             allowed, by_cat.get(sig["category"], 0.0),
                             ex["max_category_notional"], total_notional,
                             ex["max_total_notional"])
            elif allowed > account["cash"] and not dry_run:
                status = "SKIPPED_NO_CASH"  # pending - sells may free cash
                logging.info("no cash: need %.2f, have %.2f (%s)",
                             allowed, account["cash"], sig["condition_id"][:12])
            else:
                notional = round(allowed, 2)
                shares = round(notional / limit_price, 2)
                if market <= limit_price:
                    status, fill_price = "FILLED", market
                else:
                    status = "OPEN"
        else:  # SELL - close at most what we copied from THIS user
            held = account["positions"].get(sig["condition_id"], {}).get("shares", 0.0)
            copied_here = (copied.get(sig["proxy_wallet"], {})
                           .get(sig["condition_id"], {}).get("shares", 0.0))
            if held <= 0 or copied_here <= 0:
                status = "SKIPPED_NO_POSITION"
            else:
                if sig["reason"] == "user_out_of_index":
                    shares = round(min(held, copied_here), 2)  # full exit of his copy
                else:
                    shares = round(min(held, copied_here,
                                       notional / max(sig["signal_price"], 0.01)), 2)
                if market >= limit_price:
                    status, fill_price = "FILLED", market
                else:
                    status = "OPEN"

        if dry_run and status in ("FILLED", "OPEN"):
            status = "DRY_RUN"

        if status == "FILLED":
            _apply_fill(account, copied, sig, shares, fill_price)
            total_notional, by_cat = _exposure(account, prices)
            hour_state["count"] += 1
        elif status == "OPEN":
            account["open_orders"].append({
                "signal_id": sig["signal_id"], "ts": stamp, "side": sig["side"],
                "condition_id": sig["condition_id"], "limit_price": limit_price,
                "shares": shares, "category": sig["category"], "sig": sig,
            })
            total_notional, by_cat = _exposure(account, prices)
            hour_state["count"] += 1

        logging.info("order %s %s %.2f sh @ lim %.4f (sig %.3f, %s) -> %s%s",
                     sig["side"], sig["condition_id"][:12], shares, limit_price,
                     sig["signal_price"], sig["reason"], status,
                     f" fill {fill_price:.3f}" if fill_price else "")
        results.append(_exec_row(sig, stamp, ex, limit_price, fill_price,
                                 shares, status))
        if status in FINAL_STATUSES and not dry_run:
            executed.append(str(sig["signal_id"]))

    if not dry_run:
        save_state("paper_account", account)
        save_state("copied_positions", copied)
        save_state("orders_this_hour", hour_state)
        save_state("executed_signals", executed[-5000:])

    df = pd.DataFrame(results, columns=EXEC_COLUMNS)
    out = build_path(PREFIX, stamp)
    write_csv(df, out)

    by_status = df["status"].value_counts().to_dict()
    filled = df[df["status"] == "FILLED"]
    logging.info("execution done: %s | filled notional %.2f usdc",
                 ", ".join(f"{k}={v}" for k, v in sorted(by_status.items())),
                 filled["notional_usdc"].sum())
    final_total, final_by_cat = _exposure(account, prices)
    logging.info("exposure after run: total %.2f/%d | %s | cash %.2f",
                 final_total, ex["max_total_notional"],
                 ", ".join(f"{c} {n:.0f}" for c, n in sorted(final_by_cat.items()))
                 or "-", account["cash"])
    if len(df):
        lines = [f"Orders {stamp} (v{out.stem.split('_')[-1]}, dry={dry_run}):"]
        lines += [f"{r.side} {str(r.question)[:40]} {r.shares}sh @ {r.limit_price} "
                  f"[{r.status}] ({r.reason})" for r in df.itertuples()]
        send("\n".join(lines), "trades")
    return out


if __name__ == "__main__":
    run(parse_args())
