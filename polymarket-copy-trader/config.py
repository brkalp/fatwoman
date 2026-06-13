"""
Polymarket Copy Trader – Configuration
Edit this file to set up your tracked wallets and credentials.
"""

# ── Wallets to track ──────────────────────────────────────────────────────────
# Add wallet addresses of Polymarket traders you want to copy.
TRACKED_WALLETS = [
    # {"address": "0xABCDEF1234...", "alias": "whale_1"},
    # {"address": "0x9876543210...", "alias": "sharp_trader"},
]

# ── Copy settings ─────────────────────────────────────────────────────────────
COPY_RATIO = 0.1          # 0.1 = copy 10% of the tracked user's share size
MIN_ORDER_SIZE_USD = 2.0  # Skip copy if USD value is below this (Polymarket min is $1)
COPY_SELLS = True         # Mirror SELL trades too (close positions they close)
MAX_PRICE = 0.95          # Skip shares priced above this (near-certain outcome)
MIN_PRICE = 0.05          # Skip shares priced below this (near-zero outcome)

# ── Polling ───────────────────────────────────────────────────────────────────
POLLING_INTERVAL_SECONDS = 60  # How often to check for new trades

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH = "polymarket_tracker.db"

# ── Execution mode ────────────────────────────────────────────────────────────
# Set to False (and fill in PRIVATE_KEY) to place real orders
DRY_RUN = True

# ── Your Polymarket credentials ───────────────────────────────────────────────
# Required only when DRY_RUN = False.
# Use the private key of the wallet you want to trade from.
PRIVATE_KEY = None  # "0xYOUR_PRIVATE_KEY_HERE"

# Polygon mainnet (do not change for Polymarket)
CHAIN_ID = 137

# ── Optional Telegram notifications ──────────────────────────────────────────
TELEGRAM_BOT_TOKEN = None  # "123456:ABC-DEFxxx"
TELEGRAM_CHAT_ID = None    # "123456789"
