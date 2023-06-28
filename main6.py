import configparser
import time

from talib import BBANDS
from talib import MA_Type
from talib import MA
import yfinance
import mplfinance as mpf

from gmocoin import GMOcoin
from utils.notify import send_message_to_line

conf = configparser.ConfigParser()
conf.read('config.ini')

ACCESS_KEY = conf['gmocoin']['access_key']
SECRET_KEY = conf['gmocoin']['secret_key']

gmocoin = GMOcoin(access_key=ACCESS_KEY, secret_key=SECRET_KEY)

interval = 60*15
stack1, stack2 = 20, 192

send_message_to_line('Start Auto Trading...')
i, priceAtAsk = 0, 0
Ticker = yfinance.Ticker('XEM-JPY')
while True:
    time.sleep(interval)
    if i == 60*60*24/interval - 1:
        i = 0
        send_message_to_line('Auto Trading...')
    else:
        i += 1

    try:
        df = Ticker.history(period='7d', interval='15m')
    except KeyError:
        send_message_to_line('Server Maintenance')
        continue

    df['+2σ'], df['MA1'], df['-2σ'] = BBANDS(df['Close'], timeperiod=stack1, matype=MA_Type.EMA)
    df['MA2'] = MA(df['Close'], timeperiod=stack2)

    price = df['Close'].iloc[-1]
    MA2 = df['MA2'].iloc[-1]
    MA1 = df['MA1'].iloc[-1]
    lstPrice = df['Close'].iloc[-2]
    lstMA1 = df['MA1'].iloc[-2]
    lstMA2 = df['MA2'].iloc[-2]
    lstlstMA2 = df['MA2'].iloc[-3]

    try:
        gmocoin.cancelBulkOrder({'symbols': ['XEM']})
        positions = gmocoin.position
    except KeyError:
        send_message_to_line('Server Maintenance')
        continue

    if positions['XEM'] != '0':
        if priceAtAsk * 1.02 < price or \
                df['+2σ'].iloc[-1] < price and priceAtAsk < price or \
                MA1 < MA2 and priceAtAsk < price:
            params = {
                'symbol': 'XEM',
                'side': 'SELL',
                'executionType': 'LIMIT',
                'price': price,
                'size': positions['XEM']
            }
            gmocoin.order(params)
            mpf.plot(df, mav=(stack1, stack2), style='yahoo', savefig='XEM.png')
    else:
        if MA2 < MA1 and lstMA1 < lstMA2 < MA2 and MA2 + lstlstMA2 > 2*lstMA2 or \
                price < df['-2σ'].iloc[-1]:
            size = str(int(0.95*float(positions['JPY'])/price))
            params = {
                'symbol': 'XEM',
                'side': 'BUY',
                'executionType': 'LIMIT',
                'price': price,
                'size': size
            }
            gmocoin.order(params)
            priceAtAsk = price
            mpf.plot(df, mav=(stack1, stack2), style='yahoo', savefig='XEM.png')
