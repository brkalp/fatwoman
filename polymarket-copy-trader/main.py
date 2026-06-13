"""
Polymarket Copy Trader
Run:  python main.py
      python main.py --summary   (print DB summary and exit)
"""
import argparse
import logging
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional

import config
from db.database import Database
from api.data_api import PolymarketDataAPI
from api.clob import ClobOrderPlacer
from tracker.tracker import PortfolioTracker
from replicator.replicator import TradeReplicator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-22s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("copy_trader.log"),
    ],
)
logger = logging.getLogger("main")


# ── Telegram helper ───────────────────────────────────────────────────────────

def _telegram(text: str):
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": config.TELEGRAM_CHAT_ID, "text": text},
            timeout=5,
        )
    except Exception as exc:
        logger.warning("Telegram failed: %s", exc)


# ── Per-wallet polling ────────────────────────────────────────────────────────

def _process_wallet(
    wallet: Dict,
    tracker: PortfolioTracker,
    replicator: TradeReplicator,
) -> int:
    """Poll one wallet, replicate new trades. Returns number of new trades found."""
    address = wallet["address"]
    alias = wallet["alias"] or address[:10] + "..."

    new_trades = tracker.fetch_new_trades(address)
    if not new_trades:
        return 0

    logger.info("%s  →  %d new trade(s) detected", alias, len(new_trades))

    for trade in new_trades:
        tracker._db.save_detected_trade(trade)
        status = replicator.replicate(trade)

        if status in ("PLACED", "DRY_RUN"):
            verb = "would place" if status == "DRY_RUN" else "placed"
            copy_size = round(trade["size"] * config.COPY_RATIO, 2)
            _telegram(
                f"[CopyTrader] {verb.upper()}\n"
                f"Source: {alias}\n"
                f"Side: {trade['side']}  {copy_size} shares\n"
                f"Price: {trade['price']:.4f}\n"
                f"Market: {trade['market_id'][:24]}..."
            )

    return len(new_trades)


# ── Summary ───────────────────────────────────────────────────────────────────

def print_summary(db: Database):
    s = db.get_summary()
    print(f"\n{'─'*50}")
    print(f"  Tracked wallets : {s['tracked_wallets']}")
    print(f"  Detected trades : {s['detected_trades']}")
    print(f"  Copy trades     :")
    for status, count in s.get("copy_trades", {}).items():
        print(f"    {status:<12}: {count}")
    print(f"{'─'*50}")

    recent = db.get_recent_copy_trades(10)
    if recent:
        print("  Recent copy trades:")
        for t in recent:
            print(
                f"    {t['placed_at'][:19]}  {t['side']:<4}  "
                f"{t['size']:.2f}@{t['price']:.4f}  {t['status']}"
            )
    print()


# ── Main loop ─────────────────────────────────────────────────────────────────

def run():
    db = Database(config.DB_PATH)
    data_api = PolymarketDataAPI()

    # Sync config wallets into DB
    for w in config.TRACKED_WALLETS:
        db.upsert_wallet(w["address"], w.get("alias", ""))

    # CLOB client — only when live trading is requested
    clob: Optional[ClobOrderPlacer] = None
    if not config.DRY_RUN:
        if not config.PRIVATE_KEY:
            logger.error("DRY_RUN=False but PRIVATE_KEY is not set. Falling back to DRY_RUN.")
        else:
            try:
                clob = ClobOrderPlacer(config.PRIVATE_KEY, config.CHAIN_ID)
            except Exception as exc:
                logger.error("CLOB init failed: %s — falling back to DRY_RUN.", exc)

    tracker = PortfolioTracker(db, data_api)
    replicator = TradeReplicator(db, data_api, clob)

    wallets = db.get_active_wallets()
    mode = "LIVE" if (not config.DRY_RUN and clob) else "DRY_RUN"

    if not wallets:
        logger.warning(
            "No wallets configured. Edit TRACKED_WALLETS in config.py and restart."
        )

    logger.info(
        "Starting  mode=%s  wallets=%d  interval=%ds",
        mode, len(wallets), config.POLLING_INTERVAL_SECONDS,
    )

    while True:
        try:
            wallets = db.get_active_wallets()

            if wallets:
                workers = min(len(wallets), 5)
                with ThreadPoolExecutor(max_workers=workers) as pool:
                    futures = {
                        pool.submit(_process_wallet, w, tracker, replicator): w
                        for w in wallets
                    }
                    for future in as_completed(futures):
                        w = futures[future]
                        try:
                            future.result()
                        except Exception as exc:
                            logger.error(
                                "Error processing %s: %s",
                                w.get("alias") or w["address"][:10], exc,
                            )

        except KeyboardInterrupt:
            logger.info("Shutting down.")
            break
        except Exception as exc:
            logger.error("Unexpected error: %s", exc)

        time.sleep(config.POLLING_INTERVAL_SECONDS)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Polymarket Copy Trader")
    parser.add_argument(
        "--summary", action="store_true",
        help="Print DB summary and exit (no polling)",
    )
    args = parser.parse_args()

    if args.summary:
        print_summary(Database(config.DB_PATH))
    else:
        run()
