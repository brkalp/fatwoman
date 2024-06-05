""" Created on 10-08-2023 15:44:20 @author: ripintheblue """
from ib_insync import *
# util.startLoop()  # uncomment this line when in a notebook

ib = IB()
print('Connecting')
# Connect to the Interactive Brokers API (paper trading account)
ib.connect("127.0.0.1", 4002, clientId=4)
print('Connected')

# Contract details
contract = Contract()
contract.symbol = "VX"
contract.secType = "FUT"
contract.lastTradeDateOrContractMonth = "202310"
contract.exchange = "SMART"
contract.currency = "USD"

bars = ib.reqHistoricalData(contract, endDateTime='', durationStr=' 1D', barSizeSetting='1 H', whatToShow='MIDPOINT', useRTH=False)
df = util.df(bars)
print(df)