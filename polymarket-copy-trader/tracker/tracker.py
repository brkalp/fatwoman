"""
PortfolioTracker: polls a wallet's Polymarket activity and returns new trades
since the last time it was checked.
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict

from db.database import Database
from api.data_api import PolymarketDataAPI

logger = logging.getLogger(__name__)


class PortfolioTracker:
    def __init__(self, db: Database, api: PolymarketDataAPI):
        self._db = db
        self._api = api

    def fetch_new_trades(self, address: str) -> List[Dict]:
        """
        Returns all TRADE activities for `address` newer than the stored cursor.
        Side effect: advances the cursor to the latest trade timestamp seen.
        """
        last_ts = self._db.get_cursor(address)
        activities = self._api.get_user_activity(address, limit=100)

        new_trades: List[Dict] = []
        max_ts = last_ts

        for activity in activities:
            ts = _parse_timestamp(activity)
            if ts <= last_ts:
                # Activity API returns newest-first; once we hit old entries we can stop
                break

            # Only handle actual trade events
            activity_type = (activity.get("type") or "TRADE").upper()
            if activity_type not in ("TRADE",):
                continue

            trade_id = _extract_id(activity, address, ts)

            if self._db.trade_exists(trade_id):
                continue

            price = float(activity.get("price") or 0)
            size = float(activity.get("size") or activity.get("amount") or 0)
            if price <= 0 or size <= 0:
                logger.debug("Skipping activity with price=%.4f size=%.4f", price, size)
                continue

            trade = {
                "id": trade_id,
                "wallet_address": address,
                "market_id": activity.get("market") or activity.get("conditionId") or "",
                "token_id": activity.get("asset") or activity.get("tokenId") or "",
                "side": (activity.get("side") or "BUY").upper(),
                "price": price,
                "size": size,
                "usdc_size": float(activity.get("usdcSize") or activity.get("cashPayout") or 0),
                "timestamp": ts,
            }

            if not trade["market_id"] or not trade["token_id"]:
                logger.warning("Trade %s missing market_id or token_id, skipping", trade_id)
                continue

            new_trades.append(trade)
            max_ts = max(max_ts, ts)

        if max_ts > last_ts:
            self._db.set_cursor(address, max_ts)

        if new_trades:
            logger.info("Wallet %s...: %d new trade(s)", address[:10], len(new_trades))

        return new_trades


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_timestamp(activity: Dict) -> int:
    """Extract a unix timestamp (int) from an activity dict."""
    raw = activity.get("timestamp") or activity.get("createdAt") or 0
    if isinstance(raw, (int, float)):
        return int(raw)
    if isinstance(raw, str):
        # ISO-8601 string e.g. "2025-11-01T12:34:56Z"
        try:
            raw = raw.replace("Z", "+00:00")
            return int(datetime.fromisoformat(raw).replace(tzinfo=timezone.utc).timestamp())
        except ValueError:
            pass
    return 0


def _extract_id(activity: Dict, address: str, ts: int) -> str:
    """Return the best unique identifier for this activity."""
    return (
        activity.get("id")
        or activity.get("transactionHash")
        or activity.get("txHash")
        # Fallback: synthetic key that won't collide across wallets
        or f"{address}_{ts}_{activity.get('asset', '')}_{activity.get('side', '')}"
    )
