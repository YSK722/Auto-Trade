import configparser
import time

from talib import BBANDS
from talib import MA_Type
from talib import MA
from talib import RSI
import yfinance
import mplfinance as mpf

from gmocoin import GMOcoin
from utils.notify import send_message_to_line


def calcPrice(symbol, price):
    if symbol in ['DOGE', 'ADA', 'MONA', 'DAI', 'ENJ', 'QTUM', 'XTZ', 'BAT', 'XLM', 'XEM', 'XRP']:
        return f'{price:.3f}'
    else:
        return f'{price:.0f}'


def calcSize(symbol, size):
    if symbol in ['DOGE', 'ADA', 'MONA', 'DAI', 'ENJ', 'BAT', 'XLM', 'XEM', 'XRP']:
        size /= 4
        return f'{size:.0f}'
    elif symbol in ['LINK', 'DOT', 'QTUM', 'XTZ', 'LTC']:
        size /= 4
        return f'{size:.1f}'
    elif symbol in ['SOL', 'ATOM', 'BCH', 'ETH']:
        size /= 3
        return f'{size:.2f}'
    elif symbol in ['MKR']:
        size /= 3
        return f'{size:.3f}'
    else:
        size /= 2
        return f'{size:.4f}'


def showChart(df, symbol, stack):
    df = df.iloc[- stack:]
    apd = [mpf.make_addplot(df['up'].tolist()),
           mpf.make_addplot(df['low'].tolist(), color='tab:blue'),
           mpf.make_addplot(df['MA2'].tolist()),
           mpf.make_addplot(df['EMA2'].tolist()),
           mpf.make_addplot(df['RSI'].tolist(), panel=1),
           mpf.make_addplot([30] * stack, linestyle='-.', panel=1),
           mpf.make_addplot([70] * stack, linestyle='-.', color='tab:orange', panel=1)]
    try:
        mpf.plot(df, type='candle', addplot=apd, style='yahoo', savefig=f'{symbol}.png')
    except ValueError:
        pass


conf = configparser.ConfigParser()
conf.read('config.ini')

ACCESS_KEY = conf['gmocoin']['access_key']
SECRET_KEY = conf['gmocoin']['secret_key']

gmocoin = GMOcoin(access_key=ACCESS_KEY, secret_key=SECRET_KEY)

#interval = 15  # minites
#stack1, stack2 = 192, 672
interval = 5  # minites
#stack1, stack2 = 36, 48
#interval = 1  # minites
#stack1, stack2 = 240, 720
chartStack = 12 * 24
upper, lower = 4, 2

#isOrder = False
symbols = ['SOL', 'DOGE', 'LINK', 'ADA', 'MONA', 'DAI', 'MKR', 'ATOM', 'DOT', 'ENJ', 'QTUM', 'XTZ', 'BAT', 'XLM', 'XEM', 'XRP', 'LTC', 'BCH', 'ETH', 'BTC']
stack1 = [12, 8, 12, 28, 36, 16, 40, 52, 20, 72, 40, 40, 60, 48, 48, 16, 24, 16, 12, 20]
stack2 = [4, 12, 4, 48, 56, 68, 64, 76, 40, 32, 72, 68, 12, 44, 52, 8, 20, 28, 16, 24]
count, countAsk, countBid, priceAtAsk = 0, 0, 0, [0]*len(symbols)
positions = gmocoin.position
Tickers = []
for i, s in enumerate(symbols):
    if positions[s] != '0':
        priceAtAsk[i] = gmocoin.ask(s)
    Tickers.append(yfinance.Ticker(f'{s}-JPY'))

send_message_to_line('Start Auto Trading...')
while True:
    time.sleep(60 * interval)
    count += 1
    if count >= 60*24/interval:
        send_message_to_line(f'Auto Trading...\n{countAsk} Asks, {countBid} Bids for 24h')
        count, countAsk, countBid = 0, 0, 0
    """
    if isOrder:
        gmocoin.cancelBulkOrder({'symbols': symbols})
        isOrder = False
    """
    positions = gmocoin.position
    if 'JPY' in positions:
        posJPY = positions['JPY']  # example for try
    else:
        continue

    for i, symbol in enumerate(symbols):
        period = (interval*(stack1[i] + stack2[i]) + 60*24 - 1)//(60*24) + 1
        df = Tickers[i].history(period=f'{period}d', interval=f'{interval}m')
        if len(df['Close']) == 0:
            del df
            continue

        df['up'], df['MA1'], df['low'] = BBANDS(df['Close'],
                                                timeperiod=stack1[i],
                                                nbdevup=upper,
                                                nbdevdn=lower)
        df['MA2'] = MA(df['Close'], timeperiod=stack2[i])
        df['EMA2'] = MA(df['Close'], timeperiod=stack2[i], matype=MA_Type.EMA)
        df['RSI'] = RSI(df['Close'])

        price = df['Close'].iloc[-1]
        #orderPrice = calcPrice(symbol, price)
        paa = priceAtAsk[i]
        fpaa = gmocoin.ask(symbol)
        pab = gmocoin.bid(symbol)
        up = df['up'].iloc[-1]
        low = df['low'].iloc[-1]
        MA2 = df['MA2'].iloc[-1]
        EMA2 = df['EMA2'].iloc[-1]
        RSI1 = df['RSI'].iloc[-1]
        lstMA2 = df['MA2'].iloc[-2]
        lstEMA2 = df['EMA2'].iloc[-2]
        ystMA2 = df['MA2'].iloc[-1-stack1[i]]
        ystEMA2 = df['EMA2'].iloc[-1-stack1[i]]

        if positions[symbol] != '0':
            if price < low:
                priceAtAsk[i] = fpaa
            elif RSI1 > 70 and up < price or 0 < EMA2 - MA2 < ystEMA2 - ystMA2 and paa < pab*0.9982:
                params = {
                    'symbol': symbol,
                    'side': 'SELL',
                    'executionType': 'MARKET',
                    'size': positions[symbol]
                }
                #'price':orderPrice,
                #gmocoin.cancelBulkOrder({'symbols': [symbol]})
                gmocoin.order(params)
                countBid += 1
                #showChart(df, symbol, chartStack)
        else:
            if price < low or MA2 - EMA2 < (lstMA2 - lstEMA2)/2:
                size = calcSize(symbol, float(posJPY)/price)
                params = {
                    'symbol': symbol,
                    'side': 'BUY',
                    'executionType': 'MARKET',
                    'size': size
                }
                #gmocoin.cancelBulkOrder({'symbols': [symbol]})
                gmocoin.order(params)
                priceAtAsk[i] = fpaa
                countAsk += 1
                #showChart(df, symbol, chartStack)

        del df

import configparser
import time

from talib import BBANDS
from talib import MA_Type
from talib import MA
from talib import RSI
import yfinance
import mplfinance as mpf

from gmocoin import GMOcoin
from utils.notify import send_message_to_line


def calcPrice(symbol, price):
    if symbol in ['DOGE', 'ADA', 'MONA', 'DAI', 'ENJ', 'QTUM', 'XTZ', 'BAT', 'XLM', 'XEM', 'XRP']:
        return f'{price:.3f}'
    else:
        return f'{price:.0f}'


def calcSize(symbol, size):
    if symbol in ['DOGE', 'ADA', 'MONA', 'DAI', 'ENJ', 'BAT', 'XLM', 'XEM', 'XRP']:
        size /= 4
        return f'{size:.0f}'
    elif symbol in ['LINK', 'DOT', 'QTUM', 'XTZ', 'LTC']:
        size /= 4
        return f'{size:.1f}'
    elif symbol in ['SOL', 'ATOM', 'BCH', 'ETH']:
        size /= 3
        return f'{size:.2f}'
    elif symbol in ['MKR']:
        size /= 3
        return f'{size:.3f}'
    else:
        size /= 2
        return f'{size:.4f}'


def showChart(df, symbol, stack):
    df = df.iloc[- stack:]
    apd = [mpf.make_addplot(df['up'].tolist()),
           mpf.make_addplot(df['low'].tolist(), color='tab:blue'),
           mpf.make_addplot(df['MA2'].tolist()),
           mpf.make_addplot(df['EMA2'].tolist()),
           mpf.make_addplot(df['RSI'].tolist(), panel=1),
           mpf.make_addplot([30] * stack, linestyle='-.', panel=1),
           mpf.make_addplot([70] * stack, linestyle='-.', color='tab:orange', panel=1)]
    try:
        mpf.plot(df, type='candle', addplot=apd, style='yahoo', savefig=f'{symbol}.png')
    except ValueError:
        pass


conf = configparser.ConfigParser()
conf.read('config.ini')

ACCESS_KEY = conf['gmocoin']['access_key']
SECRET_KEY = conf['gmocoin']['secret_key']

gmocoin = GMOcoin(access_key=ACCESS_KEY, secret_key=SECRET_KEY)

#interval = 15  # minites
#stack1, stack2 = 192, 672
interval = 5  # minites
#stack1, stack2 = 36, 48
#interval = 1  # minites
#stack1, stack2 = 240, 720
chartStack = 12 * 24
upper, lower = 4, 2

#isOrder = False
symbols = ['SOL', 'DOGE', 'LINK', 'ADA', 'MONA', 'DAI', 'MKR', 'ATOM', 'DOT', 'ENJ', 'QTUM', 'XTZ', 'BAT', 'XLM', 'XEM', 'XRP', 'LTC', 'BCH', 'ETH', 'BTC']
stack1 = [12, 8, 12, 28, 36, 16, 40, 52, 20, 72, 40, 40, 60, 48, 48, 16, 24, 16, 12, 20]
stack2 = [4, 12, 4, 48, 56, 68, 64, 76, 40, 32, 72, 68, 12, 44, 52, 8, 20, 28, 16, 24]
count, countAsk, countBid, priceAtAsk = 0, 0, 0, [0]*len(symbols)
positions = gmocoin.position
Tickers = []
for i, s in enumerate(symbols):
    if positions[s] != '0':
        priceAtAsk[i] = gmocoin.ask(s)
    Tickers.append(yfinance.Ticker(f'{s}-JPY'))

send_message_to_line('Start Auto Trading...')
while True:
    time.sleep(60 * interval)
    count += 1
    if count >= 60*24/interval:
        send_message_to_line(f'Auto Trading...\n{countAsk} Asks, {countBid} Bids for 24h')
        count, countAsk, countBid = 0, 0, 0
    """
    if isOrder:
        gmocoin.cancelBulkOrder({'symbols': symbols})
        isOrder = False
    """
    positions = gmocoin.position
    if 'JPY' in positions:
        posJPY = positions['JPY']  # example for try
    else:
        continue

    for i, symbol in enumerate(symbols):
        period = (interval*(stack1[i] + stack2[i]) + 60*24 - 1)//(60*24) + 1
        df = Tickers[i].history(period=f'{period}d', interval=f'{interval}m')
        if len(df['Close']) == 0:
            del df
            continue

        df['up'], df['MA1'], df['low'] = BBANDS(df['Close'],
                                                timeperiod=stack1[i],
                                                nbdevup=upper,
                                                nbdevdn=lower)
        df['MA2'] = MA(df['Close'], timeperiod=stack2[i])
        df['EMA2'] = MA(df['Close'], timeperiod=stack2[i], matype=MA_Type.EMA)
        df['RSI'] = RSI(df['Close'])

        price = df['Close'].iloc[-1]
        #orderPrice = calcPrice(symbol, price)
        paa = priceAtAsk[i]
        fpaa = gmocoin.ask(symbol)
        pab = gmocoin.bid(symbol)
        up = df['up'].iloc[-1]
        low = df['low'].iloc[-1]
        MA2 = df['MA2'].iloc[-1]
        EMA2 = df['EMA2'].iloc[-1]
        RSI1 = df['RSI'].iloc[-1]
        lstMA2 = df['MA2'].iloc[-2]
        lstEMA2 = df['EMA2'].iloc[-2]
        ystMA2 = df['MA2'].iloc[-1-stack1[i]]
        ystEMA2 = df['EMA2'].iloc[-1-stack1[i]]

        if positions[symbol] != '0':
            if price < low:
                priceAtAsk[i] = fpaa
            elif RSI1 > 70 and up < price or 0 < EMA2 - MA2 < ystEMA2 - ystMA2 and paa < pab*0.9982:
                params = {
                    'symbol': symbol,
                    'side': 'SELL',
                    'executionType': 'MARKET',
                    'size': positions[symbol]
                }
                #'price':orderPrice,
                #gmocoin.cancelBulkOrder({'symbols': [symbol]})
                gmocoin.order(params)
                countBid += 1
                #showChart(df, symbol, chartStack)
        else:
            if price < low or MA2 - EMA2 < (lstMA2 - lstEMA2)/2:
                size = calcSize(symbol, float(posJPY)/price)
                params = {
                    'symbol': symbol,
                    'side': 'BUY',
                    'executionType': 'MARKET',
                    'size': size
                }
                #gmocoin.cancelBulkOrder({'symbols': [symbol]})
                gmocoin.order(params)
                priceAtAsk[i] = fpaa
                countAsk += 1
                #showChart(df, symbol, chartStack)

        del df

