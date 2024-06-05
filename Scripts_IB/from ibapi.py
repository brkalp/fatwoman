from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import sys, time, threading

class MyWrapper(EWrapper):
    def __init__(self):
        self.data_received = False
        self.error_occurred = False
        self.stop_event = threading.Event()

    def historicalData(self, reqId, bar):
        print(f"Date: {bar.date}, Close: {bar.close}")
        self.data_received = True

    def error(self, reqId, errorCode, errorString):
        if errorCode == 162:  # This error code corresponds to market data subscription warning
            print(f"Market Data Subscription Warning: {errorString}")
            self.error_occurred = True
            # sys.exit(1)  # Exit the program with a non-zero status code
        else:
            print(f"Error: {errorCode} - {errorString}")
            # sys.exit(1)  # Exit the program with a non-zero status code

class MyClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)

def print_rotating_indicator(stop_event):  # <-- Added the stop_event parameter
    indicators = ['/', '-', '\\', '|']
    while not stop_event.is_set():  # <-- Modified this line
        for indicator in indicators:
            print(f"\rWaiting for data {indicator}", end='')
            time.sleep(0.5)

def connect(port, ID = 3):
    # Create an instance of the wrapper and client
    wrapper = MyWrapper()
    client = MyClient(wrapper)
    wrapper.client = client  # Set the client in the wrapper

    print('Connecting')
    # Connect to the Interactive Brokers API (paper trading account)
    client.connect("127.0.0.1", port, clientId=3)
    print('Connected')
    return client

def disconnect(client):
    # Disconnect from the API
    client.disconnect()
    print('\nClient Disconnect')

def get_data(client):
    # Define the contract for the SPY ETF
    contract = Contract()
    contract.symbol = "VX"
    contract.secType = "FUT"
    contract.lastTradeDateOrContractMonth = "202310"
    contract.exchange = "CFE"
    contract.currency = "USD"

    # Request historical data
    print('Requesting Data')
    df = client.reqHistoricalData(1, contract, "", "7 D", "1 day", "TRADES", 1, 1, False, []) # useRTH = only data during regular trading hours
    print(df)
    print('Data requested')

def firstrun():
    client = connect(7496)
    disconnect(client)

if __name__ == "__main__":
    get_data(client)
