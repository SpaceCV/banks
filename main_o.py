# -*- coding: utf-8 -*-
import datetime
from uuid import getnode as get_mac

import qrcode
import telebot

import const
import functions
import modules
import sqlhelper
from python_qiwi import *
from sql import sql

bot = telebot.TeleBot(const.token)
sql_base = sqlhelper.sqlbase(const.path)
qiwi_pay = Pay(phone=const.qiwi_login, token=const.qiwi_token)
wallet_info = WalletInfo(phone=const.qiwi_login, token=const.qiwi_token)

# Closed Beta Test
cbt = int(sql('request', "SELECT cbt FROM status"))
if get_mac() == 164926747529928:
    sql('update', "UPDATE status SET cbt='2'")

dt = datetime.datetime
now = datetime.datetime.now()
print('Бот запущен в %s %s' % (dt.date(now), dt.time(now)))


@bot.message_handler(commands=['start'])
def command_start(message):
    modules.Modules(message).cmd_start()


if __name__ == '__main__':
    modules.main()
