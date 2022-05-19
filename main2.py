import configparser
import sys
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
priceAtAsk = 0 if len(sys.argv) == 1 else float(sys.argv[1])
i = 0
while True:
    time.sleep(interval)
    if i == 60*60*24/interval - 1:
        i = 0
        send_message_to_line('Auto Trading...')
    else:
        i += 1
    positions = gmocoin.position

    if 'XEM' not in positions:
        continue

    df = df.append(
        {'price': gmocoin.last}, ignore_index=True
    )

    if len(df) < 192:
        continue

    df['MA192'] = df['price'].rolling(window=192).mean()
    df['std'] = df['price'].rolling(window=192).std()

    df['+2σ'] = df['MA192'] + 2*df['std']
    df['-2σ'] = df['MA192'] - 2*df['std']
    df['+3σ'] = df['MA192'] + 3*df['std']
    df['-3σ'] = df['MA192'] - 3*df['std']

    price = df['price'].iloc[-1]
    MA192 = df['MA192'].iloc[-1]
    lstPrice = df['price'].iloc[-2]
    lstMA192 = df['MA192'].iloc[-2]

    pTwo = df['+2σ'].iloc[-1]
    mTwo = df['-2σ'].iloc[-1]
    pThree = df['+3σ'].iloc[-1]
    mThree = df['-3σ'].iloc[-1]
    lstpTwo = df['+2σ'].iloc[-2]
    lstmTwo = df['-2σ'].iloc[-2]

    gmocoin.cancel({'symbols': ['XEM']})

    if positions['XEM'] != '0':
        if price < MA192 and lstMA192 < lstPrice or \
                    pThree < price or \
                    price < pTwo and lstpTwo < lstPrice or \
                    price < mTwo and lstmTwo < lstPrice:
            params = {
                'symbol': 'XEM',
                'side': 'SELL',
                'executionType': 'LIMIT',
                'price': price,
                'size': positions['XEM']
            }
            gmocoin.order(params)
    else:
        if MA192 < price and lstPrice < lstMA192 or \
                price < mThree:
            size = str(int(0.95*float(positions['JPY'])/price))
            params = {
                'symbol': 'XEM',
                'side': 'BUY',
                'executionType': 'LIMIT',
                'price': price,
                'size': size
            }
            gmocoin.order(params)

    df = df.iloc[1:, :]
