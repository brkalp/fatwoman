""" Created on 14-06-2026 @author: ripintheblue """
import logging
from typing import Dict, Optional

import poly_config as config
from db.poly_db import Database
from api.data_api import PolymarketDataAPI
from api.clob import ClobOrderPlacer

PLACED  = "PLACED"
DRY_RUN = "DRY_RUN"
SKIPPED = "SKIPPED"
FAILED  = "FAILED"


class TradeReplicator:
    def __init__(self, db: Database, data_api: PolymarketDataAPI,
                 clob: Optional[ClobOrderPlacer]):
        self._db       = db
        self._data_api = data_api
        self._clob     = clob

    def replicate(self, trade: Dict) -> str:
        side  = trade["side"]
        price = trade["price"]
        label = "%s... %s %.2f@%.3f" % (trade["wallet_address"][:10], side, trade["size"], price)

        if side == "SELL" and not config.COPY_SELLS:
            return self._record(trade, SKIPPED, "COPY_SELLS disabled")
        if price > config.MAX_PRICE:
            return self._record(trade, SKIPPED, "price %.3f > MAX_PRICE" % price)
        if price < config.MIN_PRICE:
            return self._record(trade, SKIPPED, "price %.3f < MIN_PRICE" % price)

        copy_size = round(trade["size"] * config.COPY_RATIO, 2)
        copy_usdc = round(copy_size * price, 4)
        if copy_usdc < config.MIN_ORDER_SIZE_USD:
            return self._record(trade, SKIPPED,
                                "copy $%.2f < min $%.2f" % (copy_usdc, config.MIN_ORDER_SIZE_USD),
                                copy_size=copy_size)

        tick_size, neg_risk = self._market_params(trade["market_id"], trade["token_id"])

        if config.DRY_RUN or self._clob is None:
            logging.info("[DRY RUN] %s | copy %.2f shares @ %.4f (~$%.2f)",
                         label, copy_size, price, copy_usdc)
            return self._record(trade, DRY_RUN, copy_size=copy_size)

        order_id = self._clob.place_order(
            token_id=trade["token_id"], side=side, price=price, size=copy_size,
            tick_size=tick_size, neg_risk=neg_risk,
        )
        if order_id:
            logging.info("Replicated %s -> order %s", label, order_id)
            return self._record(trade, PLACED, order_id=order_id, copy_size=copy_size)
        return self._record(trade, FAILED, "CLOB returned no order_id", copy_size=copy_size)

    def _market_params(self, market_id: str, token_id: str):
        market = self._data_api.get_market(market_id)
        if not market and token_id:
            market = self._data_api.get_market_by_token(token_id)
        if market:
            tick_size = str(market.get("minimum_tick_size") or market.get("minTickSize") or "0.01")
            neg_risk  = bool(market.get("neg_risk") or market.get("negRisk", False))
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
