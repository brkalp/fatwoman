import requests
import fatwoman_log_setup
import logging
from datetime import datetime as dt

print('ib_wrapper_tickler attempts %s'% dt.now())

IP = "https://localhost"
PORT = 5000
BASE_URL = f"{IP}:{PORT}/v1/api"

r = requests.post(f"{BASE_URL}/tickle", verify=False)
r.raise_for_status()
print('ib_wrapper_tickler     done %s' % dt.now())