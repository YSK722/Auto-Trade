import hmac
import hashlib
import json
import time
from datetime import datetime
from socket import gaierror
from urllib3.exceptions import NewConnectionError, MaxRetryError

import requests

from utils.notify import send_message_to_line


class GMOcoin(object):
    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key
        self.url = 'https://api.coin.z.com'

    def _request(self, endpoint, pp='/public', params=None, method='GET'):
        time.sleep(1)
        timestamp = '{0}000'.format(
            int(time.mktime(datetime.now().timetuple())))
        body = json.dumps(params) if params else ''

        text = timestamp + method + endpoint + body
        sign = hmac.new(bytes(self.secret_key.encode('ascii')), bytes(
            text.encode('ascii')), hashlib.sha256).hexdigest()

        headers = {
            "API-KEY": self.access_key,
            "API-TIMESTAMP": timestamp,
            "API-SIGN": sign
        }

        while True:
            try:
                url = self.url+pp+endpoint
                if method == 'GET':
                    r = requests.get(url, headers=headers, params=params)
                else:
                    r = requests.post(url, headers=headers, data=body)
                break
            except (requests.exceptions.RequestException, requests.exceptions.ConnectionError, gaierror, NewConnectionError, MaxRetryError) as e:
                send_message_to_line(repr(e.args))
                time.sleep(1)

        return r.json()

    def ticker(self, symbol='XEM'):
        endpoint = f'/v1/ticker?symbol={symbol}'
        return self._request(endpoint=endpoint)

    def last(self, symbol='XEM'):
        return float(self.ticker(symbol)['data'][0]['last'])

    def ask(self, symbol='XEM'):
        return float(self.ticker(symbol)['data'][0]['ask'])

    def bid(self, symbol='XEM'):
        return float(self.ticker(symbol)['data'][0]['bid'])

    def trades(self, params=None, symbol='XEM'):
        endpoint = f'/v1/trades?symbol={symbol}'
        return self._request(endpoint=endpoint, params=params)

    def order_books(self, params=None, symbol='XEM'):
        endpoint = f'/v1/orderbooks?symbol={symbol}'
        return self._request(endpoint=endpoint, params=params)

    def assets(self):
        pp = '/private'
        endpoint = '/v1/account/assets'
        return self._request(endpoint=endpoint, pp=pp)

    def activeOrders(self, params):
        pp = '/private'
        endpoint = '/v1/activeOrders'
        return self._request(endpoint=endpoint, pp=pp, params=params)

    @property
    def position(self):
        assets = self.assets()
        if not assets.get('data'):
            return {}
        return {d['symbol']: d['amount'] for d in assets['data']}

    def order(self, params):
        pp = '/private'
        endpoint = '/v1/order'
        return self._request(endpoint=endpoint, pp=pp, params=params,
                             method='POST')

    def cancelBulkOrder(self, params):
        pp = '/private'
        endpoint = '/v1/cancelBulkOrder'
        return self._request(endpoint=endpoint, pp=pp, params=params,
                             method='POST')

    def transaction(self, symbol='XEM'):
        endpoint = f'/v1/trades?symbol={symbol}'
        return self._request(endpoint=endpoint)

    @property
    def ask_rate(self):
        transaction = self.transaction()
        ask_transaction = [d for d in transaction['data']['list']
                           if d['side'] == 'BUY']
        return float(ask_transaction[0]['price'])
