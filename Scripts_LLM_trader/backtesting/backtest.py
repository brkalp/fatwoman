import csv, json, logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import pandas_market_calendars as mcal

from llm import flow_26_1
from headlines import ticker_news


def get_date_list_without_holidays(start_date: str, end_date: str, exchange: str = "NYSE") -> list[str]:
    cal = mcal.get_calendar(exchange)
    schedule = cal.schedule(start_date=start_date, end_date=end_date)
    return [d.strftime("%Y-%m-%d") for d in schedule.index]


def parse_agent_csv(csv_text: str) -> tuple[str, str, int]:
    # !! expects exactly:
    # ticker,tendency,confidence
    # AMZN,bullish,72
    lines = [ln.strip() for ln in csv_text.splitlines() if ln.strip()]
    ticker, tendency, confidence = [x.strip() for x in lines[1].split(",")[:3]]
    return ticker, tendency, int(confidence)


def run_day(date_str: str, ticker: str) -> dict:
    logging.info("Running flow for: %s", date_str)

    data = {"headlines": ticker_news(date=date_str, ticker=ticker)}
    # print(f"Headlines for {ticker} on {date_str}: {data['headlines']}")
    agent_csv = flow_26_1(ticker=ticker, data=data)

    out_ticker, tendency, confidence = parse_agent_csv(agent_csv)

    return {
        "ticker": out_ticker,
        "date": date_str,
        "tendency": tendency,
        "confidence": confidence,
        "dataOBJ": data,
    }


def backtest(
    start_date: str,
    end_date: str,
    ticker: str,
    out_csv: str = "results.csv",
    workers: int = 10,
    save_headlines: bool = True,
):
    dates = get_date_list_without_holidays(start_date, end_date)

    rows = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_day, d, ticker) for d in dates]
        for f in as_completed(futures):
            r = f.result()

            if not isinstance(r, dict):
                raise TypeError(f"run_day returned {type(r)} instead of dict: {r!r}")

            # optional: also ensure required keys exist
            missing = [k for k in ("ticker", "date", "tendency", "confidence", "dataOBJ") if k not in r]
            if missing:
                raise KeyError(f"run_day result missing keys {missing}: {r}")

            rows.append(r)

    rows.sort(key=lambda r: r["date"])


    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ticker", "date", "tendency", "confidence", "dataOBJ"])
        w.writeheader()
        w.writerows(rows)




backtest(start_date="2025-06-01", end_date="2025-12-10", ticker="NVDA", out_csv="backtest_NVDIA_2025.csv", workers=30)