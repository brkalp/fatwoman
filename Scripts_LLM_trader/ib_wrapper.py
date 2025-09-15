import pandas
import requests
from fatwoman_dir_setup import LLM_flow1_response_file, LLM_flow1_order_file

# IBKR http calls will happen here

IP = "https://localhost"
PORT = 5000
URL = f"{IP}:{PORT}/v1/api"

def _get_account_json():
    

def _place_order():
    pass


def sellAsset(asset_name: str, count, price=None):
    if price:
        print(f"Sold {count} {asset_name} each for {price}")
    else:
        print(f"Sold {count} {asset_name} each for market value!")


def buyTicker(asset_name: str, count, price=None):
    if price:
        print(f"Bought {count} {asset_name} each for {price}")
    else:
        print(f"Bought {count} {asset_name} each for market value!")


def getCurrentPortfolio():
    pass


def doOrder(order: dict):

    if order["action"] == "buy":
        asset = order["asset"]
        buyTicker(asset, 1)

    if order["action"] == "sell":
        asset = order["asset"]
        sellAsset(asset, 1)

if __name__ == "__main__":
    pass