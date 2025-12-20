""" Created on 09-14-2025 19:03:34 @author: ripintheblue """  
import requests

from dotenv import load_dotenv
from Scripts_LLM_trader.db.db_daily_news_headlines import add_entry

from fatwoman_log_setup import script_end_log
from fatwoman_api_setup import finnhub_api_key
from fatwoman_dir_setup import LLM_data_path_finnhub_file
import pandas as pd
import requests

load_dotenv()
# finnhub_api_key=os.getenv("FINNHUB_API_KEY")
 
def save_news():
    print('Getting finnhub news...')
    url = "https://finnhub.io/api/v1/news?category=general&token=" + finnhub_api_key 
    news_list = requests.get(url).json()
    df0 = pd.DataFrame(news_list, columns=["headline", "summary", "datetime", "url"])
    df0['datetime'] = pd.to_datetime(df0['datetime'], unit='s')
    df1 = df0[['headline', 'summary', 'url']]
    print("Printing %i finnhub.io rows to %s" % (len(df1), LLM_data_path_finnhub_file))
    df1.to_csv(LLM_data_path_finnhub_file, index=False)

    for row in news_list: 
        add_entry(row["headline"], row["datetime"], row["summary"], row["url"], row.get("source", ""), "", 0)

    script_end_log()

def ticker_news(ticker :str, from_date:str, to_date:str): # this will require a painfull refactor later
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={from_date}&to={to_date}&token={finnhub_api_key}"
    resp = requests.get(url=url).json()
    list = [dict["headline"] for dict in resp]
    # list = list[:100]  # LIMIT 100

    joined = "; ".join(list)
    return joined
    
    

if __name__ == "__main__":
    save_news() 

# url = "https://finnhub.io/api/v1/news?category=general&token=" + finnhub_api_key
# res = requests.get(url).json()
# df0 = pd.DataFrame(res, columns=["headline", "summary", "datetime", "url"])
# df1 = df0[['headline', 'summary', 'url']]
# print("Printing %i finnhub.io rows to %s" % (len(df1), LLM_data_path_finnhub_file))
# df1.to_csv(LLM_data_path_finnhub_file, index=False)
# script_end_log()

# # without a date  endpoint
# # url = "https://finnhub.io/api/v1/news?category=general&token=" + finnhub_api_key
# # res = requests.get(url).json()
# # df0 = pd.DataFrame(res, columns=["headline", "summary", "datetime", "url"])
# # df1 = df0[['headline', 'summary', 'url']]
# # print("Printing %i finnhub.io rows to %s" % (len(df1), LLM_data_path_finnhub_file))
# # df1.to_csv(LLM_data_path_finnhub_file, index=False)

# # script_end_log()