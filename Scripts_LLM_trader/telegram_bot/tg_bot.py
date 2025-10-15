import requests
import os
import json


def _get_from_json(key): 
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "credentials.json")

    with open(file_path, "r") as f:
        credentials = json.load(f)
        return credentials[key]
    return None


def _send_message(chat_id, text): # send one message to chat with chat_id
    url = f"https://api.telegram.org/bot{_get_from_json('telegram_bot_token')}/sendMessage"
    res = requests.post(url, json={"chat_id": chat_id, "text": text})
    res.raise_for_status()


def notify_listeners(message): # send a message to all listeners
    for listener in _get_from_json("listeners"):
        _send_message(chat_id=listener, text=message)


if __name__ == "__main__":
    print("telegram_bot_token: ", _get_from_json("telegram_bot_token"))
