from Scripts_LLM_trader.data_gathering.db_price_fetcher import fetch_prices_calc_ret_add_to_db
from analyze_performance import EOD_message
import logging
from telegram_bot import tg_bot
import sys, os  # To make it work no matter where it is executed from

# make this append the syspath one directory up
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__": 
    eod_message = EOD_message()

    # tg_bot.notify_listeners(eod_message, test_group=True) # send to telegram
    
    fetch_prices_calc_ret_add_to_db()
    print(eod_message)
    logging.info("Finished adding market values to flows.")
