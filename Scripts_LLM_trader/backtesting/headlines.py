import requests
from fatwoman_api_setup import finnhub_api_key
from datetime import datetime, timedelta

def ticker_news(ticker :str, date:str ): # this will require a painfull refactor later
    

    d = datetime.strptime(date, "%Y-%m-%d")
    from_date = d - timedelta(days=30)
    from_date = from_date.strftime("%Y-%m-%d")
 

    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={from_date}&to={date}&token={finnhub_api_key}"
    resp = requests.get(url=url).json()
    list = [dict["headline"] for dict in resp]
    # list = list[:100]  # LIMIT 100

    joined = "; ".join(list)
    return joined
