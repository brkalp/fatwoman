""" Created on 14-06-2026 @author: ripintheblue """
import logging
from typing import Optional, List, Dict

_CLOB_HOST = "https://clob.polymarket.com"


class ClobOrderPlacer:
    def __init__(self, private_key: str, chain_id: int = 137):
        from py_clob_client.client import ClobClient
        temp  = ClobClient(_CLOB_HOST, key=private_key, chain_id=chain_id)
        creds = temp.create_or_derive_api_creds()
        self._client = ClobClient(_CLOB_HOST, key=private_key, chain_id=chain_id, creds=creds)
        logging.info("CLOB client ready")

    def place_order(self, token_id: str, side: str, price: float, size: float,
                    tick_size: str = "0.01", neg_risk: bool = False) -> Optional[str]:
        from py_clob_client.clob_types import OrderArgs, OrderType
        from py_clob_client.order_builder.constants import BUY, SELL
        clob_side = BUY if side.upper() == "BUY" else SELL
        try:
            resp = self._client.create_and_post_order(
                OrderArgs(token_id=token_id, price=price, size=size,
                          side=clob_side, order_type=OrderType.GTC),
                options={"tick_size": tick_size, "neg_risk": neg_risk},
            )
            order_id = resp.get("orderID") or resp.get("order_id")
            logging.info("Order placed id=%s %s %.2f@%.4f token=%s...",
                         order_id, side, size, price, token_id[:10])
            return order_id
        except Exception as e:
            logging.error("place_order failed: %s", e)
            return None

    def cancel_order(self, order_id: str) -> bool:
        try:
            self._client.cancel(order_id)
            logging.info("Order cancelled: %s", order_id)
            return True
        except Exception as e:
            logging.error("cancel_order %s: %s", order_id, e)
            return False

    def get_open_orders(self) -> List[Dict]:
        try:
            return self._client.get_orders() or []
        except Exception as e:
            logging.error("get_open_orders: %s", e)
            return []
