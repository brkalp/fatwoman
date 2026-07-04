""" Created on 06-29-2026 22:16:46 @author: ripintheblue """
import json
import time
from collections import defaultdict
from datetime import datetime, timezone

import os
import pandas as pd
import requests

import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import Polymarket_users_data_path


stamp = datetime.now(timezone.utc)
discovered_at = stamp.isoformat()
OUTFILE = os.path.join(Polymarket_users_data_path, f"polymarket_top_holders_by_category_{stamp.strftime('%Y%m%d_%H%M')}.csv")
GAMMA = "https://gamma-api.polymarket.com"
DATA = "https://data-api.polymarket.com"

# Tags to exclude from category discovery (generic / UI-only tags)
SKIP_TAG_IDS = {
    "100215",  # All
    "102169",  # Hide From New
    "100037",  # arch (internal)
}

TOP_N_CATEGORIES = 20
DISCOVERY_EVENT_LIMIT = 200   # events scanned to rank tags
EVENT_LIMIT = 50              # events per category when scraping holders
HOLDER_LIMIT = 100


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
        return json.loads(x)
    return []


def discover_top_categories(n=TOP_N_CATEGORIES):
    """Return {label: tag_id} for the top-n tags ranked by aggregated volume24hr."""
    print(f"Discovering top {n} categories by 24hr volume...")
    events = get(
        f"{GAMMA}/events",
        {
            "active": "true",
            "closed": "false",
            "limit": DISCOVERY_EVENT_LIMIT,
            "order": "volume24hr",
            "ascending": "false",
        },
    )

    tag_vol = defaultdict(float)
    tag_label = {}
    for event in events:
        vol = float(event.get("volume24hr") or 0)
        for t in event.get("tags", []):
            tid = str(t["id"])
            if tid in SKIP_TAG_IDS:
                continue
            tag_vol[tid] += vol
            tag_label[tid] = t["label"]

    ranked = sorted(tag_vol.items(), key=lambda x: -x[1])[:n]
    categories = {tag_label[tid]: tid for tid, _ in ranked}

    print(f"Top {n} categories discovered:")
    for rank, (tid, vol) in enumerate(ranked, 1):
        print(f"  {rank:2}. {tag_label[tid]:<30} vol24hr=${vol:,.0f}")

    return categories


CATEGORIES = discover_top_categories()

rows = []

for category, tag_id in CATEGORIES.items():
    print(f"[{category}] fetching events...")
    start_count = len(rows)

    events = get(
        f"{GAMMA}/events",
        {
            "tag_id": tag_id,
            "active": "true",
            "closed": "false",
            "limit": EVENT_LIMIT,
            "order": "volume24hr",
            "ascending": "false",
        },
    )

    for event in events:
        for market in event.get("markets", []):
            condition_id = market.get("conditionId")
            if not condition_id:
                continue

            outcomes = parse_json_list(market.get("outcomes"))
            prices = [float(x) for x in parse_json_list(market.get("outcomePrices"))]

            try:
                holder_blocks = get(
                    f"{DATA}/holders",
                    {"market": condition_id, "limit": HOLDER_LIMIT},
                )
            except requests.RequestException as e:
                print(f"[{category}] skip market {condition_id}: {e}")
                continue

            for block in holder_blocks:
                for h in block.get("holders", []):
                    outcome_idx = h.get("outcomeIndex")
                    shares = float(h.get("amount") or 0)

                    price = prices[outcome_idx] if outcome_idx is not None and outcome_idx < len(prices) else None
                    outcome = outcomes[outcome_idx] if outcome_idx is not None and outcome_idx < len(outcomes) else None

                    rows.append(
                        {
                            "category": category,
                            "tag_id": tag_id,
                            "wallet": h.get("proxyWallet"),
                            "username": h.get("name") or h.get("pseudonym"),
                            "event": event.get("title"),
                            "market": market.get("question"),
                            "market_id": condition_id,
                            "asset": h.get("asset"),
                            "outcome": outcome,
                            "outcome_index": outcome_idx,
                            "shares": shares,
                            "price": price,
                            "position_value": shares * price if price is not None else None,
                            "discovered_at": discovered_at,
                        }
                    )

    added = len(rows) - start_count
    print(f"[{category}] {added} holder rows across {len(events)} events")

df = pd.DataFrame(rows)
df.to_csv(OUTFILE, index=False)

print(f"Saved {len(df)} rows to {OUTFILE}")

script_end_log()
