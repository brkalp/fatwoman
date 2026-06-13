"""
TradeReplicator: validates a detected trade and places a proportional copy order.
"""
import logging
from typing import Dict, Optional

import config
from db.database import Database
from api.data_api import PolymarketDataAPI
from api.clob import ClobOrderPlacer

logger = logging.getLogger(__name__)

# Possible statuses stored in copy_trades
PLACED   = "PLACED"
DRY_RUN  = "DRY_RUN"
SKIPPED  = "SKIPPED"
FAILED   = "FAILED"


class TradeReplicator:
    def __init__(self, db: Database, data_api: PolymarketDataAPI,
                 clob: Optional[ClobOrderPlacer]):
        self._db = db
        self._data_api = data_api
        self._clob = clob

    def replicate(self, trade: Dict) -> str:
        """
        Validate and (optionally) execute a copy of `trade`.
        Returns the status string recorded to the DB.
        """
        side = trade["side"]
        price = trade["price"]
        label = f"{trade['wallet_address'][:10]}... {side} {trade['size']:.2f}@{price:.3f}"

        # ── Filters ───────────────────────────────────────────────────────────
        if side == "SELL" and not config.COPY_SELLS:
            return self._record(trade, SKIPPED, "COPY_SELLS disabled")

        if price > config.MAX_PRICE:
            return self._record(trade, SKIPPED, f"price {price:.3f} > MAX_PRICE {config.MAX_PRICE}")

        if price < config.MIN_PRICE:
            return self._record(trade, SKIPPED, f"price {price:.3f} < MIN_PRICE {config.MIN_PRICE}")

        copy_size = round(trade["size"] * config.COPY_RATIO, 2)
        copy_usdc = round(copy_size * price, 4)

        if copy_usdc < config.MIN_ORDER_SIZE_USD:
            return self._record(
                trade, SKIPPED,
                f"copy value ${copy_usdc:.2f} < min ${config.MIN_ORDER_SIZE_USD}",
                copy_size=copy_size,
            )

        # ── Market details (tick_size, neg_risk) ──────────────────────────────
        tick_size, neg_risk = self._fetch_market_params(trade["market_id"], trade["token_id"])

        # ── Execute ───────────────────────────────────────────────────────────
        if config.DRY_RUN or self._clob is None:
            logger.info(
                "[DRY RUN] %s | copy %.2f shares @ %.4f (~$%.2f)",
                label, copy_size, price, copy_usdc,
            )
            return self._record(trade, DRY_RUN, copy_size=copy_size)

        order_id = self._clob.place_order(
            token_id=trade["token_id"],
            side=side,
            price=price,
            size=copy_size,
            tick_size=tick_size,
            neg_risk=neg_risk,
        )

        if order_id:
            logger.info("Replicated %s → order %s", label, order_id)
            return self._record(trade, PLACED, order_id=order_id, copy_size=copy_size)

        return self._record(trade, FAILED, "CLOB returned no order_id", copy_size=copy_size)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _fetch_market_params(self, market_id: str, token_id: str):
        """Returns (tick_size_str, neg_risk_bool). Falls back to safe defaults."""
        market = self._data_api.get_market(market_id)
        if not market and token_id:
            market = self._data_api.get_market_by_token(token_id)
        if market:
            tick_size = str(
                market.get("minimum_tick_size")
                or market.get("minTickSize")
                or "0.01"
            )
            neg_risk = bool(market.get("neg_risk") or market.get("negRisk", False))
            return tick_size, neg_risk
        return "0.01", False

    def _record(self, trade: Dict, status: str, error: Optional[str] = None,
                order_id: Optional[str] = None, copy_size: float = 0) -> str:
        if copy_size == 0:
            copy_size = round(trade["size"] * config.COPY_RATIO, 2)
        self._db.save_copy_trade(
            source_trade_id=trade["id"],
            source_wallet=trade["wallet_address"],
            market_id=trade["market_id"],
            token_id=trade["token_id"],
            side=trade["side"],
            price=trade["price"],
            size=copy_size,
            status=status,
            error_msg=error,
            order_id=order_id,
        )
        return status
