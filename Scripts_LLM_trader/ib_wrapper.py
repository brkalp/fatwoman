from time import sleep
import requests
from fatwoman_dir_setup import LLM_flow1_response_file, LLM_flow1_order_file
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# IBKR http calls will happen here
# v1/api and v1/portal are different things; api -> market orders; portal -> auth
IP = "https://localhost"
PORT = 5000
BASE_URL = f"{IP}:{PORT}/v1/api"


# Keeps the session alive; have to be run every 60 seconds
def tickle():
    r = requests.post(f"{BASE_URL}/tickle", verify=False)
    r.raise_for_status()
    return r.json()


# Lookup stock info by ticker symbol; TODO: Doesn't return market data which is meh
def _lookup_stock(ticker):
    params = {"symbols": ticker}
    r = requests.post(f"{BASE_URL}/trsrv/stocks", params=params, verify=False)
    r.raise_for_status()
    return r.json()


# Returns conid for NASDAQ of a ticker symbol
def _get_ticker_conid(ticker):
    stock_info = _lookup_stock(ticker)
    stock_info = stock_info.get(ticker)
    stock_info = stock_info[0] if isinstance(stock_info, list) else stock_info
    # print("stock_info: ", stock_info)
    contracts = stock_info["contracts"]
    for contract in contracts:
        if contract["exchange"] == "NASDAQ":
            return contract["conid"]


# Reauthenticate the session, setting auth and connected
def __reauth():
    r = requests.get(f"{BASE_URL}/iserver/reauthenticate", verify=False)
    r.raise_for_status()
    return r.json()


# Make sure we are authenticated and connected if not try reauthenticating
def _check_auth_and_conn(try_number=5):
    r = requests.get(f"{BASE_URL}/iserver/auth/status", verify=False)
    r.raise_for_status()
    json = r.json()
    auth_status = json["authenticated"]
    conn_status = json["connected"]
    if auth_status and conn_status:
        return True
    else:
        if try_number > 0:
            print("IBKR SERVER IS NOT LOGGED IN!! TRYING TO REAUTHENTICATE...")
            logout()
            __reauth()
            sleep(5 + (5 - try_number) * 2)
            return _check_auth_and_conn(try_number - 1)
        else:
            print(
                "IBKR SERVER IS NOT LOGGED IN!! PLEASE LOGIN USING THE IBKR MOBILE APP OR IBKR DESKTOP APP"
            )
            print(json)


# Returns Account auth info; not portfolio info
def _get_account_json():
    r = requests.get(f"{BASE_URL}/portfolio/accounts", verify=False)
    r.raise_for_status()
    accounts = r.json()
    if not accounts:
        raise RuntimeError(
            "IB SERVER WAS NOT LOGGED IN!! NO ACCOUNT FOUND PS     ssh -L 5000:localhost:5000 fatwoman@192.168.0.154"
        )
    return accounts[0]


def _get_account_id():
    return _get_account_json()["id"]


def get_live_orders():
    url = f"{BASE_URL}/iserver/account/orders"
    print("live orders: ", url)
    r = requests.get(url, verify=False)
    # r.raise_for_status()
    if r.status_code != 200:
        print("get orders response: ", r.text)
        r.raise_for_status()

    return r.json()


# Place order by ticker symbol
def place_order_ticker(ticker, side, qty=1, price=None):

    conid = _get_ticker_conid(ticker)
    if not conid:
        raise ValueError(f"Ticker {ticker} not found")
    return _place_order_conid(conid, side, qty, price)


# Place order by conid
def _place_order_conid(conid, side, qty=1, price=None, paper_trade=True):
    if paper_trade and not check_if_paper_trading():
        raise RuntimeError(
            "YOU REQUESTED A PAPER ORDER BUT YOU ARE ON THE LIVE ACCOUNT!"
        )

    if not _check_auth_and_conn():
        raise RuntimeError("IBKR SERVER IS NOT LOGGED IN!!")

    order = {
        "orders": [
            {
                "conid": conid,
                "orderType": "MKT" if price is None else "LMT",
                "side": side.upper(),
                "tif": "DAY",  # required: Time in Force
                "quantity": qty,
                "isSuppressed": False,
                "override": True,
            }
        ]
    }
    if price:
        order["price"] = price

    # print("order json: ", order)

    headers = {"Content-Type": "application/json"}
    r = requests.post(
        f"{BASE_URL}/iserver/account/{_get_account_id()}/orders",
        json=order,
        headers=headers,
        verify=False,
    )
    # print error message if error
    if r.status_code != 200 and r.status_code != 201:
        print("order response: ", r.text)
        r.raise_for_status()
    r = r.json()

    """# Log order id(s) if order placed AND A LIST
    if isinstance(r, list):
        for item in r:
            if "id" in item:
                print(f"Order placed. ID={item['id']}")
    elif isinstance(r, dict) and "id" in r:
        """
    # print(f"Order placed. ID={r['id']}") # doesn't work rn

    return r


def _get_all_positions():
    url = f"{BASE_URL}/portfolio/{_get_account_id()}/positions"
    print(url)
    r = requests.get(url, verify=False)
    if r.status_code != 200:
        print("ERROR MESSAGE: ", r.text)
        r.raise_for_status()

    return r.json()


def sell_all_positions():
    positions = _get_all_positions()

    for position in positions:
        if position["position"] > 0:
            place_order_ticker(
                position["contractDesc"], "SELL", qty=position["position"]
            )


# Accounts for paper trading start with DU, live accounts with U
def check_if_paper_trading():
    acc_id = _get_account_id()
    return acc_id[0] == "D"

def logout():
    r = requests.post(f"{BASE_URL}/logout", verify=False)
    r.raise_for_status()
    return r.json()


# TODO: Pozisyon başına da PNL LAZIM
def get_PNL():
    acc_url = f"{BASE_URL}/iserver/account/pnl/partitioned"
    r = requests.get(acc_url, verify=False)
    print(r.json())
    pass


def doOrder(order: dict):

    if order["action"] == "buy":
        asset = order["asset"]
        # buyTicker(asset, 1)

    if order["action"] == "sell":
        asset = order["asset"]
        # sellAsset(asset, 1)

def confirm_messages(messageId):
    url = f"{BASE_URL}/iserver/reply/{messageId}"
    body = {"confirm": True}
    r = requests.post(url=url, json=body, verify=False)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    # print("tickle: ",tickle())
    print("id: ", _get_account_id())

    # print("stock apple: ", _lookup_stock("AAPL"))
    # print("is paper trading: ", check_if_paper_trading())
    # print("APPLE conid: ", _get_ticker_conid("AAPL"))
    # print("current orders: ", get_current_orders())
    # print("live orders: ", get_live_orders())

    # print(confirm_messages("77a80002-44f7-4414-b1e8-8b2b898cd193"))
    print("placed order: ", place_order_ticker("AAPL", "BUY"))
    # print("reauth: ", _check_auth_and_conn() )
    # print("all positions: ", _get_all_positions())
    #print("PNL: ", get_PNL())
    print("sell all positions: ", sell_all_positions())
    # print(requests.get("https://localhost:5000/v1/api/trsrv/stocks?symbols=AAPL", verify=False))
