import configparser
import time

import pandas as pd

from gmocoin import GMOcoin
from utils.notify import send_message_to_line

conf = configparser.ConfigParser()
conf.read('config.ini')

ACCESS_KEY = conf['gmocoin']['access_key']
SECRET_KEY = conf['gmocoin']['secret_key']

gmocoin = GMOcoin(access_key=ACCESS_KEY, secret_key=SECRET_KEY)

interval = 60*15

df = pd.DataFrame()
send_message_to_line('Start Auto Trading...')
i, priceAtAsk = 0, 0
while True:
    time.sleep(interval)
    if i == 60*60*24/interval - 1:
        i = 0
        send_message_to_line('Data Collecting...') if len(
            df) < 672 - 1 else send_message_to_line('Auto Trading...')
    else:
        i += 1

    try:
        last = gmocoin.last
        df = df.append({'price': last}, ignore_index=True)
    except KeyError:
        send_message_to_line('Server Maintenance')
        continue

    if len(df) < 672:
        continue

    df['MA672'] = df['price'].rolling(window=672).mean()
    df['MA192'] = df['price'].rolling(window=192).mean()
    df['std'] = df['price'].rolling(window=192).std()

    df['-2σ'] = df['MA192'] - 2*df['std']
    df['+3σ'] = df['MA192'] + 3*df['std']

    price = df['price'].iloc[-1]
    MA672 = df['MA672'].iloc[-1]
    MA192 = df['MA192'].iloc[-1]
    lstPrice = df['price'].iloc[-2]
    lstMA192 = df['MA192'].iloc[-2]

    gmocoin.cancelBulkOrder({'symbols': ['XEM']})
    positions = gmocoin.position

    if positions['XEM'] != '0':
        if (priceAtAsk * 1.02 < price or df['+3σ'].iloc[-1] < price):
            params = {
                'symbol': 'XEM',
                'side': 'SELL',
                'executionType': 'LIMIT',
                'price': price,
                'size': positions['XEM']
            }
            gmocoin.order(params)
    else:
        if (MA672 < MA192 < price and lstPrice < lstMA192 or
                price < df['-2σ'].iloc[-1]):
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

    df = df.iloc[1:, :]
