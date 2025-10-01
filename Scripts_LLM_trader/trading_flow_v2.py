# import json
# import ib_wrapper
from LLM import bullish_LLM, bearish_LLM, judge_LLM, summarizer_LLM
import pandas as pd
import os

from trading_flow_v1 import trading_flow_1
from trading_flow_POC import poc_flow_1

from fatwoman_log_setup import script_end_log
import logging
from fatwoman_dir_setup import LLM_data_path_newsapi_file, LLM_data_path_finnhub_file
from fatwoman_dir_setup import LLM_data_path


# gets 5 suggestion headlines from poc then all of them are fed to v1, to analyze further
def flow_v2():
    poc_resp_raw = os.path.join(
        LLM_data_path, "LLM_v0_Adviser_for_top5_latest_response.txt"
    )
    with open(poc_resp_raw, "r") as file:
        poc_resp = file.read().strip().split(",")
    analysis = []

    for suggested_ticker in poc_resp:
        analyzed_resp = trading_flow_1(suggested_ticker)
        logging.info(f"Analyzed response for {suggested_ticker}: {analyzed_resp}")
        analysis.append(analyzed_resp)
    return analysis


if __name__ == "__main__":
    flow_v2()
