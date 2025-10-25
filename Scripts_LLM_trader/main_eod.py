from data_gathering.flow_market_add import add_values
from analyze_performance import EOD_message
import logging
from telegram_bot import tg_bot
import sys, os  # To make it work no matter where it is executed from

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__": 
    eod_message = EOD_message()

    # tg_bot.notify_listeners(eod_message, test_group=True) # send to telegram
    
    add_values()
    print(eod_message)
    logging.info("Finished adding market values to flows.")
