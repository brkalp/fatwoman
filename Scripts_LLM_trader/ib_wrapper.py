import requests
from fatwoman_dir_setup import LLM_flow1_response_file, LLM_flow1_order_file
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# IBKR http calls will happen here

IP = "https://localhost"
PORT = 5000
BASE_URL = f"{IP}:{PORT}/v1/api"

def tickle():
    r = requests.post(f"{BASE_URL}/tickle", verify=False)
    r.raise_for_status()
    return r.json()

def _lookup_stock(ticker): 
    params = {"symbols": ticker} 
    r = requests.post(f"{BASE_URL}/trsrv/stocks", params=params, verify=False)
    r.raise_for_status()
    return r.json() 

def _get_ticker_conid(ticker):
    stock_info = _lookup_stock(ticker)
    stock_info = stock_info.get(ticker)
    stock_info = stock_info[0] if isinstance(stock_info, list) else stock_info
    # print("stock_info: ", stock_info)
    contracts = stock_info["contracts"]
    for contract in contracts:
        if contract["exchange"] == "NASDAQ":
            return contract["conid"]


def _get_account_json():
    r = requests.get(f"{BASE_URL}/portfolio/accounts", verify=False)
    r.raise_for_status()
    accounts = r.json()
    if not accounts:
        raise RuntimeError("IB SERVER WAS NOT LOGGED IN!! NO ACCOUNT FOUND PS     ssh -L 5000:localhost:5000 fatwoman@192.168.0.154") 

    return accounts[0]

def _get_account_id():
    return _get_account_json()["id"]

def get_current_orders():
    r = requests.get(f"{BASE_URL}/iserver/account/{_get_account_id()}/orders", verify=False)
    r.raise_for_status()
    return r.json()

def _place_order_conid(conid, side, qty=1, price=None):
    order = {
        "conid": conid,
        "orderType": "MKT" if price is None else "LMT",
        "side": side.upper(),
        "quantity": qty
    }
    if price:
        order["price"] = price

    r = requests.post(f"{BASE_URL}/iserver/account/{_get_account_id()}/orders", json=[order], verify=False)
    
    # print error message if status code is not 200
    if r.status_code != 200 or r.status_code != 201:
        print("order response: ", r.text)
    
    r.raise_for_status()
    return r.json()


def place_order_ticker(ticker, side, qty=1, price=None):
    conid = _get_ticker_conid(ticker)
    if not conid:
        raise ValueError(f"Ticker {ticker} not found")
    return _place_order_conid(conid, side, qty, price)




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
    # print("tickle: ",tickle())
    # print("id: ",_get_account_id()) 

    # print("stock apple: ", _lookup_stock("AAPL"))

    # print("APPLE conid: ", _get_ticker_conid("AAPL"))
    # print("current orders: ", get_current_orders())
    
    print("placing order: ", place_order_ticker("AAPL", "buy"))
    
    # print(requests.get("https://localhost:5000/v1/api/trsrv/stocks?symbols=AAPL", verify=False))
