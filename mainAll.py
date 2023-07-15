import configparser
import time

from talib import BBANDS
from talib import MA_Type
from talib import MA
import yfinance
import mplfinance as mpf

from gmocoin import GMOcoin
from utils.notify import send_message_to_line


def derivative():
    result = 0
    for i in range(stack1):
        if df['MA2'].iloc[-i-1] > df['MA2'].iloc[-i-2]:
            result += 1
        else:
            result -= 1
    return (result > 0)


def derivative2():
    result = 0
    for i in range(stack1):
        if df['MA2'].iloc[-i-1] + df['MA2'].iloc[-i-3] > 2 * df['MA2'].iloc[-i-2]:
            result += 1
        else:
            result -= 1
    return (result > 0)


conf = configparser.ConfigParser()
conf.read('config.ini')

ACCESS_KEY = conf['gmocoin']['access_key']
SECRET_KEY = conf['gmocoin']['secret_key']

gmocoin = GMOcoin(access_key=ACCESS_KEY, secret_key=SECRET_KEY)

interval = 60*15
stack1, stack2 = 20, 192

send_message_to_line('Start Auto Trading...')
i, priceAtAsk = 0, 0
symbols = ['XEM', 'XRP', 'LTC', 'BCH', 'ETH', 'BTC']
Tickers = []
for s in symbols:
    Tickers.append(yfinance.Ticker(f'{s}-JPY'))

while True:
    time.sleep(interval)
    if i == 60*60*24/interval - 1:
        i = 0
        send_message_to_line('Auto Trading...')
    else:
        i += 1

    try:
        gmocoin.cancelBulkOrder({'symbols': symbols})
        positions = gmocoin.position
        posJPY = positions['JPY']  # example for try
    except Exception as e:
        send_message_to_line(e)
        send_message_to_line('Server Maintenance')
        continue
    for i in range(len(symbols)):
        symbol = symbols[i]
        try:
            df = Tickers[i].history(period='3d', interval='15m')
        except Exception as e:
            send_message_to_line(e)
            continue
        
        df['+2σ'], df['MA1'], df['-2σ'] = BBANDS(df['Close'], timeperiod=stack1, matype=MA_Type.EMA)
        df['MA2'] = MA(df['Close'], timeperiod=stack2)

        price = df['Close'].iloc[-1]
        MA1 = df['MA1'].iloc[-1]
        MA2 = df['MA2'].iloc[-1]
        lstMA1 = df['MA1'].iloc[-2]
        lstMA2 = df['MA2'].iloc[-2]

        if positions[symbol] != '0':
            if 1.02 * priceAtAsk < price or \
                    df['+2σ'].iloc[-1] < price and priceAtAsk < price or \
                    MA1 < MA2 and priceAtAsk < price:
                params = {
                    'symbol': symbol,
                    'side': 'SELL',
                    'executionType': 'LIMIT',
                    'price': price,
                    'size': positions[symbol]
                }
                gmocoin.order(params)
                mpf.plot(df, mav=(stack1, stack2), style='yahoo', savefig=f'{symbol}.png')
        else:
            if MA2 < MA1 and lstMA1 < lstMA2 and (derivative() or derivative2()) or \
                    price < df['-2σ'].iloc[-1]:
                size = str(int(float(posJPY)/price/4))  # maybe causes error 4 -> len(symbols)
                params = {
                    'symbol': symbol,
                    'side': 'BUY',
                    'executionType': 'LIMIT',
                    'price': price,
                    'size': size
                }
                gmocoin.order(params)
                priceAtAsk = price
                mpf.plot(df, mav=(stack1, stack2), style='yahoo', savefig=f'{symbol}.png')

        del df
