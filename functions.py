# -*- coding: utf-8 -*-
import ast
import base64

import json
import mintersdk.minterapi
import requests
import telebot
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from mintersdk.minterapi import MinterAPI
from mintersdk.sdk import wallet
from mintersdk.sdk.transactions import MinterSendCoinTx
from sql import sql

import const
import sqlhelper
from langs import en, ru

minter_wallet = mintersdk.sdk.wallet.MinterWallet
minter = MinterAPI(api_url=const.node_url)
bot = telebot.TeleBot(const.token)

sql_base = sqlhelper.sqlbase(const.path)


def get_address(mnemonic):
    create = minter_wallet.create(mnemonic=mnemonic)
    private_key = create['address']

    return private_key


def get_token():
    PARAMS = {'grant_type': 'client_credentials'}
    HEADERS = {'Content-Type': 'application/x-www-form-urlencoded',
               'Authorization': 'Basic NWRjODAyYWM0N2ZjOWZmZTE1OTBjMzAxOjU4OTc1MjJiYTEwYWRmNTc4ODlkZmJlZjhhZDU3ZGQ3'}
    r = requests.post(url='https://bip-banker.net/oauth/token?grant_type=client_credentials', params=PARAMS,
                      headers=HEADERS)
    token = r.json()['accessToken']

    return token


# BIP BANKER
# def sell_price():
#     PARAMS = {'days': '1', 'type': 'sell'}
#     HEADERS = {'Content-Type': 'application/x-www-form-urlencoded',
#                'Authorization': 'Bearer ' + get_token()}
#     r = requests.get(url='https://bip-banker.net/v1/stats/rate', params=PARAMS,
#                       headers=HEADERS)
#     price = (float(r.json()['rate']) / 100) * 112
#     return price
#
#
# def buy_price():
#     PARAMS = {'days': '1', 'type': 'buy'}
#     HEADERS = {'Content-Type': 'application/x-www-form-urlencoded',
#                'Authorization': 'Bearer ' + get_token()}
#     r = requests.get(url='https://bip-banker.net/v1/stats/rate', params=PARAMS,
#                      headers=HEADERS)
#     price = (float(r.json()['rate']) / 100) * 101
#     return price


def sell_price():
    price = float(sql('request', "SELECT sell FROM price"))
    return price


def buy_price():
    price = float(sql('request', "SELECT buy FROM price"))
    return price


def private_key(mnemonic):
    create = minter_wallet.create(mnemonic=mnemonic)
    private_key = create['private_key']

    return private_key


def sendCoin(address, pk, to, value):
    nonce = minter.get_nonce(address=str(address))
    tx = MinterSendCoinTx(coin="BIP", to=to, value=float(value), nonce=nonce, gas_coin="BIP")
    tx.sign(private_key=pk)
    send = minter.send_transaction(tx=tx.signed_tx)
    print(send)
    hash = send['result']['hash'].lower()
    return "Mt" + hash


def get_balance(address, coin=const.coin):
    balance = minter.get_balance(str(address))
    try:
        balance = balance['result']['balance'][coin]
        balance = float(balance) / 10 ** 18
    except:
        balance = 0

    return balance


def get_price(coin):
    amount = int(json.loads(requests.get(const.node_url + "/estimate_coin_buy?coin_to_sell=BIP&value_to_buy"
                                                          "=10000000000000000&coin_to_buy=" + coin).text)["result"][
                     "will_pay"]) / 10000000000000000
    # amount = round(amount, 4)
    return amount


def get_pbip():
    price = json.loads(requests.get('https://api.bip.dev/api/price').text)['data']['price']
    amount = int(price) / 10000
    return amount


def get_all_coins_in_bip(address):
    balances = minter.get_balance(address)['result']['balance']
    a = 0
    for i in balances.items():
        amount = int(i[1]) / 1000000000000000000
        if i[0] != 'BIP':
            price = get_price(str(i[0]))
            a += float(amount) * price
        else:
            a += float(amount)
    return a


def usd_rate(valut):
    r = requests.get(url='https://api.ratesapi.io/api/latest?base=USD&symbols=' + valut)
    js = r.json()

    try:
        js = js['rates'][str(valut)]
    except KeyError:
        js = '0'
    return float(js)


def get_key(password):
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(password)
    return base64.urlsafe_b64encode(digest.finalize())


def encrypt(password, token):
    f = Fernet(get_key(password))
    return f.encrypt(bytes(token))


def decrypt(password, token):
    # de = decrypt('1234'.encode('utf-8'), en)
    # print(de)
    f = Fernet(get_key(password))
    return f.decrypt(bytes(token))


def truncate(num: float, n: int = 2) -> float:
    return int(num * 10 ** n) / 10 ** n


def cbt(tid):
    # 0 - Альфа
    # 1 - ЗБТ
    # 2 - Релиз
    status = int(sql('request', "SELECT cbt FROM status"))
    if tid in const.admins:
        return True
    elif status == 0:
        return False
    elif status == 1:
        admins = bot.get_chat_administrators(-1001386519148)
        testers_list = []
        for i in admins:
            testers_list.append(i.user.id)
        if tid in testers_list:
            return True
        else:
            return False
    elif status == 2:
        return True


def lang(tid):
    lang_sql = sql('request', "SELECT lang FROM users WHERE tid='" + str(tid) + "'")
    if lang_sql is None:
        lang = ru
    if lang_sql is not None:
        lg = lang_sql
        if lg == 'russian':
            lang = ru
        elif lg == 'english':
            lang = en
    return lang


def num_ver(number, type):
    PARAMS = {'access_key': '7ecd6213ec658e8a84b3eb1c7c884975',
              'number': number}
    r = requests.post(url=const.numverify, params=PARAMS)
    js = r.json()
    if type == 1:
        verify = js['local_format']
    elif type == 2:
        verify = js['international_format']
    elif type == 3:
        verify = js['country_prefix']
    elif type == 4:
        verify = js['country_code']
    elif type == 5:
        verify = js['country_name']
    elif type == 6:
        verify = js['location']
    elif type == 7:
        verify = js['carrier']
    elif type == 8:
        verify = js['line_type']
    return verify
