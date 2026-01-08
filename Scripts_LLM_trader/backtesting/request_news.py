""" Created on 12-26-2025 00:36:02 @author: ripintheblue """
import logging
import fatwoman_log_setup
# from fatwoman_log_setup import script_end_log
import pandas as pd
import time
import os
# import seaborn as sns
# sns.set()
# script_end_log()

from fatwoman_log_setup import script_end_log
from fatwoman_api_setup import finnhub_api_key
from fatwoman_dir_setup import LLM_data_path_finnhub_file

import requests

API_KEY = finnhub_api_key
symbol = "AAPL"
date_from = "2025-12-01"
date_to = "2025-12-02"

url = "https://finnhub.io/api/v1/company-news"
params = {
    "symbol": symbol,
    "from": date_from,
    "to": date_to,
    "token": API_KEY
}

resp = requests.get(url, params=params)
resp.raise_for_status()
news = resp.json()
df_news = pd.DataFrame(news)
df_news["datetime"] = pd.to_datetime(df_news["datetime"], unit="s", utc=True)
df_news.to_clipboard()
# for n in news:
    # print(n["datetime"], n["headline"])

# def save_news():
#     print('Getting finnhub news...')
#     url = "https://finnhub.io/api/v1/news?category=general&token=" + finnhub_api_key 
#     news_list = requests.get(url).json()
#     df0 = pd.DataFrame(news_list, columns=["headline", "summary", "datetime", "url"])
#     df0['datetime'] = pd.to_datetime(df0['datetime'], unit='s')
#     df1 = df0[['headline', 'summary', 'url']]
#     print("Printing %i finnhub.io rows to %s" % (len(df1), LLM_data_path_finnhub_file))
#     df1.to_csv(LLM_data_path_finnhub_file, index=False)

#     for row in news_list: 
#         add_entry(row["headline"], row["datetime"], row["summary"], row["url"], row.get("source", ""), "", 0)

#     script_end_log()
# ]