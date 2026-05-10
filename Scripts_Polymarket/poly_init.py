""" Created on 04-11-2026 15:13:52 @author: ripintheblue """
#%% get a ticker
import requests
import json
response = requests.get(
    "https://gamma-api.polymarket.com/markets",
    params={"active": "true", "closed": "false", "limit": 1}
)
market = response.json()[0] # get first market from the response
market.copy()
market_list = json.loads(market["clobTokenIds"])
token_Dict = {
    "title": market["question"],
    "condId": market['conditionId'],
    "Yes": market_list[0],
    "No": market_list[1]
    }

condition_id = "your-condition-id-here"
market = client.get_market(condition_id)

print(market["question"])
print(market["minimum_tick_size"])
print(market["tokens"])  # Yes/No token IDs
# Getting the condition ID / slug
# If you don't have the condition ID yet, the easiest way is to:

# Open the market on polymarket.com — the URL contains the slug (e.g. polymarket.com/event/will-btc-hit-100k)
# Use the Gamma API to search by that slug as shown above
# The response will include conditionId, which you can then use with the CLOB client
BASE = "https://gamma-api.polymarket.com/"
response = requests.get(f"{BASE}/markets", params={"slug": "russia-x-ukraine-ceasefire-by-april-30-2026"})
market = response.json()[0]
print(market)



#%% setup client
from py_clob_client.client import ClobClient
import os
from fatwoman_api_setup import POLYMARKET_CREDS 

host = "https://clob.polymarket.com"
chain_id = 137  # Polygon mainnet
private_key = POLYMARKET_CREDS # Load private key from environment variable

# Derive API credentials (L1 → L2 auth)
# temp_client = ClobClient(host, key=private_key, chain_id=chain_id)
# api_creds = temp_client.create_or_derive_api_creds()

# Initialize trading client
client = ClobClient(
    host,
    # key=private_key,
    chain_id=chain_id,
    creds=POLYMARKET_CREDS,
    # signature_type=0,  # Signature type: 0 = EOA
    # funder="YOUR_WALLET_ADDRESS",  # Funder address
)

#%% place order
from py_clob_client.clob_types import OrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY
# Fetch market details to get tick size and neg risk
market = client.get_market("YOUR_CONDITION_ID")
tick_size = str(market["minimum_tick_size"])   # e.g., "0.01"
neg_risk = market["neg_risk"]             # e.g., False

response = client.create_and_post_order(
    OrderArgs(
        token_id=token_Dict["condId"],  # From Step 1
        price=0.50,
        size=1,
        side=BUY,
        order_type=OrderType.GTC,
    ),
    options={
        "tick_size": tick_size,
        "neg_risk": neg_risk,
    },
)

print("Order ID:", response["orderID"])
print("Status:", response["status"])

# Chris is gay