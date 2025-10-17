from LLM import bullish_LLM, bearish_LLM, judge_LLM, summarizer_LLM
import pandas as pd
import logging
from db.headline_db import get_entry_summaries
 
# from fatwoman_dir_setup import LLM_data_path_newsapi_file, LLM_data_path_finnhub_file 

from telegram_bot import tg_bot


# Gets a ticker name as parameters, analyzes it, returns a summary text
def flow_v1(ticker_name="AAPL", notify_users=False, date:str="2025-10-16"): 
    df_headlines = get_entry_summaries(date)

    prompt = (
        f""" What do you think of buying {ticker_name} today ?: %s """ % df_headlines
    )
    logging.basicConfig(level=logging.INFO)

    bullish = bullish_LLM(name="v1_bull")
    bearish = bearish_LLM(name="v1_bear")
    judge = judge_LLM(name="v1_judge")

    res_opt = bullish.work(prompt)
    logging.info(f"res_opt response recieved")
    res_pes = bearish.work(prompt)
    logging.info(f"res_pes response recieved")

    judge_prompt = f""" Here are two opinions on buying {ticker_name} today. The first one is optimistic and the second one is pessimistic. Please provide a balanced and sensible conclusion based on both perspectives. optimistic: {res_opt}  pessimistic: {res_pes} """
    judge_res = judge.work(judge_prompt)
    logging.info(f"res_judge response recieved")

    summarized_text = summarizer_LLM(name="v1_summarizer").work(f"ticker: {ticker_name}; verdict= {judge_res}")
    logging.info(f"summarized_text: {summarized_text}")

    if notify_users:
        tg_bot.notify_listeners(f"---Analysis for {ticker_name}--- \n {summarized_text}") # send messages to telegram chat

    return summarized_text

 
if __name__ == "__main__": 
    flow_v1("AAPL", notify_users=True)
