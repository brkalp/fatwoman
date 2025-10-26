from flows.trading_flow_v1 import flow_v1 
from flows.trading_flow_POC import poc_flow
import logging, threading
from telegram_bot import tg_bot # this will explode if trading_flow is run as main
logging.basicConfig(level=logging.INFO)
from fatwoman_log_setup import script_end_log

def _worker_thread(ticker, notify_users, date, analysis_list):
    resp = flow_v1(ticker=ticker, date=date, notify_users=notify_users)
    logging.info(f"Analyzed response for {ticker}:\n {resp}")

    analysis_list.append(resp)

# FLOW 2: gets 5 suggestion headlines from poc then all of them are fed to v1, to analyze further
def flow_v2(date :str="2025-10-16", notify_users:bool=True):
    analysis = []
    threads = []

    for suggested_ticker in poc_flow(date): 
        print(f"Starting thread for ticker: {suggested_ticker}")
        logging.info(f"Starting thread for ticker: {suggested_ticker}")

        t = threading.Thread(target=_worker_thread, args=(suggested_ticker, False, date, analysis)) # thread
        t.start()
        threads.append(t) 
    
    for t in threads: # Wait for all threads to finish
        t.join()

    if notify_users:   
        tg_bot.notify_listeners(f"--{date}'s report--" + '\n'.join(analysis)) # send messages to telegram chat

    return analysis


if __name__ == "__main__":
    #tg_bot.notify_listeners("Testing flow_v2...")
    # flow_v2(notify_users=False)
    pass