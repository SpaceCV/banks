#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

import requests

from python_qiwi.errors import *


class Authorization(object):
    def __init__(self, token, phone):
        if isinstance(phone, str):
            self.phone = phone.replace('+', '')
            if self.phone.startswith('8'):
                self.phone = '7' + self.phone[1:]

        self._s = requests.Session()
        self._s.headers['Accept'] = 'application/json'
        self._s.headers['Content-Type'] = 'application/json'
        self._s.headers['Authorization'] = 'Bearer ' + token
        self.token = token


class WalletInfo(Authorization):
    def __str__(self):
        return 'QIWI Wallet: number={0}, token={1}'.format(self.phone, self.token)

    def list_balance(self):
        response = self._s.get('https://edge.qiwi.com/funding-sources/v2/persons/' + self.phone + '/accounts')

        if response is None:
            raise InvalidTokenError('Invalid token!')

        json = response.json()

        if ('errorCode' or 'code') in json:
            raise QIWIAPIError(json)

        balances = []

        for account in json['accounts']:
            if account['hasBalance']:
                balances.append({
                    'type': account['type'],
                    'balance': account['balance']
                })

        return balances

    def balance(self, currency=None):
        balances = self.list_balance()
        amount = 0

        for i in balances:
            bal = i['balance']
            if currency is not None:
                rate = self.get_rate(bal['currency'], currency)
                amount += bal['amount'] * rate
            amount += bal['amount']

        return amount

    def get_rate(self, From, To):
        response = self._s.get('https://edge.qiwi.com/sinap/crossRates')
        json = response.json()['result']

        for i in json:
            if str(From) == i['to'] and str(To) == i['from']:
                return i['rate']


class Pay(Authorization):
    def pay(self, account, oid, amount, currency='643', typem='Account', aid='643'):
        args = {'id': Utils.tid(),
                'sum': {
                    'amount': amount,
                    'currency': currency},
                'paymentMethod': {
                    'type': typem,
                    'accountId': aid},
                'fields': {
                    'account': account
                }}

        response = self._s.post('https://edge.qiwi.com/sinap/api/v2/terms/' + str(oid) + '/payments', json=args)
        data = response.json()

        if ('errorCode' or 'code') in data:
            raise QIWIAPIError(data)

        return response


class Utils:
    @staticmethod
    def tid():
        return str(int(time.time()) * 1000)

    @staticmethod
    def detect_mobile(phone):
        phone = str(phone)
        if 10 <= len(phone) <= 12:
            phone = phone.replace('+', '')

            if phone.startswith('8'):
                phone = phone.replace('8', '7')

            s = requests.Session()
            s.headers['Accept'] = 'application/json'
            s.headers['Content-Type'] = 'application/x-www-form-urlencoded'
            s = s.post(url='https://qiwi.com/mobile/detect.action', data={'phone': phone})
            data = s.json()

            if data.get('code', {}).get('value') == '0':
                return phone, data.get('message')
            else:
                return ArgumentError('Invalid phone number')
        else:
            raise ArgumentError('Invalid phone number')
