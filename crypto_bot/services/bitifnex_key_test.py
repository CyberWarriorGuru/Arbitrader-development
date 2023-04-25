
import hashlib
import hmac
import json
import requests

from datetime import datetime

BASE_URL = "https://api.bitfinex.com/"
MARGIN_PL_PATH = "v2/auth/r/info/margin/base"
POSITIONS_PATH = "v2/auth/r/positions"
SIG_PREFIX = '/api/'

API_KEY = ''
API_SECRET = ""


def nonce():
    return str(datetime.timestamp(datetime.now()) * 1000).split(".")[0]


def api_auth(path, non, rawBody, api_key=None, secret=None):
    sig = SIG_PREFIX + path + non + rawBody
    hashedSig = hmac.new(secret.encode() if secret else API_SECRET.encode(),
                         sig.encode(), hashlib.sha384).hexdigest()
    return {
        "bfx-nonce": non,
        "bfx-apikey": api_key if api_key else API_KEY,
        "bfx-signature": hashedSig
    }


def margin_pl():
    non = nonce()
    body = {}
    rawBody = json.dumps(body)
    path = MARGIN_PL_PATH

    auth = api_auth(path, non, rawBody)
    r = requests.post(BASE_URL + path, headers=auth, json=body, verify=True)
    print("\n" + str(r))
    if r.status_code == 200:
        get_data = r.json()
        print("Margin Info:")
        print(get_data)


def positions_status():
    non = nonce()
    body = {}
    rawBody = json.dumps(body)
    path = POSITIONS_PATH

    auth = api_auth(path, non, rawBody)
    r = requests.post(BASE_URL + path, headers=auth, json=body, verify=True)
    print("\n" + str(r))
    if r.status_code == 200:
        get_data = r.json()
        print("Position Status:")
        print(get_data)

if __name__ == '__main__':
    margin_pl()
    positions_status()