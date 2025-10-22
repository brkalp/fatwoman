""" Created on 09-14-2025 19:03:34 @author: ripintheblue """  
import requests

import os
from dotenv import load_dotenv
from db.headline_db import add_entry

load_dotenv()
finnhub_api_key=os.getenv("FINNHUB_API_KEY")

def _get_news():
    url = "https://finnhub.io/api/v1/news?category=general&token=" + finnhub_api_key 
    return requests.get(url).json()
 
def save_news():
    news_list = _get_news()
    for n in news_list: 
        add_entry(n["headline"], n["datetime"], n["summary"], n["url"], n.get("source", ""), "", 0)
 

if __name__ == "__main__": 
    save_news()
