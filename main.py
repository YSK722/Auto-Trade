import configparser
import time
import sys

import pandas as pd

from gmocoin import GMOcoin
from utils.notify import send_message_to_line

conf = configparser.ConfigParser()
conf.read('config.ini')

ACCESS_KEY = conf['gmocoin']['access_key']
SECRET_KEY = conf['gmocoin']['secret_key']

gmocoin = GMOcoin(access_key=ACCESS_KEY, secret_key=SECRET_KEY)

interval = 60*60

df = pd.DataFrame()
send_message_to_line('Start Auto Trading...')
priceAtAsk = 0 if len(sys.argv) == 1 else float(sys.argv[1])
i = 0
while True:
    time.sleep(interval)
    if i == 60*60*24/interval - 1:
        i = 0
        send_message_to_line('Data Collecting...') if len(df) < 168 - 1 else send_message_to_line('Auto Trading...')
    else:
        i += 1
    positions = gmocoin.position

    if 'XEM' not in positions:
        continue

    df = df.append(
        {'price': gmocoin.last}, ignore_index=True
    )

    if len(df) < 168:
        continue

    df['MA5'] = df['price'].rolling(window=5).mean()
    df['MA8'] = df['price'].rolling(window=8).mean()
    df['MA13'] = df['price'].rolling(window=13).mean()
    df['MA168'] = df['price'].rolling(window=168).mean()

    price = df['price'].iloc[-1]
    MA3 = round(df['price'].rolling(window=3).mean(), 3)
    MA5 = df['MA5'].iloc[-1]
    MA8 = df['MA8'].iloc[-1]
    MA13 = df['MA13'].iloc[-1]
    MA168 = df['MA168'].iloc[-1]

    gmocoin.cancel({'symbols': ['XEM']})

    if positions['XEM'] != '0':
        if priceAtAsk < price \
                and not (MA13 < MA8 < MA5) \
                or MA5 < MA8 < MA13:
            priceAtBid = price if MA5 < MA8 < MA13 else max(price, MA3)
            params = {
                'symbol': 'XEM',
                'side': 'SELL',
                'executionType': 'LIMIT',
                'price': priceAtBid,
                'size': positions['XEM']
            }
            r = gmocoin.order(params)
            send_message_to_line(r)
    else:
        lastMA5 = df['MA5'].iloc[-2]
        lastMA8 = df['MA8'].iloc[-2]
        lastMA13 = df['MA13'].iloc[-2]
        if MA168 < MA13 < MA8 < MA5 \
                and not (lastMA13 < lastMA8 < lastMA5):
            priceAtAsk = min(price, MA3)
            size = str(int(0.95*float(positions['JPY'])/priceAtAsk))
            params = {
                'symbol': 'XEM',
                'side': 'BUY',
                'executionType': 'LIMIT',
                'price': priceAtAsk,
                'size': size
            }
            r = gmocoin.order(params)
            send_message_to_line(r)

    df = df.iloc[1:, :]
