import sqlite3
import threading
import logging
from typing import List, Dict, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)
_lock = threading.Lock()


class Database:
    def __init__(self, path: str):
        self.path = path
        self._init_schema()

    @contextmanager
    def _conn(self):
        with _lock:
            conn = sqlite3.connect(self.path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            finally:
                conn.close()

    def _init_schema(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS tracked_wallets (
                    address  TEXT PRIMARY KEY,
                    alias    TEXT,
                    active   INTEGER DEFAULT 1,
                    added_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS activity_cursors (
                    address TEXT PRIMARY KEY,
                    last_ts INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS detected_trades (
                    id             TEXT PRIMARY KEY,
                    wallet_address TEXT,
                    market_id      TEXT,
                    token_id       TEXT,
                    side           TEXT,
                    price          REAL,
                    size           REAL,
                    usdc_size      REAL,
                    timestamp      INTEGER,
                    detected_at    TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS copy_trades (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_trade_id TEXT,
                    source_wallet   TEXT,
                    market_id       TEXT,
                    token_id        TEXT,
                    side            TEXT,
                    price           REAL,
                    size            REAL,
                    status          TEXT,
                    error_msg       TEXT,
                    order_id        TEXT,
                    placed_at       TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

    # ── Wallet management ─────────────────────────────────────────────────────

    def upsert_wallet(self, address: str, alias: str = ""):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO tracked_wallets (address, alias) VALUES (?, ?)
                ON CONFLICT(address) DO UPDATE SET alias=excluded.alias, active=1
            """, (address, alias))
            conn.execute("""
                INSERT OR IGNORE INTO activity_cursors (address, last_ts) VALUES (?, 0)
            """, (address,))

    def deactivate_wallet(self, address: str):
        with self._conn() as conn:
            conn.execute("UPDATE tracked_wallets SET active=0 WHERE address=?", (address,))

    def get_active_wallets(self) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT address, alias FROM tracked_wallets WHERE active=1"
            ).fetchall()
        return [{"address": r["address"], "alias": r["alias"] or ""} for r in rows]

    # ── Cursors (last-seen timestamps per wallet) ─────────────────────────────

    def get_cursor(self, address: str) -> int:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT last_ts FROM activity_cursors WHERE address=?", (address,)
            ).fetchone()
        return int(row["last_ts"]) if row else 0

    def set_cursor(self, address: str, timestamp: int):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO activity_cursors (address, last_ts) VALUES (?, ?)
                ON CONFLICT(address) DO UPDATE SET last_ts=excluded.last_ts
            """, (address, timestamp))

    # ── Detected trades ───────────────────────────────────────────────────────

    def trade_exists(self, trade_id: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM detected_trades WHERE id=?", (trade_id,)
            ).fetchone()
        return row is not None

    def save_detected_trade(self, trade: Dict):
        with self._conn() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO detected_trades
                (id, wallet_address, market_id, token_id, side, price, size, usdc_size, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade["id"], trade["wallet_address"], trade["market_id"],
                trade["token_id"], trade["side"], trade["price"],
                trade["size"], trade["usdc_size"], trade["timestamp"],
            ))

    # ── Copy trades ───────────────────────────────────────────────────────────

    def save_copy_trade(self, source_trade_id: str, source_wallet: str, market_id: str,
                        token_id: str, side: str, price: float, size: float,
                        status: str, error_msg: Optional[str], order_id: Optional[str]):
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO copy_trades
                (source_trade_id, source_wallet, market_id, token_id, side,
                 price, size, status, error_msg, order_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (source_trade_id, source_wallet, market_id, token_id, side,
                  price, size, status, error_msg, order_id))

    def get_summary(self) -> Dict:
        with self._conn() as conn:
            wallets = conn.execute(
                "SELECT COUNT(*) FROM tracked_wallets WHERE active=1"
            ).fetchone()[0]
            detected = conn.execute("SELECT COUNT(*) FROM detected_trades").fetchone()[0]
            statuses = conn.execute(
                "SELECT status, COUNT(*) as n FROM copy_trades GROUP BY status"
            ).fetchall()
        return {
            "tracked_wallets": wallets,
            "detected_trades": detected,
            "copy_trades": {r["status"]: r["n"] for r in statuses},
        }

    def get_recent_copy_trades(self, limit: int = 20) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT source_wallet, market_id, side, price, size, status, error_msg, order_id, placed_at
                FROM copy_trades ORDER BY placed_at DESC LIMIT ?
            """, (limit,)).fetchall()
        return [dict(r) for r in rows]
