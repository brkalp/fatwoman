"""Telegram notifications. Trades and PnL go to different channels.

Reads TELEGRAM_BOT_TOKEN plus TELEGRAM_CHAT_TRADES / TELEGRAM_CHAT_PNL from
the environment (.env is sourced by the run_*.sh wrappers). Without a token
the message is logged instead of sent, so paper/mock runs work anywhere.
"""
import logging
import os

import requests

_CHANNEL_ENV = {"trades": "TELEGRAM_CHAT_TRADES", "pnl": "TELEGRAM_CHAT_PNL"}


def send(text: str, channel: str = "trades") -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get(_CHANNEL_ENV[channel])
    if not token or not chat_id or os.environ.get("POLYFLOW_MOCK") == "1":
        logging.info("telegram[%s] (not sent): %s", channel, text.replace("\n", " | "))
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=15,
        )
        r.raise_for_status()
        logging.info("telegram[%s] sent (%d chars)", channel, len(text))
        return True
    except Exception as exc:  # noqa: BLE001
        logging.error("telegram[%s] send failed: %s", channel, exc)
        return False
