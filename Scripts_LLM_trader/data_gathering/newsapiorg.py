""" Created on 09-18-2025 17:24:00 @author: ripintheblue """
import logging
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_api_setup import newapiorg_api_key
from fatwoman_dir_setup import LLM_data_path_newsapi_file

import pandas as pd
import time
import os
import requests, datetime as dt

def get_news_api_org(to_date: pd.Timestamp = None):
    # to_date = None
    # url = "https://newsapi.org/v2/everything"  # supports historical ranges
    # to_dt = pd.Timestamp.utcnow() if to_date is None else pd.Timestamp(to_date)
    # from_time = to_dt - dt.timedelta(days=3)
        # "from": pd.Timestamp(from_time).isoformat(),
        # "to": pd.Timestamp(to_dt).isoformat(),
        # "q": "business" # historical endpoint

    API_KEY = newapiorg_api_key
    url = f"https://newsapi.org/v2/top-headlines?category=business&pageSize=100&language=en&apiKey={API_KEY}" ## simple endpoint

    params = {
        "apiKey": API_KEY,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 100,
    }

    resp = requests.get(url, params=params )
    data = resp.json()
    df0 = pd.DataFrame(data["articles"])
    df1 = df0[['source', 'title', 'description','publishedAt', 'content']]
    print("Printing %i rows from newsapiorg.io to %s" % (len(df1), LLM_data_path_newsapi_file))
    df1.to_csv(LLM_data_path_newsapi_file, index=False)

if __name__ == "__main__":
    # for date_today in pd.date_range(start="2023-01-30", end="2023-01-31"):
    #     print(f"Getting headlines for date: {date_today}")
    #     to_date = date_today
    # get_news_api_org(to_date)
    get_news_api_org()
    script_end_log()

# better endpoint
    # if mode == "top-headlines":
    #     url = "https://newsapi.org/v2/top-headlines"
    #     params = {
    #         "apiKey": API_KEY,
    #         "country": country if sources is None else None,  # can't mix with sources
    #         "category": category if sources is None else None,
    #         "sources": sources,                                # optional alternative
    #         "pageSize": 100,
    #         "language": "en",
    #         "q": q,  # optional keyword filter on headlines only


# has more noise Less noise: the second feed is heavy on PR wires, aggregators, and niche sites → higher pump/PR bias.
# API_KEY = newapiorg_api_key
# url = f"https://newsapi.org/v2/top-headlines?category=business&pageSize=100&language=en&apiKey={API_KEY}"
# url = "https://newsapi.org/v2/everything"

# # from_time = (dt.datetime.utcnow() - dt.timedelta(days=3)).isoformat("T") + "Z"

# params = {
#     "q": "stocks OR market OR economy",
#     "sortBy": "publishedAt",
#     "language": "en",
#     "searchIn": "title,description", 
#     "pageSize": 100,
#     "apiKey": API_KEY,
# }

# resp = requests.get(url, params=params )
# data = resp.json()
# len(data["articles"])

# for article in data["articles"][:5]:
#     print(article["title"])

# script_end_log()


