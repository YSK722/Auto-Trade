from utils.notify import send_message_to_line
from gmocoin import GMOcoin
import pandas as pd
import time
import configparser
from sklearn.linear_model import SGDClassifier
import collections
import random
from sklearn.feature_extraction import DictVectorizer
from sklearn import preprocessing


conf = configparser.ConfigParser()
conf.read('config.ini')

ACCESS_KEY = conf['gmocoin']['access_key']
SECRET_KEY = conf['gmocoin']['secret_key']

gmocoin = GMOcoin(access_key=ACCESS_KEY, secret_key=SECRET_KEY)

interval = 60*15
stack1, stack2 = 96, 192

df = pd.DataFrame()
send_message_to_line('Start Auto Trading...')
i, priceAtAsk = 0, 0
VX = DictVectorizer()
VY = preprocessing.LabelEncoder()
model = SGDClassifier()
firstY = 0
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
    elif len(df) == stack2:
        D = []
        diff = df.diff()
        for i in range(1, stack2 - stack1):
            x = collections.Counter(list(diff.iloc[i::stack1 + i]))
            y = 1 if diff.iloc[stack1 + i] > 0 else 0
            D.append((x, y))

        firstY = D[0][1]
        random.shuffle(D)
        VX = DictVectorizer()
        VY = preprocessing.LabelEncoder()
        X = VX.fit_transform([d[0] for d in D])
        Y = VY.fit_transform([d[1] for d in D])
        model.fit(X, Y)

    test = collections.Counter(list(df.diff().iloc[stack2 - stack1::]))
    Xtest = VX.transform(test)
    score = model.predict_proba(Xtest)
    price = df['price'].iloc[-1]

    gmocoin.cancelBulkOrder({'symbols': ['XEM']})
    positions = gmocoin.position

    if positions['XEM'] != '0':
        if score[firstY] > 0.5 and priceAtAsk < price:
            send_message_to_line(
                f'BUY (price: {price}, P_down: {score[firstY]})')
            """
            params = {
                'symbol': 'XEM',
                'side': 'SELL',
                'executionType': 'LIMIT',
                'price': price,
                'size': positions['XEM']
            }
            gmocoin.order(params)
            """
    else:
        if score[firstY] < 0.2:
            send_message_to_line(
                f'BUY (price: {price}, P_down: {score[firstY]})')
            """
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
            """

    df = df.iloc[1:, :]
