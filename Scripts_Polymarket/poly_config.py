""" Created on 14-06-2026 @author: ripintheblue """
import os

# ── Wallets to track ──────────────────────────────────────────────────────────
TRACKED_WALLETS = [
    # {"address": "0xABCDEF1234...", "alias": "whale_1"},
    # {"address": "0x9876543210...", "alias": "sharp_trader"},
]

# ── Copy settings ─────────────────────────────────────────────────────────────
COPY_RATIO         = 0.1   # 0.1 = copy 10% of tracked user's share size
MIN_ORDER_SIZE_USD = 2.0   # skip if copy USD value is below this (Polymarket min is $1)
COPY_SELLS         = True  # mirror SELL trades too (close positions they close)
MAX_PRICE          = 0.95  # skip shares priced above this (near-certain outcome)
MIN_PRICE          = 0.05  # skip shares priced below this (near-zero outcome)

# ── Polling ───────────────────────────────────────────────────────────────────
POLLING_INTERVAL_SECONDS = 60

# ── Database path ─────────────────────────────────────────────────────────────
try:
    from fatwoman_dir_setup import polymarket_tracker_db
    DB_PATH = polymarket_tracker_db
except ImportError:
    DB_PATH = 'polymarket_tracker.db'

# ── Execution mode ────────────────────────────────────────────────────────────
DRY_RUN = True  # set False + PRIVATE_KEY to place real orders

# ── Credentials ─────────────────────────────────────────────────────────────
try:
    from fatwoman_api_setup import POLYMARKET_CREDS
    PRIVATE_KEY = POLYMARKET_CREDS
except ImportError:
    PRIVATE_KEY = None  # "0xYOUR_PRIVATE_KEY_HERE"

CHAIN_ID = 137  # Polygon mainnet

# ── Optional Telegram notifications ──────────────────────────────────────────
try:
    from fatwoman_api_setup import tg_bot_credentials
    TELEGRAM_BOT_TOKEN = tg_bot_credentials.get('token')
    TELEGRAM_CHAT_ID   = str(tg_bot_credentials.get('listeners', [None])[0])
except Exception:
    TELEGRAM_BOT_TOKEN = None
    TELEGRAM_CHAT_ID   = None
