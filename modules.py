# -*- coding: utf-8 -*-
import datetime

import telebot
from telebot.types import *

import const
import functions
import sqlhelper
from python_qiwi import *
from sql import sql

bot = telebot.TeleBot(const.token)
sql_base = sqlhelper.sqlbase(const.path)
qiwi_pay = Pay(phone=const.qiwi_login, token=const.qiwi_token)
wallet_info = WalletInfo(phone=const.qiwi_login, token=const.qiwi_token)


def main():
    bot.delete_webhook()
    bot.polling(none_stop=True)


class Modules:
    def __init__(self, data_a):
        global tid, cid, ctype, mid, data, message, lang
        try:
            call = data_a
            mci = call.chat_instance
            cid = call.message.chat.id
            mid = call.message.message_id
            tid = call.from_user.id
            data = call.data
        except AttributeError:
            message = data_a
            tid = message.from_user.id
            cid = message.chat.id
            ctype = message.chat.type
        lang = functions.lang(tid)

    def cmd_start(self):
        cbt = functions.cbt(tid)
        if (ctype == 'private' or tid in const.admins) and cbt is True:
            mtext = message.text
            if len(mtext.split()) > 1:
                if mtext.split()[1]:
                    ref = mtext.split()[1].replace('ref', '')
                    tid_sql = sql('request', "SELECT tid FROM users WHERE tid='" + str(tid) + "'")
                    if tid_sql is None:
                        if str(ref) != str(tid):
                            tid_ref = sql('request', "SELECT * FROM refs WHERE tid='" + str(tid) + "'")
                            if tid_ref is None:
                                sql('update',
                                    "INSERT INTO refs (tid, from_ref) VALUES ('" + str(tid) + "', '" + ref + "')")
                            elif tid_ref is not None:
                                bot.send_message(cid, lang.ref1)
                        else:
                            bot.send_message(cid, lang.ref2)
                    else:
                        bot.send_message(cid, lang.ref3)

            tid_sql = sql('request', "SELECT tid FROM users WHERE tid='" + str(tid) + "'")
            if tid_sql is None:
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton(text='English', callback_data='english'),
                             InlineKeyboardButton(text='Русский', callback_data='russian'))
                bot.send_message(cid, 'Выберите язык / Choose language',
                                 reply_markup=keyboard)
            elif tid_sql is not None:
                Modules(self).start()

    def start(self):
        keyb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        keyb.add(*[KeyboardButton(text=name) for name in lang.main])

        curr = sql('request', "SELECT currency FROM users WHERE tid='" + str(tid) + "'")

        buy_rub = functions.truncate(functions.buy_price() * functions.usd_rate(curr))
        sell_rub = functions.truncate(functions.sell_price() * functions.usd_rate(curr))

        buy_price = functions.truncate(functions.buy_price(), 4)
        sell_price = functions.truncate(functions.sell_price(), 4)

        bot.send_message(cid, lang.start_cmd.format(buy_price, buy_rub, curr, sell_price, sell_rub, curr),
                         reply_markup=keyb,
                         parse_mode='markdown')
