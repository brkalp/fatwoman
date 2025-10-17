from flows.trading_flow_v1 import flow_v1 
from flows.trading_flow_POC import poc_flow
import logging
from telegram_bot import tg_bot # this will explode if trading_flow is run as main


# FLOW 2: gets 5 suggestion headlines from poc then all of them are fed to v1, to analyze further
def flow_v2(date :str="2025-10-16"):
    logging.config(level=logging.INFO)
    analysis = []
    for suggested_ticker in poc_flow(date): # bunları paralel çalıştırmak lazım bağımsız
        logging.info(f"ANALYSING TICKER: {suggested_ticker}")
        analyzed_resp = flow_v1(suggested_ticker, date=date)
        logging.info(f"Analyzed response for {suggested_ticker}:\n {analyzed_resp}")
        analysis.append(analyzed_resp) 

    tg_bot.notify_listeners("--today's report--" + '\n'.join(analysis)) # send messages to telegram chat

    return analysis


if __name__ == "__main__":
    tg_bot.notify_listeners("Testing flow_v2...")
    flow_v2()

"""
def flow_v2():
    poc_resp_raw = os.path.join(
        LLM_data_path, "LLM_v0_Adviser_for_top5_latest_response.txt"
    )
    with open(poc_resp_raw, "r") as file:
        poc_resp = file.read().strip().split(",")
    analysis = []

    for suggested_ticker in poc_resp: # bunları paralel çalıştırmak lazım bağımsız
        analyzed_resp = trading_flow_1(suggested_ticker)
        logging.info(f"Analyzed response for {suggested_ticker}: {analyzed_resp}")
        analysis.append(analyzed_resp) 

    tg_bot.notify_listeners("--today's report--" + '\n'.join(analysis)) # send messages to telegram chat

    return analysis
"""
