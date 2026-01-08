from LLM import bullish_LLM, bearish_LLM, judge_LLM, summarizer_LLM
import json
import logging

# os.chdir(r'Z:\15GB\Scripts_LLM_trader')
from data_gathering.FinnHub import ticker_news
from Scripts_LLM_trader.db.db_daily_news_headlines import get_entry_summaries
from datetime import timedelta, datetime
import Scripts_LLM_trader.db.trades_db as trades_db
from telegram_bot import tg_bot
from fatwoman_log_setup import script_end_log

def get_headlines(ticker: str, date: str, headline_factory: str) -> str:
    if headline_factory == "get_entry_summaries":
        return get_entry_summaries(date)
    if headline_factory == "ticker_news":

        d = datetime.strptime(date, "%Y-%m-%d")
        from_date = d - timedelta(days=30)
        from_date = from_date.strftime("%Y-%m-%d")

        return ticker_news(ticker=ticker, from_date=from_date, to_date=date)


# Gets a ticker name as parameters, analyzes it, returns a summary text
def flow_v1(
    date: str = "2025-10-16",
    ticker="AAPL",
    notify_users=False,
    headline_factory="get_entry_summaries",
):
    flow_id = trades_db.add_base(date=date, ticker=ticker, flow_name ='trade_flow_v1')  # creates base flow entry
    # flow_id = flow_db.get_id(date=date, ticker=ticker) # TODO: this may return a wrong id, as date and ticker are not PK
    logging.info(f"{ticker}, {date}; flow_id: {flow_id}")

    df_headlines = get_headlines(ticker, date, headline_factory=headline_factory)
    bullish = bullish_LLM(name="v1_bull", flow_id=flow_id, ticker=ticker)
    bearish = bearish_LLM(name="v1_bear", flow_id=flow_id, ticker=ticker)
    judge = judge_LLM(name="v1_judge", flow_id=flow_id, ticker=ticker)

    prompt = f" What do you think of buying {ticker} today ?: {df_headlines} "
    logging.basicConfig(level=logging.INFO)

    resp_bullish = bullish.work(prompt)
    #logging.info(f"bullish response recieved")

    # TODO flow_chat.add(FLOW_ID, res_opt.chat_id)
    resp_bearish = bearish.work(prompt)
    #logging.info(f"pessimist response recieved")

    judge_prompt = f""" Here are two opinions on buying {ticker} today. The first one is optimistic and the second one is pessimistic. Please provide a balanced and sensible conclusion based on both perspectives. optimistic: {resp_bullish}  pessimistic: {resp_bearish} """
    resp_judge = judge.work(judge_prompt)
    #logging.info(f"judge response recieved")

    summarizer_prompt = f"ticker: {ticker}; verdict= {resp_judge}"
    resp_summarizer = summarizer_LLM(
        name="v1_summarizer", flow_id=flow_id, ticker=ticker
    ).work(summarizer_prompt)
    # logging.info(f"summarized_text: {resp_summarizer}")

    summarizer_json = json.loads(resp_summarizer)
    trades_db.add_order(flow_id=flow_id, order=summarizer_json["tendency"], amount=1)
    if notify_users:
        tg_bot.notify_listeners(
            f"---Analysis for {ticker}--- \n {resp_summarizer}"
        )  # send messages to telegram chat

    return resp_summarizer


if __name__ == "__main__":
    flow_v1(ticker="AAPL", notify_users=True)
