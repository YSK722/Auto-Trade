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
stack1, stack2 = 20, 192

df = pd.DataFrame()
send_message_to_line('Start Auto Trading...')
i, priceAtAsk = 0, 0
while True:
    time.sleep(interval)
    if i == 60*60*24/interval - 1:
        i = 0
        send_message_to_line('Data Collecting...') if len(
            df) < stack2 - 1 else send_message_to_line('Auto Trading...')
    else:
        i += 1

    try:
        last = gmocoin.last
        df = df.append({'price': last}, ignore_index=True)
    except KeyError:
        send_message_to_line('Server Maintenance')
        continue

    if len(df) < stack2:
        continue

    df['MA2'] = df['price'].rolling(window=stack2).mean()
    df['MA1'] = df['price'].rolling(window=stack1).mean()
    df['std'] = df['price'].rolling(window=stack1).std()

    df['-σ'] = df['MA1'] - df['std']
    df['-2σ'] = df['MA1'] - 2*df['std']
    df['+2σ'] = df['MA1'] + 2*df['std']

    price = df['price'].iloc[-1]
    MA2 = df['MA2'].iloc[-1]
    MA1 = df['MA1'].iloc[-1]
    lstPrice = df['price'].iloc[-2]
    lstMA1 = df['MA1'].iloc[-2]

    gmocoin.cancelBulkOrder({'symbols': ['XEM']})
    positions = gmocoin.position

    if positions['XEM'] != '0':
        if priceAtAsk * 1.02 < price or df['+2σ'].iloc[-1] < price and priceAtAsk < price:
            params = {
                'symbol': 'XEM',
                'side': 'SELL',
                'executionType': 'LIMIT',
                'price': price,
                'size': positions['XEM']
            }
            gmocoin.order(params)
    else:
        if MA2 < MA1 and price < df['-σ'].iloc[-1] or price < df['-2σ'].iloc[-1]:
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
