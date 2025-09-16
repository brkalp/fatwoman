import json
import ib_wrapper
from LLM import consulter_LLM

from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import LLM_flow1_response_file, LLM_flow1_order_file

if __name__ == "__main__":
    trader = consulter_LLM()
    response = trader.work()

    orders = json.loads(response)

    for order in orders:
        ib_wrapper.doOrder(order)
    # response.csv(LLM_flow1_response_file)

script_end_log()



"""response =
    [
    {
        "action": "buy",
        "asset": "GLD",
        "confidence": 70,
        "reason": "Fed cut expectations, ETF inflows, and geopolitical risk support further upside in gold despite recent records."
    },
    {
        "action": "buy",
        "asset": "TLT",
        "confidence": 55,
        "reason": "Morgan Stanley sees a series of rate cuts; adding duration can benefit if the 10-year yield drifts lower."
    }
    ]
"""
