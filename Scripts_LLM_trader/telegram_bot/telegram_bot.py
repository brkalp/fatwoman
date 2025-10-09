import requests 

class TelegramBot:

    def __init__(self):
        self.listeners = get_from_json("listeners")
    
    def _send_message(self, chat_id, text): 
        url = f"https://api.telegram.org/bot{get_from_json('telegram_bot_token')}/sendMessage"
        res = requests.post(url, json={"chat_id": chat_id, "text": text})
        res.raise_for_status()
    
    def notify_listeners(self, message):
        for listener in self.listeners:
            self._send_message(chat_id=listener, text=message)    

def get_from_json(key):
    with open('./telegram_bot/credentials.json', 'r') as f:
        f = f.read()
        import json
        credentials = json.loads(f)
        return credentials[key]
    return None

def notify_chat(messaage):
    bot = TelegramBot()
    bot.notify_listeners(messaage)

if __name__ == "__main__":
    bot = TelegramBot()
    print(get_from_json("telegram_bot_token"))
     # bot.notify_listeners("Test message from bot.")