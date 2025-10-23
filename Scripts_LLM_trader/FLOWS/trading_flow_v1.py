from LLM import bullish_LLM, bearish_LLM, judge_LLM, summarizer_LLM
import pandas as pd
import logging
from db.headline_db import get_entry_summaries
from db.chat_cache_db import get_id as get_chat_id, set_flow_id
import db.flow_db as flow_db 

from telegram_bot import tg_bot

# LLM'in içine flow_id'si koysak daha iyi

# Gets a ticker name as parameters, analyzes it, returns a summary text
def flow_v1(date: str = "2025-10-16", ticker_name="AAPL", notify_users=False):
    flow_db.add_base(date=date, ticker=ticker_name) # creates base flow entry
    flow_id = flow_db.get_id(date=date, ticker=ticker_name)
    
    df_headlines = get_entry_summaries(date)
    bullish = bullish_LLM(name="v1_bull")
    bearish = bearish_LLM(name="v1_bear")
    judge = judge_LLM(name="v1_judge")

    prompt = f" What do you think of buying {ticker_name} today ?: {df_headlines} "
    logging.basicConfig(level=logging.INFO)

    resp_bullish = bullish.work(prompt)
    logging.info(f"bullish response recieved")

    # TODO flow_chat.add(FLOW_ID, res_opt.chat_id)
    resp_bearish = bearish.work(prompt)
    logging.info(f"pessimist response recieved")

    judge_prompt = f""" Here are two opinions on buying {ticker_name} today. The first one is optimistic and the second one is pessimistic. Please provide a balanced and sensible conclusion based on both perspectives. optimistic: {resp_bullish}  pessimistic: {resp_bearish} """
    resp_judge = judge.work(judge_prompt)
    logging.info(f"judge response recieved")

    summarizer_prompt = f"ticker: {ticker_name}; verdict= {resp_judge}"
    resp_summarizer = summarizer_LLM(name="v1_summarizer").work(summarizer_prompt)
    logging.info(f"summarized_text: {resp_summarizer}")

    summarzier_json = resp_summarizer.json()
    flow_db.add_order(order=summarzier_json["tendency"], amount=1)
    if notify_users:
        tg_bot.notify_listeners(
            f"---Analysis for {ticker_name}--- \n {resp_summarizer}"
        )  # send messages to telegram chat

    return resp_summarizer


if __name__ == "__main__":
    flow_v1(ticker_name="AAPL", notify_users=True)
