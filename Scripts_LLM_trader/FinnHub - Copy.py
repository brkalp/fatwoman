""" Created on 09-14-2025 19:03:34 @author: ripintheblue """
import logging
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_api_setup import finnhub
from fatwoman_dir_setup import LLM_data_path_finnhub
import pandas as pd
import requests
import os

url = "https://finnhub.io/api/v1/news?category=general&token=" + finnhub
res = requests.get(url).json()
df0 = pd.DataFrame(res, columns=["headline", "summary", "datetime", "url"])
df1 = df0[['headline', 'summary', 'url']]
print("Printing %i finnhub.io rows to %s" % (len(df1), LLM_data_path_finnhub))
df1.to_csv(LLM_data_path_finnhub, index=False)

script_end_log()
