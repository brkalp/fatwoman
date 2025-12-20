""" Created on 12-14-2025 18:34:42 @author: ripintheblue """
import logging
logging.basicConfig(level=logging.INFO)
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from Scripts_LLM_trader.db.db_daily_news_headlines import get_entry_summaries
import pandas as pd
import time
# from flows.trading_flow_v2 import flow_v2
from flows.trading_flow_v1 import flow_v1
from LLM import bullish_LLM, bearish_LLM, judge_LLM, summarizer_LLM
# from flows.trading_flow_POC import poc_flow
from data_gathering.FinnHub import save_news
from data_gathering.FinnHub import ticker_news
import Scripts_LLM_trader.db.trades_db as trades_db
# from data_gathering.db_price_fetcher import _get_market_values
import datetime as dt
import threading
from telegram_bot import tg_bot # this will explode if trading_flow is run as main
import json
import sys, os  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from LLM import consulter_LLM

import sys, traceback
def _tracehook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)
sys.excepthook = _tracehook

def get_headlines(ticker: str, date: str, headline_factory: str) -> str:
    if headline_factory == "get_entry_summaries":
        return get_entry_summaries(date)
    if headline_factory == "ticker_news":

        d = dt.datetime.strptime(date, "%Y-%m-%d")
        from_date = d - dt.timedelta(days=30)
        from_date = from_date.strftime("%Y-%m-%d")

        return ticker_news(ticker=ticker, from_date=from_date, to_date=date)
    
# Gets a ticker name as parameters, analyzes it, returns a summary text
def flow_v1(date:str="2025-10-16", ticker="AAPL", notify_users=False, headline_factory="get_entry_summaries"):

    flow_id = trades_db.add_base(date=date, ticker=ticker, flow_name ='trade_flow_v1')  # creates base flow entry
    # flow_id = flow_db.get_id(date=date, ticker=ticker) # TODO: this may return a wrong id, as date and ticker are not PK
    logging.info(f"{ticker}, {date}; flow_id: {flow_id}")

    df_headlines = get_headlines(ticker, date, headline_factory=headline_factory)
    bullish = bullish_LLM(name="v1_bull", flow_id=flow_id, ticker=ticker)
    bearish = bearish_LLM(name="v1_bear", flow_id=flow_id, ticker=ticker)
    judge = judge_LLM(name="v1_judge", flow_id=flow_id, ticker=ticker)

    prompt = f" What do you think of buying {ticker} today ?: {df_headlines} "
    logging.basicConfig(level=logging.INFO)

    resp_bullish = bullish.work(prompt)
    #logging.info(f"bullish response recieved")

    # TODO flow_chat.add(FLOW_ID, res_opt.chat_id)
    resp_bearish = bearish.work(prompt)
    #logging.info(f"pessimist response recieved")

    judge_prompt = f""" Here are two opinions on buying {ticker} today. The first one is optimistic and the second one is pessimistic. Please provide a balanced and sensible conclusion based on both perspectives. optimistic: {resp_bullish}  pessimistic: {resp_bearish} """
    resp_judge = judge.work(judge_prompt)
    #logging.info(f"judge response recieved")

    summarizer_prompt = f"ticker: {ticker}; verdict= {resp_judge}"
    resp_summarizer = summarizer_LLM(
        name="v1_summarizer", flow_id=flow_id, ticker=ticker
    ).work(summarizer_prompt)
    # logging.info(f"summarized_text: {resp_summarizer}")

    summarizer_json = json.loads(resp_summarizer)
    trades_db.add_order(flow_id=flow_id, order=summarizer_json["tendency"], amount=1)
    if notify_users:
        tg_bot.notify_listeners(
            f"---Analysis for {ticker}--- \n {resp_summarizer}"
        )  # send messages to telegram chat

    return resp_summarizer

def _worker_thread_flow_v1(ticker, notify_users, date, analysis_list):
    resp = flow_v1(ticker=ticker, date=date, notify_users=notify_users) #logging.info(f"Analyzed response for {ticker}:\n {resp}")
    analysis_list.append(resp)

def flow_top5(date:str="2025-10-16"):
    #logging.info("Starting POC trading flow... %s" % date)
    df_headlines = get_entry_summaries(date)
    prompt = (""" Please provide me with top 5 trade ideas based on news of today. I will buy and hold these till end of day and close them next morning. here are the headlines: %s """ %df_headlines)
    trader = consulter_LLM(name = 'v0_Adviser_for_top5')
    response = trader.work(prompt)  
    # logging.basicConfig(level=logging.INFO)
    #logging.info("Response: %s" % response) 
    return response.replace(' ','').split(",")  # should be list of tickers

#%% Execution
if __name__ == "__main__":
    logging.info("Starting LLM main")
    save_news() # Get news
    date = dt.datetime.today()
    analysis = [] # def flow_v2(date :str="2025-10-16", notify_users:bool=True):
    threads = []
    notify_users=True

    top5_tickers = flow_top5(date)
    for suggested_ticker in top5_tickers: 
        print(f"Starting thread for ticker: {suggested_ticker}")
        #logging.info(f"Starting thread for ticker: {suggested_ticker}")
        t = threading.Thread(target=_worker_thread_flow_v1, args=(suggested_ticker, False, date, analysis)) # thread
        t.start()
        threads.append(t) 
    
    for t in threads: # Wait for all threads to finish
        t.join()

    if notify_users:   
        tg_bot.notify_listeners(f"--{date}'s report--" + '\n'.join(analysis)) # send messages to telegram chat


    script_end_log()
