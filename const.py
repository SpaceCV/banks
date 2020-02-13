# -*- coding: utf-8 -*-
import base64
from uuid import getnode as get_mac
from sql import sql

# if get_mac() == 110425379764441:
#     os = ''
#     token = base64.b64decode('OTUyNzkwMDcwOkFBR3dmbS1oYmhqWXRWVVlKckFidnhia2hneHdZNG1TQ1A0').decode('utf-8')
# elif get_mac() == 164926748093578:
#     os = '/home/Ocean_Bank/'
#     token = base64.b64decode('OTExMDQyODIyOkFBSGtvUENnX2tELUFTLUZ5RFU4YU5DRlFSN3FTRG9fMlhR').decode('utf-8')

if get_mac() == 110425379764441:
    os = ''
    token = base64.b64decode('OTUyNzkwMDcwOkFBR3dmbS1oYmhqWXRWVVlKckFidnhia2hneHdZNG1TQ1A0').decode('utf-8')
elif get_mac() == 164926748094385:
    os = '/home/ocean/'
    token = base64.b64decode('OTUyNzkwMDcwOkFBR3dmbS1oYmhqWXRWVVlKckFidnhia2hneHdZNG1TQ1A0').decode('utf-8')

bpubkey = os + 'bpubkey.pem'
fprivkey = os + 'fprivkey.pem'

path = os + 'db.db'
qr_path = os + 'qr_codes/'
bip_dev = 'https://api.bip.dev'
btc1001 = 'https://minter.1001btc.com/getcfg/'
coin = 'BIP'
currency = ['RUB', 'USD', 'EUR']
langs = ['english', 'russian']
admins = [111489667, 200711590]
users = [723744060, 186365094, 958241771, 591253, 108794197, 373946570, 710303458, 270224738, 882811101, 340447474,
         71731775]
mobile = 200
min_mob = 15
group_cid = -1001386519148
main = ['Платежи', 'Кабинет', 'История']
numverify = 'http://apilayer.net/api/validate'

mnemonic = base64.b64decode('dmFzdCBzdGVhayB0b21hdG8gYXBhcnQga25vdyBob2xkIGxpYmVydHkgbWFnaWMgYmVuZWZpdCBlbmhhbmNlIGp1aWNlIHNvY2Nlcg==').decode('utf-8')

# QIWI
qiwi_login = base64.b64decode('Kzc5OTUxMjMwMzk1').decode('utf-8')
qiwi_token = base64.b64decode('YzY0ZDdlMGQwNmJiNjA2NDcyZGU5MzMwYzZhYzQ0NzQ=').decode('utf-8')

# Mainnet
node_url = sql('request', "SELECT url FROM nodes WHERE status='1'")
explorer_api_url = 'https://explorer-api.minter.network/api/v1'

# Testnet
test_node_url = 'https://api.testnet.minter.stakeholder.space'
test_explorer_api_url = 'https://explorer-api.testnet.minter.network/api/v1'
