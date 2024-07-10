
# root='wss://ws.kite.trade'
import alpine.broker_api.ba_ka as kt
import pandas as pd
from time import sleep
with open('enctoken.txt', 'r') as rd:
    token = rd.read()
kite = kt.ba_ka("kite", "ULH359", token)
kws = kite.kws()  # For Websocket


print("Start..")
stock = {1793: 'AARTIIND', 5633: 'ACC',
         6401: 'ADANIENT', 3861249: 'ADANIPORTS'}
# print(list(stock.keys()))

ltp_data = {}


# def on_ticks(ws, ticks):
#     for symbol in ticks:
#         ltp_data[stock[symbol['instrument_token']]] = {
#             "ltp": symbol["last_price"], "High": symbol["ohlc"]["high"], "Low": symbol["ohlc"]["low"]}
#     print(ltp_data)
#     # print(ticks)

def on_ticks(ws, ticks):
    for symbol in ticks:
        ltp_data[stock[symbol['instrument_token']]] = {
            "ltp": symbol["last_price"]}
    print(ltp_data)
    # print(ticks)
    
def on_connect(ws, response):
    ws.subscribe(list(stock.keys()))
    # MODE_FULL , MODE_QUOTE MODE_LTP
    ws.set_mode(ws.MODE_QUOTE, list(stock.keys()))


kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.connect(threaded=True)
while len(ltp_data.keys()) != len(list(stock.keys())):
    sleep(0.5)
    continue

# while True:
#     for i in list(stock.values()):
#         ltp = ltp_data[i]['ltp']
#         high = ltp_data[i]['High']
#         print(i, ltp, high)

#         if ltp > high:
#             print("Yes")