# import json
# import ib_wrapper 
from LLM import *
import pandas as pd
from datetime import datetime as dt

from fatwoman_log_setup import script_end_log
import logging
from fatwoman_dir_setup import LLM_data_path_newsapi_file, LLM_data_path_finnhub_file
from fatwoman_dir_setup import LLM_flow1_response_file, LLM_flow1_order_file

def poc_flow_backtest():
    # Get headlines at date x
    for date_today in pd.date_range(start="2023-01-30", end="2023-01-31"):
        print(f"Getting headlines for date: {date_today}")
        to_date = date_today

    print(f"Getting headlines: {LLM_data_path_finnhub_file}")
    df_headlines_1 = pd.read_csv(LLM_data_path_finnhub_file)['headline']
    print(f"Getting headlines: {LLM_data_path_newsapi_file}")
    df_headlines_2 = pd.read_csv(LLM_data_path_newsapi_file)['title'].rename('headline')
    df_headlines = pd.concat( [df_headlines_1, df_headlines_2] )

    prompt = (""" Please provide me with top 5 trade ideas based on news of today. I will buy and hold these till end of day and close them next morning. here are the headlines: %s """ %df_headlines)
    trader = consulter_LLM(name = 'Adviser_for_top5')
    response, tokens = trader.work(prompt) 
    print("Response: ", response)
    # print(tokens)

    logging.info("Response: %s" % response)
    logging.info("Tokens used: %s" % tokens)

new_row.to_csv("data.csv", mode="a", header=False, index=False)


if __name__ == "__main__":
    poc_flow_backtest()
    script_end_log()


    
    # """orders = json.loads(response)


    # for order in orders:
    #     ib_wrapper.doOrder(order)"""
    # # response.csv(LLM_flow1_response_file)

# """response =
#     [
#     {
#         "action": "buy",
#         "asset": "GLD",
#         "confidence": 70,
#         "reason": "Fed cut expectations, ETF inflows, and geopolitical risk support further upside in gold despite recent records."
#     },
#     {
#         "action": "buy",
#         "asset": "TLT",
#         "confidence": 55,
#         "reason": "Morgan Stanley sees a series of rate cuts; adding duration can benefit if the 10-year yield drifts lower."
#     }
#     ]
# """
