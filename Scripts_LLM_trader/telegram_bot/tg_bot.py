import requests
import os
import json


def _get_from_json(key): # why does it take from credentials instead of .env ? 
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "credentials.json")

    with open(file_path, "r") as f:
        credentials = json.load(f)
        return credentials[key]
    return None


def _send_message(chat_id, text): # send one message to chat with chat_id
    url = f"https://api.telegram.org/bot{_get_from_json('main_fatbot_token')}/sendMessage"
    res = requests.post(url, json={"chat_id": chat_id, "text": text})
    res.raise_for_status()


def notify_listeners(message, test_group=False): # send a message to all listeners
    target_list = "listener_chat_id"
    if test_group or (_get_from_json("testing") and _get_from_json("testing") is True):
        target_list = "testing_group"
    
    for listener in _get_from_json(target_list):
        _send_message(chat_id=listener, text=message)

"""
Ticker order    profit  open   close 
AAPL   bearish  4.32    50.11  54.40
AMZN   bullish  -3.20   50.00  47.80
"""

if __name__ == "__main__":
    # notify_listeners("hello to you too", True)
    print("main_fatbot_token: ", _get_from_json("main_fatbot_token")) 