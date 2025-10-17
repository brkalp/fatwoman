""" Created on 09-14-2025 19:03:34 @author: ripintheblue """
import logging 
from fatwoman_dir_setup import LLM_data_path_finnhub_file
from dotenv import load_dotenv

import pandas as pd
import requests
import os

load_dotenv()
finnhub_api_key=os.getenv("FINNHUB_API_KEY")

url = "https://finnhub.io/api/v1/news?category=general&token=" + finnhub_api_key
res = requests.get(url).json()
df0 = pd.DataFrame(res, columns=["headline", "summary", "datetime", "url"])
df1 = df0[['headline', 'summary', 'url']]
print("Printing %i finnhub.io rows to %s" % (len(df1), LLM_data_path_finnhub_file))
df1.to_csv(LLM_data_path_finnhub_file, index=False) 

# without a date  endpoint
# url = "https://finnhub.io/api/v1/news?category=general&token=" + finnhub_api_key
# res = requests.get(url).json()
# df0 = pd.DataFrame(res, columns=["headline", "summary", "datetime", "url"])
# df1 = df0[['headline', 'summary', 'url']]
# print("Printing %i finnhub.io rows to %s" % (len(df1), LLM_data_path_finnhub_file))
# df1.to_csv(LLM_data_path_finnhub_file, index=False)

# script_end_log()
