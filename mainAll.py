import configparser
import time

from talib import BBANDS
from talib import MA_Type
from talib import MA
import yfinance
import mplfinance as mpf

from gmocoin import GMOcoin
from utils.notify import send_message_to_line


def calcPrice(symbol, price):
    if symbol in []:
        return f'{price:.3f}'
    else:
        return f'{price:.0f}'


def calcSize(symbol, size):
    if symbol in []:
        size /= 4
        return f'{size:.0f}'
    elif symbol in []:
        size /= 3
        return f'{size:.1f}'
    elif symbol in []:
        size /= 2
        return f'{size:.2f}'
    elif symbol in []:
        size /= 2
        return f'{size:.3f}'
    elif symbol in []:
        size /= 2
        return f'{size:.4f}'


conf = configparser.ConfigParser()
conf.read('config.ini')

ACCESS_KEY = conf['gmocoin']['access_key']
SECRET_KEY = conf['gmocoin']['secret_key']

gmocoin = GMOcoin(access_key=ACCESS_KEY, secret_key=SECRET_KEY)

interval = 15  # minites
stack1, stack2, stack3 = 20, 192, 672
period = (interval*stack3 + 60*24 - 1)//(60*24) + 1

send_message_to_line('Start Auto Trading...')
isOrder = False
symbols = []
count, priceAtAsk = 0, [0] * len(symbols)
positions = gmocoin.position
Tickers = []
for i, s in enumerate(symbols):
    if positions[s] != '0':
        priceAtAsk[i] = float(gmocoin.ticker(s)['data'][0]['last'])
    Tickers.append(yfinance.Ticker(f'{s}-JPY'))

while True:
    time.sleep(60 * interval)
    if count > 60*24/interval:
        count = 0
        send_message_to_line('Auto Trading...')
    else:
        count += 1

    if isOrder:
        gmocoin.cancelBulkOrder({'symbols': symbols})
        isOrder = False
    positions = gmocoin.position
    if 'JPY' in positions:
        posJPY = positions['JPY']  # example for try
    else:
        continue

    for i, symbol in enumerate(symbols):
        df = Tickers[i].history(period='{period}d', interval='{interval}m')
        if len(df['Close']) == 0:
            del df
            continue

        df['up'], df['MA1'], df['low'] = BBANDS(df['Close'],
                                                timeperiod=stack1,
                                                nbdevup=3,
                                                nbdevup=3,
                                                matype=MA_Type.EMA)
        df['MA2'] = MA(df['Close'], timeperiod=stack2)
        df['MA3'] = MA(df['Close'], timeperiod=stack3)

        price = df['Close'].iloc[-1]
        orderPrice = calcPrice(symbol, price)
        paa = priceAtAsk[i]
        MA1 = df['MA1'].iloc[-1]
        MA2 = df['MA2'].iloc[-1]
        MA3 = df['MA3'].iloc[-1]
        lstMA1 = df['MA1'].iloc[-2]
        lstMA2 = df['MA2'].iloc[-2]
        lstMA3 = df['MA3'].iloc[-2]

        if positions[symbol] != '0':
            if df['up'].iloc[-1] < price and paa < price or \
                    MA1 < MA2 and lstMA2 < lstMA1 and paa < price or \
                    MA1 < MA3 and paa < price or \
                    price < 0.9 * paa:
                params = {
                    'symbol': symbol,
                    'side': 'SELL',
                    'executionType': 'LIMIT',
                    'price': orderPrice,
                    'size': positions[symbol]
                }
                gmocoin.order(params)
                isOrder = True
                mpf.plot(df, mav=(stack1, stack2, stack3), type='line', style='yahoo', savefig=f'{symbol}.png')
        else:
            if MA3 < MA1 and lstMA1 < lstMA3 or price < df['low'].iloc[-1]:
                size = calcSize(symbol, float(posJPY)/price)
                params = {
                    'symbol': symbol,
                    'side': 'BUY',
                    'executionType': 'LIMIT',
                    'price': orderPrice,
                    'size': size
                }
                gmocoin.order(params)
                priceAtAsk[i] = price
                isOrder = True
                mpf.plot(df, mav=(stack1, stack2, stack3), type='line', style='yahoo', savefig=f'{symbol}.png')

        del df
