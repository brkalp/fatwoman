from LLM import bullish_LLM, bearish_LLM, judge_LLM, summarizer_LLM
import pandas as pd
import logging
from db.headline_db import get_entry_summaries
from db.chat_cache_db import get_id as get_chat_id
import db.flow_db as flow
import db.flow_chat_conn as flow_chat_conn


# from fatwoman_dir_setup import LLM_data_path_newsapi_file, LLM_data_path_finnhub_file

from telegram_bot import tg_bot


# Gets a ticker name as parameters, analyzes it, returns a summary text
def flow_v1(date: str = "2025-10-16", ticker_name="AAPL", notify_users=False):
    flow.add_base(date=date, ticker=ticker_name)
    flow_id = flow.get_id(date=date, ticker=ticker_name)
    df_headlines = get_entry_summaries(date)
    bullish = bullish_LLM(name="v1_bull")
    bearish = bearish_LLM(name="v1_bear")
    judge = judge_LLM(name="v1_judge")

    prompt = f" What do you think of buying {ticker_name} today ?: {df_headlines} "
    logging.basicConfig(level=logging.INFO)

    resp_bullish = bullish.work(prompt)
    logging.info(f"bullish response recieved")
    flow_chat_conn.add_chat(flow_id, get_chat_id(prompt, resp_bullish))

    # TODO flow_chat.add(FLOW_ID, res_opt.chat_id)
    resp_bearish = bearish.work(prompt)
    logging.info(f"pessimist response recieved")
    flow_chat_conn.add_chat(flow_id, get_chat_id(prompt, resp_bearish))

    judge_prompt = f""" Here are two opinions on buying {ticker_name} today. The first one is optimistic and the second one is pessimistic. Please provide a balanced and sensible conclusion based on both perspectives. optimistic: {resp_bullish}  pessimistic: {resp_bearish} """
    resp_judge = judge.work(judge_prompt)
    logging.info(f"judge response recieved")
    flow_chat_conn.add_chat(flow_id, get_chat_id(prompt, resp_judge))

    summarizer_prompt = f"ticker: {ticker_name}; verdict= {resp_judge}"
    resp_summarizer = summarizer_LLM(name="v1_summarizer").work(summarizer_prompt)
    logging.info(f"summarized_text: {resp_summarizer}")
    flow_chat_conn.add_chat(flow_id, get_chat_id(prompt, resp_summarizer))

    summarzier_json = resp_summarizer.json()
    flow.add_order(order=summarzier_json["tendency"], amount=1)
    if notify_users:
        tg_bot.notify_listeners(
            f"---Analysis for {ticker_name}--- \n {resp_summarizer}"
        )  # send messages to telegram chat

    return resp_summarizer


if __name__ == "__main__":
    flow_v1("AAPL", notify_users=True)
