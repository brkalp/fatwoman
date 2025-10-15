from flows.trading_flow_v1 import flow_1
from flows.trading_flow_v2 import flow_v2

if __name__ == "__main__":
    print('flow_v2 executed successfully: \n' + flow_v2())
    # trading_flow_v1("AAPL", notify_users=True) 