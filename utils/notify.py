import requests


def pprint(message):
    if isinstance(message, dict):
        s = ''
        for k, v in message.items():
            s += f'{k}:{v}\n'
        message = s
    return '\n'+message


def send_message_to_line(message):
    access_token = # 自分のLINEのアクセストークン
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    data = {'message': pprint(message)}
    requests.post(url='https://notify-api.line.me/api/notify',
                  headers=headers,
                  data=data)
