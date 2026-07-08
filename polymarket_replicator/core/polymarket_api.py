"""Polymarket API access (gamma + data-api) with an offline deterministic
mock mode used for paper testing, unit tests and backtest development.

Mock mode is active when config mock_api=true or POLYFLOW_MOCK=1. All mock
data is a pure function of (entity, time bucket), so two calls inside the
same hour return identical trades - which is what the dedupe logic in step 4
relies on - while prices drift hour to hour so pnl and slippage are non-zero.
"""
import hashlib
import logging
import os
import random
import time
from datetime import datetime, timedelta, timezone

import requests

GAMMA = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com"

# tag ids from the existing daily discovery script
CATEGORIES = {
    "Politics": 2,
    "Finance": 120,
    "Crypto": 21,
    "Sports": 100639,
    "Tech": 1401,
    "Culture": 596,
    "Geopolitics": 100265,
}

_session = requests.Session()


def _mock_enabled(cfg) -> bool:
    return bool(cfg.get("mock_api")) or os.environ.get("POLYFLOW_MOCK") == "1"


def _get(url, params=None, retries=3):
    for attempt in range(retries):
        try:
            r = _session.get(url, params=params, timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception as exc:  # noqa: BLE001 - log and retry any transport error
            if attempt == retries - 1:
                logging.error("GET %s failed after %d tries: %s", url, retries, exc)
                raise
            time.sleep(2 ** attempt)


def _rng(*keys) -> random.Random:
    seed = hashlib.md5("|".join(str(k) for k in keys).encode()).hexdigest()
    return random.Random(int(seed[:12], 16))


class PolymarketAPI:
    """Live client. as_of (datetime) enables backtest filtering: any data
    with timestamps after as_of is dropped where the API allows it."""

    def __init__(self, cfg, as_of=None):
        self.cfg = cfg
        self.as_of = as_of

    def now(self) -> datetime:
        return self.as_of or datetime.now(timezone.utc)

    # --- universe -------------------------------------------------------
    def top_markets(self, category: str, limit: int):
        params = {
            "order": "volumeNum", "ascending": "false", "limit": limit,
            "closed": "false", "tag_id": CATEGORIES[category],
        }
        return [
            {
                "condition_id": m.get("conditionId"),
                "question": m.get("question"),
                "category": category,
                "volume": float(m.get("volumeNum") or 0),
                "last_price": float(m.get("lastTradePrice") or 0.5),
            }
            for m in _get(f"{GAMMA}/markets", params)
            if m.get("conditionId")
        ]

    def top_events(self, limit: int):
        events = _get(f"{GAMMA}/events", {"order": "volume", "ascending": "false",
                                          "limit": limit, "closed": "false"})
        out = []
        for ev in events:
            for m in (ev.get("markets") or [])[:1]:  # biggest market per event
                if m.get("conditionId"):
                    out.append({
                        "condition_id": m["conditionId"],
                        "question": m.get("question"),
                        "category": _category_from_tags(ev.get("tags")),
                        "volume": float(ev.get("volume") or 0),
                        "last_price": float(m.get("lastTradePrice") or 0.5),
                    })
        return out

    def market_holders(self, condition_id: str, limit: int):
        data = _get(f"{DATA_API}/holders", {"market": condition_id, "limit": limit})
        holders = []
        for token in data if isinstance(data, list) else [data]:
            for h in token.get("holders", []):
                holders.append({
                    "proxy_wallet": h.get("proxyWallet"),
                    "user_name": h.get("name") or h.get("pseudonym") or "",
                    "holding_usdc": float(h.get("amount") or 0),
                })
        holders.sort(key=lambda h: -h["holding_usdc"])
        return holders[:limit]

    # --- per-user data ----------------------------------------------------
    def user_activity(self, wallet: str, since: datetime):
        rows = _get(f"{DATA_API}/activity",
                    {"user": wallet, "type": "TRADE", "limit": 500}) or []
        out = []
        for t in rows:
            ts = datetime.fromtimestamp(int(t.get("timestamp", 0)), tz=timezone.utc)
            if ts < since or ts > self.now():
                continue
            out.append({
                "trade_id": t.get("transactionHash") or f"{wallet}{t.get('timestamp')}",
                "ts": ts.isoformat(),
                "condition_id": t.get("conditionId"),
                "question": t.get("title") or "",
                "side": (t.get("side") or "BUY").upper(),
                "outcome": t.get("outcome") or "",
                "price": float(t.get("price") or 0.5),
                "usdc_size": float(t.get("usdcSize") or 0),
            })
        return out

    def wallet_active_before(self, wallet: str, as_of: datetime) -> bool:
        """True if the wallet already traded on or before as_of. Used by the
        backtest universe back-calculation in step 1."""
        rows = _get(f"{DATA_API}/activity",
                    {"user": wallet, "type": "TRADE", "limit": 500}) or []
        stamps = [int(t.get("timestamp", 0)) for t in rows]
        return bool(stamps) and min(stamps) <= as_of.timestamp()

    def user_account(self, wallet: str):
        """Account size + 30d daily pnl series ending at as_of/now."""
        value = _get(f"{DATA_API}/value", {"user": wallet})
        size = float(value[0].get("value", 0)) if isinstance(value, list) and value else 0.0
        # data-api has no historical equity endpoint; approximate daily pnl
        # from realized trade activity. Lookahead is avoided by ts filter,
        # survivorship caveat is logged by the callers that backtest.
        trades = self.user_activity(wallet, self.now() - timedelta(days=30))
        pnl_by_day = {}
        for t in trades:
            day = t["ts"][:10]
            sign = 1 if t["side"] == "SELL" else -1
            pnl_by_day[day] = pnl_by_day.get(day, 0.0) + sign * t["usdc_size"]
        days = sorted(pnl_by_day)
        wins = sum(1 for t in trades if t["side"] == "SELL" and t["price"] > 0.5)
        sells = sum(1 for t in trades if t["side"] == "SELL")
        return {
            "account_size": size,
            "n_trades_30d": len(trades),
            "daily_pnl": [pnl_by_day[d] for d in days],
            "accuracy": (wins / sells) if sells else 0.0,
        }

    def market_price(self, condition_id: str) -> float:
        markets = _get(f"{GAMMA}/markets", {"condition_ids": condition_id})
        if markets:
            return float(markets[0].get("lastTradePrice") or 0.5)
        return 0.5

    def user_weekly_return(self, wallet: str, week_start: datetime) -> float:
        """Forward 1-week return of a wallet starting at week_start, as a
        fraction of account size. Live approximation from trade activity;
        used only by the backtester."""
        acct = self.user_account(wallet)
        trades = self.user_activity(wallet, week_start)
        pnl = sum((1 if t["side"] == "SELL" else -1) * t["usdc_size"]
                  for t in trades
                  if week_start <= datetime.fromisoformat(t["ts"])
                  < week_start + timedelta(days=7))
        return pnl / max(acct["account_size"], 1.0)


def _category_from_tags(tags):
    for tag in tags or []:
        label = tag.get("label") if isinstance(tag, dict) else str(tag)
        if label in CATEGORIES:
            return label
    return "Other"


class MockPolymarketAPI(PolymarketAPI):
    """Deterministic offline stand-in with the same interface."""

    N_WALLETS_PER_CAT = 120

    # --- internals --------------------------------------------------------
    def _hour(self) -> str:
        return self.now().strftime("%Y%m%d%H")

    def _day(self) -> str:
        return self.now().strftime("%Y%m%d")

    def _wallets(self, category):
        return [
            "0x" + hashlib.md5(f"{category}|wallet|{i}".encode()).hexdigest()[:38]
            for i in range(self.N_WALLETS_PER_CAT)
        ]

    def _markets(self, category):
        out = []
        for i in range(12):
            cond = "0x" + hashlib.md5(f"{category}|market|{i}".encode()).hexdigest()[:40]
            out.append({
                "condition_id": cond,
                "question": f"{category} mock market {i}?",
                "category": category,
                "volume": 5_000_000 / (i + 1),
                "last_price": self.market_price(cond),
            })
        return out

    def _wallet_category(self, wallet):
        for cat in CATEGORIES:
            if wallet in self._wallets(cat):
                return cat
        return "Politics"

    # --- interface --------------------------------------------------------
    def top_markets(self, category, limit):
        return self._markets(category)[:limit]

    def top_events(self, limit):
        out = []
        for cat in CATEGORIES:
            out.extend(self._markets(cat))
        out.sort(key=lambda m: -m["volume"])
        return out[:limit]

    def market_holders(self, condition_id, limit):
        cat = next((c for c in CATEGORIES
                    if condition_id in [m["condition_id"] for m in self._markets(c)]),
                   "Politics")
        rng = _rng("holders", condition_id)
        wallets = rng.sample(self._wallets(cat), min(limit, self.N_WALLETS_PER_CAT))
        return sorted(
            ({
                "proxy_wallet": w,
                "user_name": f"mock_{cat.lower()}_{w[2:8]}",
                "holding_usdc": round(_rng("hold", condition_id, w).uniform(1e3, 5e5), 2),
            } for w in wallets),
            key=lambda h: -h["holding_usdc"],
        )

    def user_activity(self, wallet, since):
        """0-3 trades per wallet per hour, stable within the hour."""
        out = []
        cat = self._wallet_category(wallet)
        markets = self._markets(cat)
        cursor = since.replace(minute=0, second=0, microsecond=0)
        while cursor <= self.now():
            hour_key = cursor.strftime("%Y%m%d%H")
            rng = _rng("act", wallet, hour_key)
            for j in range(rng.choice([0, 0, 0, 1, 1, 2, 3])):
                m = rng.choice(markets)
                ts = cursor + timedelta(minutes=rng.randint(0, 59))
                if ts < since or ts > self.now():
                    continue
                out.append({
                    "trade_id": hashlib.md5(f"{wallet}|{hour_key}|{j}".encode()).hexdigest()[:16],
                    "ts": ts.isoformat(),
                    "condition_id": m["condition_id"],
                    "question": m["question"],
                    "side": rng.choice(["BUY", "BUY", "BUY", "SELL"]),
                    "outcome": rng.choice(["Yes", "No"]),
                    "price": round(self.market_price(m["condition_id"]), 3),
                    "usdc_size": round(rng.uniform(50, 5000), 2),
                })
            cursor += timedelta(hours=1)
        return out

    def wallet_active_before(self, wallet, as_of):
        born = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(
            days=_rng("born", wallet).randint(0, 900))
        return born <= as_of

    def user_account(self, wallet):
        rng = _rng("acct", wallet)
        size = round(10 ** rng.uniform(3.5, 6.0), 2)  # 3k .. 1M
        daily = [round(size * _rng("pnl", wallet, i, self._day()[:6]).uniform(-0.03, 0.035), 2)
                 for i in range(30)]
        return {
            "account_size": size,
            "n_trades_30d": rng.randint(3, 120),
            "daily_pnl": daily,
            "accuracy": round(rng.uniform(0.35, 0.78), 3),
        }

    def market_price(self, condition_id):
        base = int(hashlib.md5(condition_id.encode()).hexdigest()[:6], 16) / 0xFFFFFF
        drift = _rng("px", condition_id, self._hour()).uniform(-0.04, 0.04)
        return round(min(0.97, max(0.03, 0.2 + 0.6 * base + drift)), 3)

    def user_weekly_return(self, wallet, week_start):
        # skilled mock users (high accuracy) earn more on average, so the
        # selection edge is visible in backtests
        acc = self.user_account(wallet)["accuracy"]
        rng = _rng("wret", wallet, week_start.strftime("%Y%m%d"))
        return round(rng.gauss((acc - 0.5) * 0.06, 0.03), 5)


def get_api(cfg, as_of=None) -> PolymarketAPI:
    if _mock_enabled(cfg):
        logging.info("using MOCK polymarket api (as_of=%s)", as_of)
        return MockPolymarketAPI(cfg, as_of)
    return PolymarketAPI(cfg, as_of)
