# Created on 02-28-2024 03:58:58 @author: ripintheblue
import fatwoman_log_setup
import logging
from fatwoman_dir_setup import binance_Orderbook_loc_prefix, Binance_save_log_path
from fatwoman_api_setup import Binance_Secret, Binance_Key
from binance.client import Client
import pandas as pd
from datetime import datetime as dt
import os

print('Binance download %s' % dt.now())
client = Client(api_key=Binance_Secret, api_secret=Binance_Key)

def get_order_book(symbol, limit=15):
    order_book = client.get_order_book(symbol=symbol, limit=limit)
    bids = order_book['bids']
    asks = order_book['asks']
    return bids, asks

def process_order_book(bids, asks):
    bids_df = pd.DataFrame(bids, columns=['price', 'quantity']).assign(type='bid')
    asks_df = pd.DataFrame(asks, columns=['price', 'quantity']).assign(type='ask')
    order_book_df = pd.concat([bids_df, asks_df], axis=0).reset_index(drop=True).sort_values(['price'])
    order_book_df['timestamp'] = dt.now().strftime('%Y-%m-%d %H:%M:%S')
    return order_book_df

def save_order_book_to_csv(order_book_df, file_full_path):
    file_exists = os.path.exists(file_full_path)
    order_book_df.to_csv(file_full_path, mode='a', sep=',', header=not file_exists, index=False)
# ImportError: cannot import name 'binance_orderbook_loc_prefix' from 'fatwoman_dir_setup' (/media/fatwoman/15GB/Scripts_Setup_Dirs/fatwoman_dir_setup.py)
ticker = "BTCUSDT"
bids, asks = get_order_book(ticker)
file_full_path = binance_Orderbook_loc_prefix + ticker + ".csv"

order_book_df = process_order_book(bids, asks)
save_order_book_to_csv(order_book_df, file_full_path)

#   File "/home/fatwoman/.local/lib/python3.8/site-packages/binance/client.py", line 368, in _handle_response
#     raise BinanceAPIException(response, response.status_code, response.text)
# binance.exceptions.BinanceAPIException: APIError(code=-1099): Not found, unauthenticated, or unauthorized.
# 240821 16:15:14 - binance_orderbook_save -  ERROR - Uncaught exception
# Traceback (most recent call last):
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/urllib3/connection.py", line 203, in _new_conn
#     sock = connection.create_connection(
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/urllib3/util/connection.py", line 60, in create_connection
#     for res in socket.getaddrinfo(host, port, family, socket.SOCK_STREAM):
#   File "/usr/lib/python3.8/socket.py", line 918, in getaddrinfo
#     for res in _socket.getaddrinfo(host, port, family, type, proto, flags):
# socket.gaierror: [Errno -3] Temporary failure in name resolution

# The above exception was the direct cause of the following exception:

# Traceback (most recent call last):
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/urllib3/connectionpool.py", line 790, in urlopen
#     response = self._make_request(
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/urllib3/connectionpool.py", line 491, in _make_request
#     raise new_e
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/urllib3/connectionpool.py", line 467, in _make_request
#     self._validate_conn(conn)
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/urllib3/connectionpool.py", line 1092, in _validate_conn
#     conn.connect()
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/urllib3/connection.py", line 611, in connect
#     self.sock = sock = self._new_conn()
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/urllib3/connection.py", line 210, in _new_conn
#     raise NameResolutionError(self.host, self, e) from e
# urllib3.exceptions.NameResolutionError: <urllib3.connection.HTTPSConnection object at 0x7f7fc2eea160>: Failed to resolve 'api.binance.com' ([Errno -3] Temporary failure in name resolution)

# The above exception was the direct cause of the following exception:

# Traceback (most recent call last):
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/requests/adapters.py", line 486, in send
#     resp = conn.urlopen(
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/urllib3/connectionpool.py", line 844, in urlopen
#     retries = retries.increment(
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/urllib3/util/retry.py", line 515, in increment
#     raise MaxRetryError(_pool, url, reason) from reason  # type: ignore[arg-type]
# urllib3.exceptions.MaxRetryError: HTTPSConnectionPool(host='api.binance.com', port=443): Max retries exceeded with url: /api/v3/ping (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x7f7fc2eea160>: Failed to resolve 'api.binance.com' ([Errno -3] Temporary failure in name resolution)"))

# During handling of the above exception, another exception occurred:

# Traceback (most recent call last):
#   File "/media/fatwoman/15GB/Scripts_Binance/binance_orderbook_save.py", line 12, in <module>
#     client = Client(api_key=Binance_Secret, api_secret=Binance_Key)
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/binance/client.py", line 344, in __init__
#     self.ping()
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/binance/client.py", line 570, in ping
#     return self._get('ping', version=self.PRIVATE_API_VERSION)
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/binance/client.py", line 415, in _get
#     return self._request_api('get', path, signed, version, **kwargs)
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/binance/client.py", line 378, in _request_api
#     return self._request(method, uri, signed, **kwargs)
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/binance/client.py", line 358, in _request
#     self.response = getattr(self.session, method)(uri, **kwargs)
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/requests/sessions.py", line 602, in get
#     return self.request("GET", url, **kwargs)
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/requests/sessions.py", line 589, in request
#     resp = self.send(prep, **send_kwargs)
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/requests/sessions.py", line 703, in send
#     r = adapter.send(request, **kwargs)
#   File "/home/fatwoman/.local/lib/python3.8/site-packages/requests/adapters.py", line 519, in send
#     raise ConnectionError(e, request=request)
# requests.exceptions.ConnectionError: HTTPSConnectionPool(host='api.binance.com', port=443): Max retries exceeded with url: /api/v3/ping (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x7f7fc2eea160>: Failed to resolve 'api.binance.com' ([Errno -3] Temporary failure in name resolution)"))