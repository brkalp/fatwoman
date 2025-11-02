# import json
# import ib_wrapper 
from LLM import *
import pandas as pd
import logging
from db.headline_db import get_entry_summaries

# Based on fed data returns top 5 tickers to buy & hold
def poc_flow(date:str="2025-10-16"):

    df_headlines = get_entry_summaries(date)

    prompt = (""" Please provide me with top 5 trade ideas based on news of today. I will buy and hold these till end of day and close them next morning. here are the headlines: %s """ %df_headlines)
    trader = consulter_LLM(name = 'v0_Adviser_for_top5')
    response = trader.work(prompt)  

    logging.basicConfig(level=logging.INFO)
    logging.info("Response: %s" % response) 

    return response.replace(' ','').split(",")  # should be list of tickers

if __name__ == "__main__":
    poc_flow("2025-10-16") 

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
