
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import BarData
import threading
import time

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data_received_event = threading.Event()

    data = []

    def historicalData(self, reqId: int, bar: BarData):
        self.data.append([bar.date, bar.open, bar.high, bar.low, bar.close])

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        print('Historical data end')
        self.data_received_event.set()

    def error(self, reqId, errorCode, errorString):
        if reqId in [-1]:
            print(f"{errorCode} {errorString}")
        else:
            print(f"Error: {reqId} {errorCode} {errorString}")
        # if errorCode in [162]:  # ErrorCode 162: Historical Market Data Service error message
            self.data_received_event.set()

def get_historical_data(contract, duration_str='1 M', candle_size='1 day'):
    ibapi = IBapi()
    ibapi.connect('127.0.0.1', 4001, 1)
    
    # Start the socket in a thread
    api_thread = threading.Thread(target=ibapi.run, daemon=True)
    api_thread.start()

    time.sleep(1)  # Allow time for connection

    ibapi.reqHistoricalData(
                            reqId=1,
                            contract=contract,
                            endDateTime='',
                            durationStr=duration_str,
                            barSizeSetting=candle_size,
                            whatToShow='MIDPOINT',
                            useRTH=0,
                            formatDate=1,
                            keepUpToDate=False,
                            chartOptions=[]
                            )

    # Wait for data to be loaded or an error to occur
    ibapi.data_received_event.wait()

    ibapi.disconnect()
    return ibapi.data

if __name__ == "__main__":
    contract = Contract()
    contract.symbol = 'EUR'
    contract.secType = 'CASH'
    contract.exchange = 'IDEALPRO'
    contract.currency = 'USD'

    historical_data = get_historical_data(contract)
    for entry in historical_data:
        print(entry)
