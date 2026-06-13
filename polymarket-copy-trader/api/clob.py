"""
Thin wrapper around py_clob_client for placing Polymarket orders.
Only instantiated when DRY_RUN=False and a PRIVATE_KEY is configured.
"""
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

_CLOB_HOST = "https://clob.polymarket.com"


class ClobOrderPlacer:
    def __init__(self, private_key: str, chain_id: int = 137):
        from py_clob_client.client import ClobClient

        # Derive L2 API credentials from the wallet private key
        temp = ClobClient(_CLOB_HOST, key=private_key, chain_id=chain_id)
        creds = temp.create_or_derive_api_creds()
        self._client = ClobClient(
            _CLOB_HOST,
            key=private_key,
            chain_id=chain_id,
            creds=creds,
        )
        logger.info("CLOB client ready")

    def place_order(
        self,
        token_id: str,
        side: str,
        price: float,
        size: float,
        tick_size: str = "0.01",
        neg_risk: bool = False,
    ) -> Optional[str]:
        """
        Places a GTC limit order at `price` for `size` shares.
        Returns the order_id string on success, None on failure.
        """
        from py_clob_client.clob_types import OrderArgs, OrderType
        from py_clob_client.order_builder.constants import BUY, SELL

        clob_side = BUY if side.upper() == "BUY" else SELL
        try:
            resp = self._client.create_and_post_order(
                OrderArgs(
                    token_id=token_id,
                    price=price,
                    size=size,
                    side=clob_side,
                    order_type=OrderType.GTC,
                ),
                options={"tick_size": tick_size, "neg_risk": neg_risk},
            )
            order_id = resp.get("orderID") or resp.get("order_id")
            logger.info(
                "Order placed | id=%s side=%s size=%.2f price=%.4f token=%s...",
                order_id, side, size, price, token_id[:10],
            )
            return order_id
        except Exception as exc:
            logger.error("place_order failed: %s", exc)
            return None

    def cancel_order(self, order_id: str) -> bool:
        try:
            self._client.cancel(order_id)
            logger.info("Order cancelled: %s", order_id)
            return True
        except Exception as exc:
            logger.error("cancel_order(%s): %s", order_id, exc)
            return False

    def get_open_orders(self) -> List[Dict]:
        try:
            return self._client.get_orders() or []
        except Exception as exc:
            logger.error("get_open_orders: %s", exc)
            return []
