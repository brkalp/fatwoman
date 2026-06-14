""" Created on 14-06-2026 @author: ripintheblue """
import sys
import os
# Add fatwoman setup modules to path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _d in ['Scripts_Setup_Logger', 'Scripts_Setup_Dirs']:
    sys.path.insert(0, os.path.join(_ROOT, _d))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Scripts_Polymarket/ itself

from fatwoman_log_setup import script_end_log
import logging
import time
import argparse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Optional

import poly_config as config
from db.poly_db import Database
from api.data_api import PolymarketDataAPI
from api.clob import ClobOrderPlacer
from tracker.tracker import PortfolioTracker
from replicator.replicator import TradeReplicator


def _telegram(text: str):
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        return
    try:
        requests.post(
            "https://api.telegram.org/bot%s/sendMessage" % config.TELEGRAM_BOT_TOKEN,
            json={"chat_id": config.TELEGRAM_CHAT_ID, "text": text},
            timeout=5,
        )
    except Exception as e:
        logging.warning("Telegram failed: %s", e)


def _process_wallet(wallet: Dict, tracker: PortfolioTracker,
                    replicator: TradeReplicator) -> int:
    address = wallet["address"]
    alias   = wallet["alias"] or address[:10] + "..."

    new_trades = tracker.fetch_new_trades(address)
    if not new_trades:
        return 0

    logging.info("%s -> %d new trade(s) detected", alias, len(new_trades))

    for trade in new_trades:
        tracker._db.save_detected_trade(trade)
        status = replicator.replicate(trade)

        if status in ("PLACED", "DRY_RUN"):
            verb      = "WOULD PLACE" if status == "DRY_RUN" else "PLACED"
            copy_size = round(trade["size"] * config.COPY_RATIO, 2)
            _telegram(
                "[CopyTrader] %s\nSource: %s\nSide: %s  %.2f shares\nPrice: %.4f\nMarket: %s..."
                % (verb, alias, trade["side"], copy_size, trade["price"], trade["market_id"][:24])
            )
    return len(new_trades)


def print_summary(db: Database):
    s = db.get_summary()
    print("\n" + "-" * 50)
    print("  Tracked wallets : %d" % s["tracked_wallets"])
    print("  Detected trades : %d" % s["detected_trades"])
    print("  Copy trades     :")
    for status, count in s.get("copy_trades", {}).items():
        print("    %-12s: %d" % (status, count))
    print("-" * 50)
    for t in db.get_recent_copy_trades(10):
        print("  %s  %-4s  %.2f@%.4f  %s" % (
            t["placed_at"][:19], t["side"], t["size"], t["price"], t["status"]))
    print()


def run():
    db       = Database(config.DB_PATH)
    data_api = PolymarketDataAPI()

    for w in config.TRACKED_WALLETS:
        db.upsert_wallet(w["address"], w.get("alias", ""))

    clob: Optional[ClobOrderPlacer] = None
    if not config.DRY_RUN:
        if not config.PRIVATE_KEY:
            logging.error("DRY_RUN=False but PRIVATE_KEY not set — falling back to DRY_RUN")
        else:
            try:
                clob = ClobOrderPlacer(config.PRIVATE_KEY, config.CHAIN_ID)
            except Exception as e:
                logging.error("CLOB init failed: %s — falling back to DRY_RUN", e)

    tracker    = PortfolioTracker(db, data_api)
    replicator = TradeReplicator(db, data_api, clob)
    wallets    = db.get_active_wallets()
    mode       = "LIVE" if (not config.DRY_RUN and clob) else "DRY_RUN"

    if not wallets:
        logging.warning("No wallets configured — edit TRACKED_WALLETS in poly_config.py")

    logging.info("Starting | mode=%s | wallets=%d | interval=%ds",
                 mode, len(wallets), config.POLLING_INTERVAL_SECONDS)

    while True:
        try:
            wallets = db.get_active_wallets()
            if wallets:
                with ThreadPoolExecutor(max_workers=min(len(wallets), 5)) as pool:
                    futures = {
                        pool.submit(_process_wallet, w, tracker, replicator): w
                        for w in wallets
                    }
                    for future in as_completed(futures):
                        w = futures[future]
                        try:
                            future.result()
                        except Exception as e:
                            logging.error("Error processing %s: %s",
                                          w.get("alias") or w["address"][:10], e)
        except KeyboardInterrupt:
            logging.info("Shutting down.")
            break
        except Exception as e:
            logging.error("Unexpected error: %s", e)

        time.sleep(config.POLLING_INTERVAL_SECONDS)

    script_end_log()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Polymarket Copy Trader")
    parser.add_argument("--summary", action="store_true",
                        help="Print DB summary and exit")
    args = parser.parse_args()

    if args.summary:
        print_summary(Database(config.DB_PATH))
    else:
        run()
