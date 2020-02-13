# -*- coding: utf-8 -*-
import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

import const
import sqlhelper
from mintersdk.sdk.wallet import MinterWallet
import base64
import functions

bot = telebot.TeleBot(const.token)
sql_base = sqlhelper.sqlbase(const.path)

print('Бот запущен')


@bot.message_handler(commands=['start'])
def command_start(message):
    cid = message.chat.id
    tid = message.from_user.id

    tid_sql = sql_base.sqlrequest("SELECT tid FROM users WHERE tid='" + str(tid) + "'")
    if tid_sql is None:
        create = MinterWallet.create()
        address = create['address']
        mnemonic = create['mnemonic']
        mnstr = base64.urlsafe_b64encode(mnemonic.encode("utf-8"))
        mnstr = str(mnstr, "utf-8")

        create1 = MinterWallet.create()
        address1 = create1['address']
        mnemonic1 = create1['mnemonic']
        mnstr1 = base64.urlsafe_b64encode(mnemonic1.encode("utf-8"))
        mnstr1 = str(mnstr1, "utf-8")
        sql_base.sqlupdate(
            "INSERT INTO users (tid, addresses, mnemonics, pettiness) VALUES ('" + str(tid) + "', '" + str(address) + "', '" + str(
                mnstr) + "', '" + str(address1) + ',' + str(mnstr1) + "')")

    keyb = ReplyKeyboardMarkup(resize_keyboard=True)
    keyb.add('Главная', 'События')
    keyb.add('Оплатить', 'Ещё')

    bot.send_message(cid, 'Привет!',
                     reply_markup=keyb, parse_mode='markdown')


@bot.message_handler(commands=['help'])
def command_help(message):
    cid = message.chat.id
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='Что это?', callback_data='what_is'))

    bot.send_message(cid, 'Помощь', reply_markup=keyboard)


@bot.message_handler(commands=['admin'])
def command_admin(message):
    cid = message.chat.id
    bot.send_message(cid, 'Что будем делать?')


@bot.message_handler(content_types=["text"])
def text(message):
    cid = message.chat.id
    tid = message.from_user.id
    if message.text == 'Главная':
        mid = bot.send_message(cid, 'Загрузка').message_id
        all = sql_base.sqlrequest("SELECT addresses, pettiness FROM users WHERE tid='" + str(tid) + "'")
        addresses = all[0].split(',')
        pettiness = str(all[1]).split(',')[0]
        keyboard = InlineKeyboardMarkup(row_width=2)
        amount = 0
        for i in addresses:
            amount += functions.get_all_coins_in_bip(str(i))
            keyboard.add(InlineKeyboardButton(text=str(i), callback_data=str(i)))
        keyboard.add(InlineKeyboardButton(text='Мелочница', callback_data='pettiness'))
        amount += functions.get_all_coins_in_bip(pettiness)
        amount = round(amount, 4)
        keyboard.add(InlineKeyboardButton(text='Привязать другой кошелек', callback_data='add'))
        bot.edit_message_text('Твой баланс составляет ' + str(amount) + ' BIP \n'
                              'Чтобы узнать более подробно или произвести операцию - выбери кошелек', cid, mid,
                              reply_markup=keyboard)
    elif message.text == 'Оплатить':
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text='Переводы', callback_data='transfer'),
                     InlineKeyboardButton(text='Платежи', callback_data='pays'),
                     InlineKeyboardButton(text='Действия', callback_data='actions'))
        bot.send_message(cid, 'Что делаем?', reply_markup=keyboard)
    elif message.text == 'События':
        bot.send_message(cid, 'События')
    elif message.text == 'Ещё':
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(InlineKeyboardButton(text='Рюкзак', callback_data='bag'),
                     InlineKeyboardButton(text='Изменить данные', callback_data='edit_data'),
                     InlineKeyboardButton(text='Настройки', callback_data='settings'),
                     InlineKeyboardButton(text='Помощь', callback_data='help'))
        bot.send_message(cid, 'Здесь будет информация об аккаунте и настройки', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        cid = call.message.chat.id
        mid = call.message.message_id
        tid = call.from_user.id
        if call.data == 'settings':
            notifications = str(*sql_base.sqlrequest("SELECT notif FROM users WHERE tid='" + str(tid) + "'"))
            if notifications == 'False':
                ntext = 'Уведомления OFF'
            elif notifications == 'True':
                ntext = 'Уведомления ON'
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(InlineKeyboardButton(text='Курс валюты', callback_data='currency'),
                         InlineKeyboardButton(text='Язык', callback_data='lang'),
                         InlineKeyboardButton(text=ntext, callback_data='notifications'),
                         InlineKeyboardButton(text='ПИН-коды', callback_data='pins'))
            bot.edit_message_text('Настройки', cid, mid, reply_markup=keyboard)
        elif call.data == 'transfer':
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(InlineKeyboardButton(text='По адресу кошелька', callback_data='address'),
                         InlineKeyboardButton(text='Между счетами', callback_data='lang'),
                         InlineKeyboardButton(text='По никнейму Telegram', callback_data='telegram'))
            bot.edit_message_text('Что делаем?', cid, mid, reply_markup=keyboard)
        elif call.data == 'pays':
            bot.edit_message_text('Здесь будет оплата', cid, mid)
        elif call.data == 'actions':
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(InlineKeyboardButton(text='Создать чек', callback_data='address'))
            bot.edit_message_text('Выбери', cid, mid, reply_markup=keyboard)
        elif call.data == 'pins':
            addresses = str(*sql_base.sqlrequest("SELECT addresses FROM users WHERE tid='" + str(tid) + "'")).split(',')
            keyboard = InlineKeyboardMarkup(row_width=1)
            a = 0
            for i in addresses:
                keyboard.add(InlineKeyboardButton(text=str(i), callback_data='edit_pin' + str(a)))
                a += 1
            bot.edit_message_text('Выбери для чего сменить пин', cid, mid, reply_markup=keyboard)
        elif call.data == 'currency':
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(InlineKeyboardButton(text='Рубль', callback_data='ruble'))
            bot.edit_message_text('Выбери валюту', cid, mid, reply_markup=keyboard)
        elif call.data == 'lang':
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(InlineKeyboardButton(text='Русский', callback_data='russian'))
            bot.edit_message_text('Выбери язык', cid, mid, reply_markup=keyboard)
        elif call.data == 'notifications':
            notifications = str(*sql_base.sqlrequest("SELECT notif FROM users WHERE tid='" + str(tid) + "'"))
            if notifications == 'True':
                sql_base.sqlupdate("UPDATE users SET notif='False' WHERE tid='" + str(tid) + "'")
                ntext = 'Уведомления OFF'
            elif notifications == 'False':
                sql_base.sqlupdate("UPDATE users SET notif='True' WHERE tid='" + str(tid) + "'")
                ntext = 'Уведомления ON'
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(InlineKeyboardButton(text='Курс валюты', callback_data='currency'),
                         InlineKeyboardButton(text='Язык', callback_data='lang'),
                         InlineKeyboardButton(text=ntext, callback_data='notifications'))
            bot.edit_message_text('Настройки', cid, mid, reply_markup=keyboard)
        elif call.data == 'bag':
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(InlineKeyboardButton(text='Привязять ИНН', callback_data='edit_data'),
                         InlineKeyboardButton(text='Привязать права', callback_data='settings'),
                         InlineKeyboardButton(text='Привязять СТС', callback_data='edit_data'))
            bot.edit_message_text('Работает только для граждан РФ', cid, mid, reply_markup=keyboard)
        elif call.data == 'edit_pin':
            keyboard = InlineKeyboardMarkup(row_width=3)
            keyboard.add(InlineKeyboardButton(text='1', callback_data='1'),
                         InlineKeyboardButton(text='2', callback_data='2'),
                         InlineKeyboardButton(text='3', callback_data='3'),
                         InlineKeyboardButton(text='4', callback_data='4'),
                         InlineKeyboardButton(text='5', callback_data='5'),
                         InlineKeyboardButton(text='6', callback_data='6'),
                         InlineKeyboardButton(text='7', callback_data='7'),
                         InlineKeyboardButton(text='8', callback_data='8'),
                         InlineKeyboardButton(text='9', callback_data='9'),
                         InlineKeyboardButton(text='Отмена', callback_data='cancel'),
                         InlineKeyboardButton(text='0', callback_data='0'),
                         InlineKeyboardButton(text='Очистить', callback_data='clean'))
            bot.edit_message_text('Изменить пинкод', cid, mid, reply_markup=keyboard)
        elif len(call.data) == 42:
            print(call.data)
            addresses = str(*sql_base.sqlrequest("SELECT addresses FROM users WHERE tid='" +
                                                str(tid) + "'")).split(',')
            if call.data in addresses:
                keyboard = InlineKeyboardMarkup(row_width=3)
                keyboard.add(InlineKeyboardButton(text='Приоритетный кошелек', callback_data='foreground' + call.data),
                             InlineKeyboardButton(text='Операции', callback_data='operations' + call.data),
                             InlineKeyboardButton(text='История', callback_data='history' + call.data),
                             InlineKeyboardButton(text='Сменить пин', callback_data='edit_pin' + call.data),
                             InlineKeyboardButton(text='Ограничения', callback_data='limit' + call.data),
                             InlineKeyboardButton(text='Уведомления', callback_data='notifications' + call.data))
                bot.edit_message_text('Кошелек ' + call.data, cid, mid, reply_markup=keyboard)


if __name__ == '__main__':
    bot.delete_webhook()
    bot.polling(none_stop=True)
