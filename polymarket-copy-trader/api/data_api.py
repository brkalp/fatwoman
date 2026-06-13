"""
HTTP client for Polymarket's public Data API and Gamma API.
"""
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

_DATA_BASE = "https://data-api.polymarket.com"
_GAMMA_BASE = "https://gamma-api.polymarket.com"


class PolymarketDataAPI:
    def __init__(self, timeout: int = 15):
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers["User-Agent"] = "polymarket-copy-trader/1.0"

    # ── Activity / positions ──────────────────────────────────────────────────

    def get_user_activity(self, address: str, limit: int = 100) -> List[Dict]:
        """
        Returns recent activity for a wallet (newest first).
        Each entry has: type, side, asset (token_id), market (condition_id),
        price, size, usdcSize, timestamp / createdAt, transactionHash.
        """
        try:
            r = self._session.get(
                f"{_DATA_BASE}/activity",
                params={"user": address, "limit": limit},
                timeout=self._timeout,
            )
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, list) else data.get("data", [])
        except Exception as exc:
            logger.error("get_user_activity(%s): %s", address[:10], exc)
            return []

    def get_user_positions(self, address: str) -> List[Dict]:
        """Returns current open positions for a wallet."""
        try:
            r = self._session.get(
                f"{_DATA_BASE}/positions",
                params={"user": address},
                timeout=self._timeout,
            )
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, list) else data.get("data", [])
        except Exception as exc:
            logger.error("get_user_positions(%s): %s", address[:10], exc)
            return []

    # ── Market details ────────────────────────────────────────────────────────

    def get_market(self, condition_id: str) -> Optional[Dict]:
        """
        Returns Gamma market dict with keys: conditionId, question,
        minimum_tick_size (or minTickSize), neg_risk (or negRisk).
        """
        try:
            r = self._session.get(
                f"{_GAMMA_BASE}/markets",
                params={"conditionIds": condition_id},
                timeout=self._timeout,
            )
            r.raise_for_status()
            data = r.json()
            return data[0] if isinstance(data, list) and data else None
        except Exception as exc:
            logger.error("get_market(%s): %s", condition_id[:12], exc)
            return None

    def get_market_by_token(self, token_id: str) -> Optional[Dict]:
        """Lookup market via CLOB token ID."""
        try:
            r = self._session.get(
                f"{_GAMMA_BASE}/markets",
                params={"clob_token_ids": token_id},
                timeout=self._timeout,
            )
            r.raise_for_status()
            data = r.json()
            return data[0] if isinstance(data, list) and data else None
        except Exception as exc:
            logger.error("get_market_by_token(%s): %s", token_id[:12], exc)
            return None
