""" Created on 09-19-2025 15:55:16 @author: ripintheblue """
import requests
import fatwoman_log_setup
import logging
from datetime import datetime as dt

print('ib_wrapper_tickler attempts %s'% dt.now())

IP = "https://localhost"
PORT = 5000
BASE_URL = f"{IP}:{PORT}/v1/api"

r = requests.post(f"{BASE_URL}/tickle", verify=False)
response_text = r.text
r.raise_for_status()
print('ib_wrapper_tickler     done %s' % dt.now())
logging.info("ib_wrapper_tickler response: %s" %response_text)

# ssh -L 5000:localhost:5000 fatwoman@192.168.0.154