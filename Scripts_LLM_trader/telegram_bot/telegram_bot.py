
class TelegramBot:

    def __init__(self):
        self.listeners = []
    
    def send_message(self, chat_id, text): 
        pass
    
    def notify_listeners(self, message):
        pass    

def get_from_json(key):
    with open('credentials.json', 'r') as f:
        f = f.read()
        import json
        credentials = json.loads(f)
        return credentials[key]
    return None