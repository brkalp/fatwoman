# from flows.trading_flow_v1 import flow_1
# from flows.trading_flow_v2 import flow_v2
from data_gathering.FinnHub import save_news

import sys, os # To make it work no matter where it is executed from
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


if __name__ == "__main__":
    # print('flow_v2 executed successfully: \n' + flow_v2())
    save_news()
    # trading_flow_v1("AAPL", notify_users=True) 