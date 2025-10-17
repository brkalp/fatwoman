from LLM import bullish_LLM, bearish_LLM, judge_LLM, summarizer_LLM
import pandas as pd
 
# from fatwoman_dir_setup import LLM_data_path_newsapi_file, LLM_data_path_finnhub_file 

from telegram_bot import tg_bot

def get_headlines():
    print(f"Getting headlines: {LLM_data_path_finnhub_file}")
    df_headlines_1 = pd.read_csv(LLM_data_path_finnhub_file)["headline"]
    print(f"Getting headlines: {LLM_data_path_newsapi_file}")
    df_headlines_2 = pd.read_csv(LLM_data_path_newsapi_file)["title"].rename("headline")
    df_headlines = pd.concat([df_headlines_1, df_headlines_2])

    return df_headlines

# Gets a ticker name as parameters, analyzes it, returns a summary text
def flow_1(ticker_name="AAPL", notify_users=False, date=""): 
    df_headlines = get_headlines().to_list()

    prompt = (
        f""" What do you think of buying {ticker_name} today ?: %s """ % df_headlines
    )
    
    bullish = bullish_LLM(name="v1_bull", loc_override=ticker_name)
    bearish = bearish_LLM(name="v1_bear", loc_override=ticker_name)
    judge = judge_LLM(name="v1_judge", loc_override=ticker_name)

    res_opt = bullish.work(prompt)
    print(f"res_opt response recieved")
    res_pes = bearish.work(prompt)
    print(f"res_pes response recieved")

    judge_prompt = f""" Here are two opinions on buying {ticker_name} today. The first one is optimistic and the second one is pessimistic. Please provide a balanced and sensible conclusion based on both perspectives. optimistic: {res_opt}  pessimistic: {res_pes} """
    judge_res = judge.work(judge_prompt)
    print(f"res_judge response recieved")

    summarized_text = summarizer_LLM(name="v1_summarizer", loc_override=ticker_name).work("ticker: "+ ticker_name + ",  " +judge_res)
    print(f"summarized_text: {summarized_text}")

    if notify_users:
        tg_bot.notify_listeners(f"---Analysis for {ticker_name}--- \n {summarized_text}") # send messages to telegram chat

    return summarized_text

 
if __name__ == "__main__": 
    flow_1("AAPL", notify_users=True)
