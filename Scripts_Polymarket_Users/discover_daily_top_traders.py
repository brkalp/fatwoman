""" Created on 06-29-2026 22:16:46 @author: ripintheblue """
import json
import os
import time
from datetime import datetime, timezone

import pandas as pd
import requests

import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import Polymarket_users_data_path

# ── Config ────────────────────────────────────────────────────────────────────
GAMMA        = "https://gamma-api.polymarket.com"
DATA         = "https://data-api.polymarket.com"
EVENT_LIMIT  = 20
HOLDER_LIMIT = 50

CATEGORIES = {
    "Politics":   2,
    "Finance":    120,
    "Crypto":     21,
    "Sports":     100639,
    "Tech":       1401,
    "Culture":    596,
    "Geopolitics":100265,
}

stamp        = datetime.now(timezone.utc)
discovered_at = stamp.isoformat()
OUTFILE      = os.path.join(
    Polymarket_users_data_path,
    f"polymarket_top_holders_by_category_{stamp.strftime('%Y%m%d_%H%M')}.csv",
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def get(url, params, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)


def parse_json_list(x):
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        try:
            return json.loads(x)
        except (json.JSONDecodeError, ValueError):
            return []
    return []


# ── Main loop ─────────────────────────────────────────────────────────────────
rows = []

for category, tag_id in CATEGORIES.items():
    print(f"[{category}] fetching events...")
    start_count = len(rows)

    try:
        events = get(
            f"{GAMMA}/events",
            {
                "tag_id":    tag_id,
                "active":    "true",
                "closed":    "false",
                "limit":     EVENT_LIMIT,
                "order":     "volume24hr",
                "ascending": "false",
            },
        )
    except requests.RequestException as exc:
        print(f"[{category}] failed to fetch events: {exc}")
        continue

    if not events:
        print(f"[{category}] no events returned")
        continue

    for event in events:
        for market in event.get("markets", []):
            condition_id = market.get("conditionId")
            if not condition_id:
                continue

            outcomes = parse_json_list(market.get("outcomes"))
            prices   = [float(x) for x in parse_json_list(market.get("outcomePrices"))]

            try:
                holder_blocks = get(
                    f"{DATA}/holders",
                    {"market": condition_id, "limit": HOLDER_LIMIT},
                )
            except requests.RequestException as exc:
                print(f"[{category}] skip market {condition_id}: {exc}")
                continue

            if not holder_blocks:
                continue

            for block in holder_blocks:
                for h in block.get("holders", []):
                    outcome_idx = h.get("outcomeIndex")
                    shares      = float(h.get("amount") or 0)
                    price       = (
                        prices[outcome_idx]
                        if outcome_idx is not None and outcome_idx < len(prices)
                        else None
                    )
                    outcome = (
                        outcomes[outcome_idx]
                        if outcome_idx is not None and outcome_idx < len(outcomes)
                        else None
                    )

                    rows.append(
                        {
                            "category":       category,
                            "wallet":         h.get("proxyWallet"),
                            "username":       h.get("name") or h.get("pseudonym"),
                            "event":          event.get("title"),
                            "market":         market.get("question"),
                            "market_id":      condition_id,
                            "asset":          h.get("asset"),
                            "outcome":        outcome,
                            "outcome_index":  outcome_idx,
                            "shares":         shares,
                            "price":          price,
                            "position_value": shares * price if price is not None else None,
                            "discovered_at":  discovered_at,
                        }
                    )

    added = len(rows) - start_count
    print(f"[{category}] {added} holder rows across {len(events)} events")

# ── Save ──────────────────────────────────────────────────────────────────────
df = pd.DataFrame(rows)
df.to_csv(OUTFILE, index=False)
print(f"Saved {len(df)} rows to {OUTFILE}")

script_end_log()
