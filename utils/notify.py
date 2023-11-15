import requests
from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError
from socket import gaierror
from urllib3.exceptions import NewConnectionError, MaxRetryError


def pprint(message):
    if isinstance(message, dict):
        s = ''
        for k, v in message.items():
            s += f'{k}:{v}\n'
        message = s
    #return '\n'+message
    return message


def send_message_to_line(message):
    line_bot_api = LineBotApi() # 自分のLINEのアクセストークン
    try:
        line_bot_api.push_message(,
                                  TextSendMessage(text=pprint(message)))
    except (LineBotApiError, requests.exceptions.ConnectionError, gaierror, NewConnectionError, MaxRetryError) as e:
        send_message_to_line_old(message)

def send_message_to_line_old(message):
    access_token = # 自分のLINEのアクセストークン
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    data = {'message': pprint(message)}
    try:
        requests.post(url='https://notify-api.line.me/api/notify',
                      headers=headers,
                      data=data)
    except (LineBotApiError, requests.exceptions.ConnectionError, gaierror, NewConnectionError, MaxRetryError) as e:
        print(e)
