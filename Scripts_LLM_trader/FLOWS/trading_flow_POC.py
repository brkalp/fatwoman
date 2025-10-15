# import json
# import ib_wrapper 
from LLM import *
import pandas as pd

from fatwoman_log_setup import script_end_log
import logging
from fatwoman_dir_setup import LLM_data_path_newsapi_file, LLM_data_path_finnhub_file
from fatwoman_dir_setup import LLM_flow1_response_file, LLM_flow1_order_file


# Based on fed data returns top 5 tickers to buy & hold
def poc_flow():
    print(f"Getting headlines: {LLM_data_path_finnhub_file}")
    df_headlines_1 = pd.read_csv(LLM_data_path_finnhub_file)['headline']
    print(f"Getting headlines: {LLM_data_path_newsapi_file}")
    df_headlines_2 = pd.read_csv(LLM_data_path_newsapi_file)['title'].rename('headline')
    df_headlines = pd.concat( [df_headlines_1, df_headlines_2] )

    prompt = (""" Please provide me with top 5 trade ideas based on news of today. I will buy and hold these till end of day and close them next morning. here are the headlines: %s """ %df_headlines)
    trader = consulter_LLM(name = 'v0_Adviser_for_top5')
    response, tokens = trader.work(prompt) 
    print("Response: ", response)
    # print(tokens)

    logging.info("Response: %s" % response)
    logging.info("Tokens used: %s" % tokens)

if __name__ == "__main__":
    poc_flow()
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
