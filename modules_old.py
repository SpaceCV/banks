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


# Admin
def admin():
    users = sql('request', "SELECT COUNT(*) FROM users")
    bal_wal = functions.get_balance(functions.get_address(const.mnemonic))
    status_qiwi = int(sql('request', "SELECT qiwi FROM status"))
    cbt = int(sql('request', "SELECT cbt FROM status"))
    balance = wallet_info.list_balance()
    for i in balance:
        bl = i['balance']
        if bl['currency'] == 643:
            balrub = bl['amount']
        elif bl['currency'] == 398:
            balkzt = bl['amount']

    if status_qiwi == 0:
        qiwi = 'Выключен'
        kq = InlineKeyboardButton(text='Включить QIWI', callback_data='qiwi_on')
    elif status_qiwi == 1:
        qiwi = 'Включен'
        kq = InlineKeyboardButton(text='Выключить QIWI', callback_data='qiwi_off')

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton(text='Рассылка', callback_data='pass'),
                 InlineKeyboardButton(text='Статистика', callback_data='stats'),
                 InlineKeyboardButton(text='Изменить курс', callback_data='edit_rate'), kq)

    if cbt == 1:
        keyboard.add(InlineKeyboardButton(text='Перейти в А-тесты', callback_data='cbt'))
    elif cbt == 0:
        keyboard.add(InlineKeyboardButton(text='Перейти в Б-тесты', callback_data='cbt'))

    text = 'Админка:\n\n' \
           'Баланс QIWI RUB: {0} RUB\n' \
           'Баланс QIWI KZT: {1} KZT\n' \
           'Баланс кошелька: {2} BIP\n' \
           'Пользователей: {3}\n' \
           'Статус QIWI: {4}'.format(balrub, balkzt, bal_wal, users, qiwi)

    return text, keyboard


class Modules:
    def __init__(self, data_a):
        global tid, cid, ctype, mid, data, message
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

    def cu(self):
        cbt = functions.cbt(tid)
        if (ctype == 'private' or tid in const.admins) and cbt is True:
            lang = functions.lang(tid)

            keyb = InlineKeyboardMarkup()
            keyb.add(*[InlineKeyboardButton(text=name, callback_data='valut_' + name) for name in const.currency])

            bot.send_message(cid, lang.cu1, reply_markup=keyb)

    def command_start(self):
        cbt = functions.cbt(tid)
        lang = functions.lang(tid)
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

    def mx(call):
        lang = functions.lang(tid)
        keyboard = InlineKeyboardMarkup(row_width=2)
        addresses = str(*sql('request', "SELECT addresses FROM users WHERE tid='" + str(tid) + "'"))
        addresses = addresses.split(',')
        keb = [InlineKeyboardButton(text=lang.Mx2, callback_data='edit_pin' + data),
               InlineKeyboardButton(text=lang.back, callback_data='my'),
               InlineKeyboardButton(text=lang.Mx6, callback_data='name_' + data)]
        text = lang.Mx7
        if data != addresses[0]:
            text = lang.Mx1
            keb.insert(1, InlineKeyboardButton(text=lang.Mx3, callback_data='close' + data))
            keb.insert(3, InlineKeyboardButton(text=lang.Mx5, callback_data='choose_' + data))
        keyboard.add(*keb)
        bot.edit_message_text(text, cid, mid, parse_mode='markdown', reply_markup=keyboard)

    # Main Buttons
    def start(self):
        lang = functions.lang(tid)
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

    def cab_btn(self):
        cabs = Modules.cab(self)

        bot.send_message(cid, cabs[0], reply_markup=cabs[1], parse_mode='markdown', disable_web_page_preview=True)

    def history(message):
        cid = message.chat.id
        tid = message.from_user.id
        lang = functions.lang(tid)

        tr = sql_base.sqlrequestall(
            "SELECT * FROM history WHERE tid='" + str(tid) + "' AND status='done' ORDER by id DESC")
        keyboard = InlineKeyboardMarkup()

        if not history:
            bot.send_message(cid, lang.history4)
        elif history:
            for i in tr:
                dt = datetime.datetime.strptime(i[7], '%Y-%m-%d %H:%M:%S')
                keyboard.add(InlineKeyboardButton(text=str(dt.date()), callback_data='history' + str(i[0])),
                             InlineKeyboardButton(text=lang.history5, callback_data='history' + str(i[0])))
            bot.send_message(cid, lang.history6, parse_mode='markdown', reply_markup=keyboard)

    def pays(data, type):
        if type == 1:
            cid = data.chat.id
            tid = data.from_user.id
        else:
            cid = data.message.chat.id
            mid = data.message.message_id
            tid = data.from_user.id
        lang = functions.lang(tid)

        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(InlineKeyboardButton(text=lang.pays3, callback_data='pays'),
                     InlineKeyboardButton(text=lang.pays5, callback_data='transfer'))
        keyboard.add(InlineKeyboardButton(text=lang.pays1, callback_data='mobile'))
        bot.send_message(cid, lang.pays2, reply_markup=keyboard, parse_mode='markdown')

    def cab(self):
        user = sql('request', "SELECT * FROM users WHERE tid='" + str(tid) + "'")
        wallets = user[3]
        wallet_0 = sql('request', "SELECT * FROM wallets WHERE id='" + wallets[0] + "'")
        wal_spl = wallet_0[1].replace(wallet_0[1][5:37], '....')
        all_wallets = wallets.split(',')
        lang = functions.lang(tid)

        keyboard = InlineKeyboardMarkup(row_width=2)
        keb = [InlineKeyboardButton(text=lang.cab1, callback_data='deposit_' + wallet_0[1]),
               InlineKeyboardButton(text=lang.cab2, callback_data='pass'),
               InlineKeyboardButton(text=lang.cab3, callback_data='partners'),
               InlineKeyboardButton(text=lang.cab4, callback_data='my')]

        if len(all_wallets) < 3:
            keb.insert(3, InlineKeyboardButton(text=lang.cab5, callback_data='address_new'))

        keyboard.add(*keb)

        PARAMS = {'address': wallet_0[1]}
        r = requests.get(url=const.node_url + '/address', params=PARAMS)
        js = r.json()['result']['balance']

        coins = []
        for (k, v) in js.items():
            v = float(v) / 1000000000000000000
            amo = functions.truncate(v, 2)
            if amo == 0.00:
                amo = v
            if k == 'BIP':
                total = functions.truncate(
                    float(v) * functions.buy_price() * functions.usd_rate(user[4]))
            else:
                total = functions.truncate(
                    float(v) * functions.get_price(k) * functions.buy_price() * functions.usd_rate(user[4]))
            coin = lang.cab6.format(k, amo, total, user[4])
            if k == 'BIP':
                coins.insert(0, coin)
            else:
                coins.append(coin)

        text_coin = ''

        for i in coins:
            text_coin += i

        name = sql('request', "SELECT name FROM wallets WHERE address='" + str(wallet_0[1]) + "'")
        if name is not None:
            name = lang.cab7.format(wal_spl, wallet_0[0], name)
        elif name is None:
            name = lang.cab8.format(wal_spl, wallet_0[0])

        buy_rub = functions.truncate(functions.buy_price() * functions.usd_rate(user[5]))
        sell_rub = functions.truncate(functions.sell_price() * functions.usd_rate(user[5]))
        buy_price = functions.truncate(functions.buy_price(), 4)
        sell_price = functions.truncate(functions.sell_price(), 4)

        text = lang.cab9.format(buy_price, buy_rub, user[4], sell_price, sell_rub, user[4], name, text_coin)
        return text, keyboard

    def name_(call):
        cid = call.message.chat.id
        mid = call.message.message_id
        data = call.data
        msg = bot.edit_message_text('✏️ Введите название для счета', cid, mid)
        bot.register_next_step_handler(msg, name_wal, data[5:])

    def my(self):
        addresses = str(sql('request', "SELECT addresses FROM users WHERE tid='" + str(tid) + "'"))
        addresses = addresses.split(',')
        result = []
        keyboard = InlineKeyboardMarkup(row_width=2)
        abc = True
        for i in addresses:
            if addresses[0] == i:
                text = '☑️ '
            else:
                text = ''
            wall = sql('request', "SELECT * FROM wallets WHERE id='" + str(i) + "'")
            if wall[3] == 'None':
                name = wall[1].replace(wall[1][5:37], '....')
            else:
                name = wall[3]
            keb = InlineKeyboardButton(text=text + str(name), callback_data=i)
            result.append(keb)
            if len(addresses) >= 2 and abc == True:
                if addresses[1] == i:
                    bek = InlineKeyboardButton(text='Назад', callback_data='back_cabinet')
                    result.append(bek)
                    abc = False
            elif len(addresses) == 1 and abc == True:
                bek = InlineKeyboardButton(text='Назад', callback_data='back_cabinet')
                result.append(bek)
                abc = False

        keyboard.add(*result)

        bot.edit_message_text('💼 *Выберите счет*', cid, mid, parse_mode='markdown', reply_markup=keyboard)

    def send_coin(message, type):
        cid = message.chat.id
        tid = message.from_user.id
        if type == 'telegram':
            ff = message.forward_from
            if ff is not None:
                ftid = message.forward_from.id
                tidid = sql('request', "SELECT * FROM users WHERE tid='" + str(ftid) + "'")
                if tidid is not None:
                    bot.send_message(cid, 'Сколько перешлем?')
                elif tidid is None:
                    bot.send_message(cid, 'Этот пользователь не зарегистрирован. Но мы можем создать чек и он будет '
                                          'автоматически активирован, когда пользователь зарегистрируется. Согласны?')
            else:
                bot.send_message(cid, 'Я не могу принять это сообщение')
                start(cid, tid)
        elif type == 'minter':
            mtext = message.text
            if len(mtext) == 42:
                a_ll = sql('request',
                    "SELECT * FROM history WHERE tid='" + str(tid) + "' and type='" + type + "' ORDER BY id DESC")
                print(a_ll)
                curr = str(*sql_base.sqlrequest("SELECT currency FROM users WHERE tid='" + str(tid) + "'"))
                sql('update',
                    "UPDATE history SET coin='BIP', aid='" + str(mtext) + "' WHERE id='" + str(a_ll[0]) + "'")
                address = a_ll[2]
                addr_spl = address.replace(str(address)[5:37], '....')

                min_sum = functions.truncate(1 * functions.buy_price() * functions.usd_rate(curr))
                max_sum = functions.truncate(const.mobile * functions.buy_price() * functions.usd_rate(curr))

                wallet = sql('request', "SELECT * FROM wallets WHERE address='" + str(address) + "'")
                if wallet is not None:
                    name = '*Со счёта:* [%s](https://minterscan.net/address/%s) (%s)\n' % (addr_spl, address, wallet[2])
                elif wallet is None:
                    name = '*Со счёта:* [%s](https://minterscan.net/address/%s)\n' % (addr_spl, address)

                a = ['1', '2', '3', '4', '5', '6', '7', '8  ', '9']
                keyb = InlineKeyboardMarkup()
                keyb.add(InlineKeyboardButton(text='Оплата монетой: BIP', callback_data='snd_coin'))
                keyb.add(*[InlineKeyboardButton(text=name, callback_data='snd_' + name) for name in a])
                keyb.add(InlineKeyboardButton(text='Отмена', callback_data='snd_cancel'),
                         InlineKeyboardButton(text='0', callback_data='pass'),
                         InlineKeyboardButton(text='Очистить', callback_data='snd_clean'),
                         InlineKeyboardButton(text='Готово', callback_data='pass'))
                text = '💸 *Сумма отправки*\n\n' \
                       '*Мин. сумма:* 1 BIP (%s %s)\n' \
                       '*Макс. сумма:* %s BIP (%s %s)\n' \
                       '*Комиссия:* 0.01 BIP\n\n' \
                       '📲 *Отправка монет через Minter*\n\n' \
                       '%s' \
                       '*Адрес:* %s\n' \
                       '*Итого сумма:* 0 BIP (0 %s)\n\n' \
                       '*Ввод:* 0 BIP' % (min_sum, curr, const.mobile, max_sum, curr, name, mtext, curr)
                bot.send_message(cid, text, reply_markup=keyb, parse_mode='markdown')
            else:
                bot.send_message(cid, 'Я не могу принять это сообщение')
                start(cid, tid)

    def send(call):
        message = call.message
        cid = message.chat.id
        mid = message.message_id
        tid = call.from_user.id
        r = call.data[5:]
        sp = r.split('_')
        a = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
        if sp[0].isdigit():
            if len(sp) > 1:
                ab = sp[1]
            elif len(sp) == 1:
                ab = ''

            a_ll = sql_base.sqlrequest(
                "SELECT * FROM history WHERE tid='" + str(tid) + "' and type='minter' ORDER BY id DESC")
            curr = str(*sql_base.sqlrequest("SELECT currency FROM users WHERE tid='" + str(tid) + "'"))
            address = a_ll[2]
            coin = a_ll[8]
            phone = a_ll[4]
            amount = ab + sp[0]

            if coin is None:
                coin = 'BIP'
                sql_base.sqlupdate("UPDATE history SET coin='BIP' WHERE id='" + str(a_ll[0]) + "'")

            if coin != 'BIP':
                comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.11, 4)
                amount_in_coin = (float(amount) - float(comis)) / functions.get_price(coin)
            elif coin == 'BIP':
                comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.01, 4)
                amount_in_coin = float(amount) - float(comis)
            addr_spl = address.replace(str(address)[5:37], '....')

            amount_in_coin_tru = functions.truncate(amount_in_coin)

            min_sum = functions.truncate(const.min_mob * functions.buy_price() * functions.usd_rate(curr))
            max_sum = functions.truncate(const.mobile * functions.buy_price() * functions.usd_rate(curr))
            total = functions.truncate(
                (float(amount) - float(comis)) * functions.buy_price() * functions.usd_rate(curr))

            keyb = InlineKeyboardMarkup()
            keyb.add(InlineKeyboardButton(text='Оплата монетой: ' + coin, callback_data='snd_coin'))
            keyb.add(
                *[InlineKeyboardButton(text=name, callback_data=call.data[:4] + name + '_' + amount) for name in a])
            keyb.add(InlineKeyboardButton(text='Отмена', callback_data='snd_cancel'),
                     InlineKeyboardButton(text='0', callback_data=call.data[:4] + '0_' + amount),
                     InlineKeyboardButton(text='Очистить', callback_data='snd_clean'))
            keyb.add(InlineKeyboardButton(text='Готово', callback_data=call.data[:4] + 'ready_' + amount))

            sql_base.sqlupdate("UPDATE history SET sum='" +
                               str(float(amount)) + "', in_coin='" +
                               str(float(amount_in_coin)) + "' WHERE id='" + str(a_ll[0]) + "'")

            wallet = sql_base.sqlrequest("SELECT * FROM wallets WHERE address='" + str(address) + "'")
            if wallet is not None:
                name = '*Со счёта:* [%s](https://minterscan.net/address/%s) (%s)\n' % (addr_spl, address, wallet[2])
            elif wallet is None:
                name = '*Со счёта:* [%s](https://minterscan.net/address/%s)\n' % (addr_spl, address)

            bot.edit_message_text('💸 *Сумма пополнения*\n\n'
                                  '*Мин. сумма:* %s BIP (%s %s)\n'
                                  '*Макс. сумма:* %s BIP (%s %s)\n'
                                  '*Комиссия:* %s BIP\n\n'
                                  '📲 *Отправка монет через Minter*\n\n'
                                  '%s'
                                  '*Номер телефона:* %s\n'
                                  '*Итого сумма:* %s %s (%s %s)\n\n'
                                  '*Ввод:* %s BIP' % (const.min_mob, min_sum, curr, const.mobile, max_sum, curr, comis,
                                                      name, phone, amount_in_coin_tru, coin, total, curr, amount),
                                  cid, mid, reply_markup=keyb, parse_mode='markdown', disable_web_page_preview=True)
        elif sp[0] == 'cancel':
            bot.delete_message(cid, mid)
            start(cid, tid)
        elif sp[0] == 'coin':
            address = str(*sql_base.sqlrequest("SELECT wallet FROM history WHERE tid='"
                                               + str(tid) + "' and type='mobile' ORDER BY id DESC"))
            a_ll = sql_base.sqlrequest(
                "SELECT * FROM history WHERE tid='" + str(tid) + "' and type='mobile' ORDER BY id DESC")
            address = address.split(',')[0]
            PARAMS = {'address': address}
            r = requests.get(url=const.node_url + '/address', params=PARAMS)
            js = r.json()['result']['balance']
            coins = []
            kcoins = []

            for (k, v) in js.items():
                v = float(v) / 1000000000000000000
                amo = functions.truncate(v, 2)
                if amo == 0.00:
                    amo = v
                coin = '*%s* %s' % (k, amo)
                if k == a_ll[8]:
                    cho = '☑️ '
                else:
                    cho = ''
                if k == 'BIP':
                    kcoins.insert(0, [cho + k, k])
                else:
                    kcoins.append([cho + k, k])

                if k == 'BIP':
                    coin += '\n'
                    coins.insert(0, coin)
                else:
                    amincoin = functions.truncate(v * functions.get_price(k), 2)
                    coin += ' (%s BIP)\n' % amincoin
                    coins.append(coin)

            text_coin = ''

            keyb = InlineKeyboardMarkup(row_width=2)
            keyb.add(*[InlineKeyboardButton(text=a, callback_data='snd_chocoin_' + b) for (a, b) in kcoins])

            for i in coins:
                text_coin += i

            bot.edit_message_text(text_coin, cid, mid, reply_markup=keyb, parse_mode='markdown')
        elif sp[0] == 'chocoin':
            a_ll = sql_base.sqlrequest(
                "SELECT * FROM history WHERE tid='" + str(tid) + "' and type='mobile' ORDER BY id DESC")

            curr = str(*sql_base.sqlrequest("SELECT currency FROM users WHERE tid='" + str(tid) + "'"))
            address = a_ll[2]
            coin = sp[1]
            phone = a_ll[4]
            addr_spl = address.replace(str(address)[5:37], '....')

            sum = a_ll[5]
            if sum is None:
                sum = 0
                cb = 'pass'
            else:
                cb = call.data[:4] + '_0_' + str(sum)

            amount = sum

            if coin != 'BIP':
                comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.11, 4)
                amount_in_coin = (float(amount) - float(comis)) / functions.get_price(coin)
            elif coin == 'BIP':
                comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.01, 4)
                amount_in_coin = float(amount) - float(comis)

            sql_base.sqlupdate("UPDATE history SET coin='" + str(sp[1]) + "', in_coin='" +
                               str(amount_in_coin) + "' WHERE id='" + str(a_ll[0]) + "'")

            min_sum = functions.truncate(const.min_mob * functions.buy_price() * functions.usd_rate(curr))
            max_sum = functions.truncate(const.mobile * functions.buy_price() * functions.usd_rate(curr))
            total = functions.truncate(
                (float(amount) - float(comis)) * functions.buy_price() * functions.usd_rate(curr))

            if sum == 0:
                itogo = '0 %s (0 %s)' % (coin, curr)
            else:
                amo = functions.truncate(amount_in_coin, 2)
                if amo == 0.00:
                    amo = amount_in_coin
                itogo = '%s %s (%s %s)' % (amo, coin, total, curr)

            keyb = InlineKeyboardMarkup()
            keyb.add(InlineKeyboardButton(text='Оплата монетой: ' + coin, callback_data='snd_coin'))
            keyb.add(*[InlineKeyboardButton(text=name, callback_data='snd_' + name) for name in a])
            keyb.add(InlineKeyboardButton(text='Отмена', callback_data='snd_cancel'),
                     InlineKeyboardButton(text='0', callback_data=cb),
                     InlineKeyboardButton(text='Очистить', callback_data='snd_clean'))
            if sum != 0 and sum != '0':
                keyb.add(InlineKeyboardButton(text='Готово', callback_data=call.data[:4] + 'ready_' + str(sum)))
            else:
                keyb.add(InlineKeyboardButton(text='Готово', callback_data='pass'))

            wallet = sql_base.sqlrequest("SELECT * FROM wallets WHERE address='" + str(address) + "'")
            if wallet is not None:
                name = '*Со счёта:* [%s](https://minterscan.net/address/%s) (%s)\n' % (addr_spl, address, wallet[2])
            elif wallet is None:
                name = '*Со счёта:* [%s](https://minterscan.net/address/%s)\n' % (addr_spl, address)

            bot.edit_message_text('💸 *Сумма пополнения*\n\n'
                                  '*Мин. сумма:* %s BIP (%s %s)\n'
                                  '*Макс. сумма:* %s BIP (%s %s)\n'
                                  '*Комиссия:* %s BIP\n\n'
                                  '📲 *Отправка монет через Minter*\n\n'
                                  '%s'
                                  '*Номер телефона:* %s\n'
                                  '*Итого сумма:* %s\n\n'
                                  '*Ввод:* %s BIP' % (const.min_mob, min_sum, curr, const.mobile, max_sum, curr, comis,
                                                      name, phone, itogo, sum),
                                  cid, mid, reply_markup=keyb, parse_mode='markdown', disable_web_page_preview=True)
        elif sp[0] == 'clean':
            try:
                a_ll = sql_base.sqlrequest(
                    "SELECT * FROM history WHERE tid='" + str(tid) + "' and type='mobile' ORDER BY id DESC")
                curr = str(*sql_base.sqlrequest("SELECT currency FROM users WHERE tid='" + str(tid) + "'"))
                address = a_ll[2]
                phone = a_ll[4]
                coin = a_ll[8]
                addr_spl = address.replace(str(address)[5:37], '....')
                sql_base.sqlupdate("UPDATE history SET sum='0' WHERE id='" + str(a_ll[0]) + "'")

                if coin != 'BIP':
                    comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.11, 4)
                elif coin == 'BIP':
                    comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.01, 4)
                min_sum = functions.truncate(const.min_mob * functions.buy_price() * functions.usd_rate(curr))
                max_sum = functions.truncate(const.mobile * functions.buy_price() * functions.usd_rate(curr))

                keyb = InlineKeyboardMarkup()
                keyb.add(InlineKeyboardButton(text='Оплата монетой: ' + coin, callback_data='snd_coin'))
                keyb.add(*[InlineKeyboardButton(text=name, callback_data='snd_' + name) for name in a])
                keyb.add(InlineKeyboardButton(text='Отмена', callback_data='snd_cancel'),
                         InlineKeyboardButton(text='0', callback_data='pass'),
                         InlineKeyboardButton(text='Очистить', callback_data='snd_clean'),
                         InlineKeyboardButton(text='Готово', callback_data='pass'))

                wallet = sql_base.sqlrequest("SELECT * FROM wallets WHERE address='" + str(address) + "'")
                if wallet is not None:
                    name = '*Со счёта:* [%s](https://minterscan.net/address/%s) (%s)\n' % (addr_spl, address, wallet[2])
                elif wallet is None:
                    name = '*Со счёта:* [%s](https://minterscan.net/address/%s)\n' % (addr_spl, address)

                bot.edit_message_text('💸 *Сумма пополнения*\n\n'
                                      '*Мин. сумма:* %s BIP (%s %s)\n'
                                      '*Макс. сумма:* %s BIP (%s %s)\n'
                                      '*Комиссия:* %s %s\n\n'
                                      '📲 *Отправка монет через Minter*\n\n'
                                      '%s'
                                      '*Номер телефона:* %s\n'
                                      '*Итого сумма:* 0 %s (0 %s)\n\n'
                                      '*Ввод:* 0 BIP' % (
                                      const.min_mob, min_sum, curr, const.mobile, max_sum, curr, comis,
                                      coin, name, phone, coin, curr),
                                      cid, mid, reply_markup=keyb, parse_mode='markdown', disable_web_page_preview=True)
            except telebot.apihelper.ApiException:
                bot.answer_callback_query(call.id, 'Очищено', show_alert=True)
        elif sp[0] == 'ready':
            a_ll = sql_base.sqlrequest(
                "SELECT * FROM history WHERE tid='" + str(tid) + "' and type='mobile' ORDER BY id DESC")
            curr = str(*sql_base.sqlrequest("SELECT currency FROM users WHERE tid='" + str(tid) + "'"))
            address = a_ll[2]
            phone = a_ll[4]
            coin = a_ll[8]
            summ_in_bip = a_ll[5]
            PARAMS = {'address': a_ll[2]}
            r = requests.get(url=const.node_url + '/address', params=PARAMS)
            js = r.json()['result']['balance']
            for (k, v) in js.items():
                v = float(v) / 1000000000000000000
                if k == a_ll[8]:
                    amount = v
                    if const.mobile < float(a_ll[5]) or const.min_mob > float(a_ll[5]):
                        bot.answer_callback_query(call.id, '⚠️ Сумма платежа выходит за пределы лимитов',
                                                  show_alert=True)
                        if coin is None:
                            coin = 'BIP'
                        addr_spl = address.replace(str(address)[5:37], '....')
                        sql_base.sqlupdate("UPDATE history SET sum='0', in_coin='0' WHERE id='" + str(a_ll[0]) + "'")

                        min_sum = functions.truncate(const.min_mob * functions.buy_price() * functions.usd_rate(curr))
                        max_sum = functions.truncate(const.mobile * functions.buy_price() * functions.usd_rate(curr))

                        if coin != 'BIP':
                            comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.11, 4)
                        elif coin == 'BIP':
                            comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.01, 4)

                        keyb = InlineKeyboardMarkup()
                        keyb.add(InlineKeyboardButton(text='Оплата монетой: ' + coin, callback_data='snd_coin'))
                        keyb.add(*[InlineKeyboardButton(text=name, callback_data='snd_' + name) for name in a])
                        keyb.add(InlineKeyboardButton(text='Отмена', callback_data='snd_cancel'),
                                 InlineKeyboardButton(text='0', callback_data='pass'),
                                 InlineKeyboardButton(text='Очистить', callback_data='snd_clean'),
                                 InlineKeyboardButton(text='Готово', callback_data='pass'))

                        wallet = sql_base.sqlrequest("SELECT * FROM wallets WHERE address='" + str(address) + "'")
                        if wallet is not None:
                            name = '*Со счёта:* [%s](https://minterscan.net/address/%s) (%s)\n' % (
                                addr_spl, address, wallet[2])
                        elif wallet is None:
                            name = '*Со счёта:* [%s](https://minterscan.net/address/%s)\n' % (addr_spl, address)

                        bot.edit_message_text('💸 *Сумма пополнения*\n\n'
                                              '*Мин. сумма:* %s BIP (%s %s)\n'
                                              '*Макс. сумма:* %s BIP (%s %s)\n'
                                              '*Комиссия:* %s %s\n\n'
                                              '📲 *Отправка монет через Minter*\n\n'
                                              '%s'
                                              '*Номер телефона:* %s\n'
                                              '*Итого сумма:* 0 %s (0 %s)\n\n'
                                              '*Ввод:* 0 BIP' % (const.min_mob, min_sum, curr, const.mobile, max_sum,
                                                                 curr, comis, coin, name, phone, coin, curr),
                                              cid, mid, reply_markup=keyb, parse_mode='markdown',
                                              disable_web_page_preview=True)
                    elif float(amount) < float(a_ll[9]):
                        amo = float(a_ll[9]) - float(amount)
                        bot.answer_callback_query(call.id, 'На вашем счете недостаточно %s %s' % (amo, k),
                                                  show_alert=True)
                        if coin is None:
                            coin = 'BIP'
                        addr_spl = address.replace(str(address)[5:37], '....')
                        sql_base.sqlupdate("UPDATE history SET sum='0', in_coin='0' WHERE id='" + str(a_ll[0]) + "'")

                        min_sum = functions.truncate(const.min_mob * functions.buy_price() * functions.usd_rate(curr))
                        max_sum = functions.truncate(const.mobile * functions.buy_price() * functions.usd_rate(curr))

                        if coin != 'BIP':
                            comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.11, 4)
                        elif coin == 'BIP':
                            comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.01, 4)

                        keyb = InlineKeyboardMarkup()
                        keyb.add(InlineKeyboardButton(text='Оплата монетой: ' + coin, callback_data='snd_coin'))
                        keyb.add(*[InlineKeyboardButton(text=name, callback_data='snd_' + name) for name in a])
                        keyb.add(InlineKeyboardButton(text='Отмена', callback_data='snd_cancel'),
                                 InlineKeyboardButton(text='0', callback_data='pass'),
                                 InlineKeyboardButton(text='Очистить', callback_data='snd_clean'),
                                 InlineKeyboardButton(text='Готово', callback_data='pass'))

                        wallet = sql_base.sqlrequest("SELECT * FROM wallets WHERE address='" + str(address) + "'")
                        if wallet is not None:
                            name = '*Со счёта:* [%s](https://minterscan.net/address/%s) (%s)\n' % (
                                addr_spl, address, wallet[2])
                        elif wallet is None:
                            name = '*Со счёта:* [%s](https://minterscan.net/address/%s)\n' % (addr_spl, address)

                        bot.edit_message_text('💸 *Сумма пополнения*\n\n'
                                              '*Мин. сумма:* %s BIP (%s %s)\n'
                                              '*Макс. сумма:* %s BIP (%s %s)\n'
                                              '*Комиссия:* %s %s\n\n'
                                              '📲 *Отправка монет через Minter*\n\n'
                                              '%s'
                                              '*Номер телефона:* %s\n'
                                              '*Итого сумма:* 0 %s (0 %s)\n\n'
                                              '*Ввод:* 0 BIP' % (const.min_mob, min_sum, curr, const.mobile, max_sum,
                                                                 curr, comis, curr, name, phone, coin, curr),
                                              cid, mid, reply_markup=keyb, parse_mode='markdown',
                                              disable_web_page_preview=True)
                    elif (const.min_mob <= int(sp[1]) <= const.mobile) and float(amount) >= float(a_ll[9]):
                        summ_in_bip = float(summ_in_bip)
                        if coin == 'BIP':
                            comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.01, 4)
                            in_coin = str(summ_in_bip - comis)
                            in_curr = str(functions.buy_price() * (summ_in_bip - comis) * functions.usd_rate(curr))
                        else:
                            comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.11, 4)
                            in_coin = str((summ_in_bip - comis) / functions.get_price(coin))
                            in_curr = str(functions.buy_price() * (summ_in_bip - comis) * functions.usd_rate(curr))
                        sql_base.sqlupdate("UPDATE history SET in_curr='" +
                                           in_curr + "', in_coin='" + in_coin + "', curr='"
                                           + curr + "' WHERE id='" + str(a_ll[0]) + "'")
                        return sp[1]

    def a_(tid, cid, mid, address):
        a_ll = sql('request',
            "SELECT * FROM history WHERE tid='" + str(tid) +
            "' and type='mobile' ORDER BY id DESC")
        aid = sql('request',
            "SELECT aid FROM history WHERE tid='" + str(tid) +
            "' and type='mobile' and aid IS NOT NULL ORDER BY id DESC")
        sql('update',
            "UPDATE history SET wallet='" + address + "' WHERE id='" + str(a_ll[0]) + "'")
        if aid is not None:
            keyb = InlineKeyboardMarkup()
            keyb.add(InlineKeyboardButton(text=str(*aid), callback_data='phone' + str(*aid)))
            keyb.add(InlineKeyboardButton(text='Ввести номер телефона', callback_data='input'))
            bot.edit_message_text('📱 *Выберите номер телефона или введите новый*', cid, mid,
                                  parse_mode='markdown', reply_markup=keyb)
        elif aid is None:
            msg = bot.edit_message_text('📱 *Номер телефона*\n\n'
                                        '*Доступно:* Россия, Казахстан\n'
                                        '*Формат:* +79991234567', cid, mid, parse_mode='markdown')
            bot.register_next_step_handler(msg, number)

    def number(message):
        cid = message.chat.id
        mtext = message.text
        tid = message.from_user.id

        if mtext == 'Кабинет':
            modules.cabinet(message)
        elif mtext == 'Платежи':
            pays(message)
        elif mtext == 'История':
            history(message)
        else:
            try:
                phone = Utils.detect_mobile(mtext)[0]
                ks = keyboard_start(tid, phone)

                bot.send_message(cid, ks[0], reply_markup=ks[1], parse_mode='markdown', disable_web_page_preview=True)
            except python_qiwi.errors.ArgumentError:
                if (mtext == 11 or mtext == 12) and (
                mtext.startswith('+'), mtext.startswith('7'), mtext.startswith('8')):
                    msg = bot.send_message(cid, 'Введенный номер не верен')
                    bot.register_next_step_handler(msg, number)
                elif mtext == 11 or mtext == 12:
                    msg = bot.send_message(cid, 'Возможно мы не поддерживаем этот номер, но вы можете помочь нам. '
                                                'Добавьтесь в этот чат и мы попробуем подключить ваш номер. '
                                                'https://t.me/joinchat/BqUygxQFE7MexVzRxZ5j2g')
                    bot.register_next_step_handler(msg, number)
                else:
                    msg = bot.send_message(cid, 'Введенный номер не верен')
                    bot.register_next_step_handler(msg, number)

    def keyboard_start(tid, phone, coin='BIP'):
        a_ll = sql('request',
            "SELECT * FROM history WHERE tid='" + str(tid) + "' and type='mobile' ORDER BY id DESC")
        curr = str(*sql_base.sqlrequest("SELECT currency FROM users WHERE tid='" + str(tid) + "'"))
        sql('update', "UPDATE history SET coin='BIP', aid='" + str(phone) + "' WHERE id='" + str(a_ll[0]) + "'")
        address = a_ll[2]
        addr_spl = address.replace(str(address)[5:37], '....')

        min_sum = functions.truncate(const.min_mob * functions.buy_price() * functions.usd_rate(curr))
        max_sum = functions.truncate(const.mobile * functions.buy_price() * functions.usd_rate(curr))
        coms = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.01, 4)

        wallet = sql('request',"SELECT * FROM wallets WHERE address='" + str(address) + "'")
        if wallet is not None:
            name = '*Со счёта:* [%s](https://minterscan.net/address/%s) (%s)\n' % (addr_spl, address, wallet[2])
        elif wallet is None:
            name = '*Со счёта:* [%s](https://minterscan.net/address/%s)\n' % (addr_spl, address)

        a = ['1', '2', '3', '4', '5', '6', '7', '8  ', '9']
        keyb = InlineKeyboardMarkup()
        keyb.add(InlineKeyboardButton(text='Оплата монетой: ' + coin, callback_data='summ_coin'))
        keyb.add(*[InlineKeyboardButton(text=name, callback_data='summ_' + name) for name in a])
        keyb.add(InlineKeyboardButton(text='Отмена', callback_data='summ_cancel'),
                 InlineKeyboardButton(text='0', callback_data='pass'),
                 InlineKeyboardButton(text='Очистить', callback_data='summ_clean'),
                 InlineKeyboardButton(text='Готово', callback_data='pass'))
        text = '💸 *Сумма пополнения*\n\n' \
               '*Мин. сумма:* %s BIP (%s %s)\n' \
               '*Макс. сумма:* %s BIP (%s %s)\n' \
               '*Комиссия:* %s BIP\n\n' \
               '📲 *Пополнение телефона*\n\n' \
               '%s' \
               '*Номер телефона:* %s\n' \
               '*Итого сумма:* 0 %s (0 %s)\n\n' \
               '*Ввод:* 0 BIP' % (
               const.min_mob, min_sum, curr, const.mobile, max_sum, curr, coms, name, phone, coin, curr)
        return text, keyb

    def name_wal(message, address):
        mtext = message.text
        cid = message.chat.id
        tid = message.from_user.id
        wallet = sql('request', "SELECT * FROM wallets WHERE address='" + str(address) + "'")

        if wallet is not None:
            sql('update', "UPDATE wallets SET name='" + str(mtext) + "' WHERE address='" + str(address) + "'")
        elif wallet is None:
            sql('update',
                "INSERT INTO wallets (address, name) VALUES ('" + str(address) + "', '" + str(mtext) + "')")
        bot.send_message(cid, '✅ Название присвоено!')
        start(cid, tid)

    def pin(call):
        message = call.message
        cid = message.chat.id
        mid = message.message_id
        tid = message.from_user.id
        r = call.data[4:]
        sp = r.split('_')
        if sp[0].isdigit():
            sp_ = s_p(sp)
            pin = sp_[0]
            ab = sp_[1]

            if pin == '●●●●':
                create = MinterWallet.create()
                address = create['address']
                mnemonic = create['mnemonic']
                password = str(sp[1] + sp[0]).encode('utf-8')
                encrypted = functions.encrypt(password, mnemonic.encode('utf-8')).decode('utf-8')
                return 1, address, encrypted
            else:
                a = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
                keyb = InlineKeyboardMarkup()
                keyb.add(
                    *[InlineKeyboardButton(text=name, callback_data='pin_' + name + '_' + ab + sp[0]) for name
                      in a])
                keyb.add(InlineKeyboardButton(text='0', callback_data='pin_0_' + ab + sp[0]),
                         InlineKeyboardButton(text='Очистить', callback_data='pin_clean'))
                bot.edit_message_text('🔐 *Установите PIN-код для вашего счета*\n\n'
                                      '*PIN:* ' + pin, cid, mid, parse_mode='markdown', reply_markup=keyb)
        elif sp[0] == 'clean':
            try:
                a = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
                keyb = InlineKeyboardMarkup()
                keyb.add(*[InlineKeyboardButton(text=name, callback_data='pin_' + name) for name in a])
                keyb.add(InlineKeyboardButton(text='0', callback_data='pin_0'),
                         InlineKeyboardButton(text='Очистить', callback_data='pin_clean'))
                bot.edit_message_text('🔐 *Установите PIN-код для вашего счета*\n\n'
                                      '*PIN:* ○○○○', cid, mid, reply_markup=keyb, parse_mode='markdown')
            except telebot.apihelper.ApiException:
                bot.answer_callback_query(call.id, 'Очищено', show_alert=True)

    def pin_new(call):
        message = call.message
        cid = message.chat.id
        mid = message.message_id
        tid = call.from_user.id
        r = call.data[4:]
        sp = r.split('_')
        if sp[0].isdigit():
            sp_ = s_p(sp)
            pin = sp_[0]
            ab = sp_[1]

            if pin == '●●●●':
                create = MinterWallet.create()
                address = create['address']
                mnemonic = create['mnemonic']
                password = str(sp[1] + sp[0]).encode('utf-8')
                encrypted = functions.encrypt(password, mnemonic.encode('utf-8')).decode('utf-8')
                return 1, address, encrypted
            else:
                a = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
                keyb = InlineKeyboardMarkup()
                keyb.add(
                    *[InlineKeyboardButton(text=name, callback_data='new_' + name + '_' + ab + sp[0]) for name
                      in a])
                keyb.add(InlineKeyboardButton(text='Отмена', callback_data='new_cancel'),
                         InlineKeyboardButton(text='0', callback_data='new_0_' + ab + sp[0]),
                         InlineKeyboardButton(text='Очистить', callback_data='new_clean'))
                bot.edit_message_text('🔐 *Установите PIN-код для вашего счета*\n\n'
                                      '*PIN:* ' + pin, cid, mid, parse_mode='markdown', reply_markup=keyb)
        elif sp[0] == 'cancel':
            bot.delete_message(cid, mid)
            start(cid, tid)
        elif sp[0] == 'clean':
            try:
                a = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
                keyb = InlineKeyboardMarkup()
                keyb.add(*[InlineKeyboardButton(text=name, callback_data='new_' + name) for name in a])
                keyb.add(InlineKeyboardButton(text='Отмена', callback_data='new_cancel'),
                         InlineKeyboardButton(text='0', callback_data='new_0'),
                         InlineKeyboardButton(text='Очистить', callback_data='new_clean'))
                bot.edit_message_text('🔐 *Установите PIN-код для вашего счета*\n\n'
                                      '*PIN:* ○○○○', cid, mid, reply_markup=keyb, parse_mode='markdown')
            except telebot.apihelper.ApiException:
                bot.answer_callback_query(call.id, 'Очищено', show_alert=True)

    def KeyBoard(call):
        message = call.message
        cid = message.chat.id
        mid = message.message_id
        tid = call.from_user.id
        r = call.data[5:]
        sp = r.split('_')
        a = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
        if sp[0].isdigit():
            if len(sp) > 1:
                ab = sp[1]
            elif len(sp) == 1:
                ab = ''

            a_ll = sql_base.sqlrequest(
                "SELECT * FROM history WHERE tid='" + str(tid) + "' and type='mobile' ORDER BY id DESC")
            curr = str(*sql_base.sqlrequest("SELECT currency FROM users WHERE tid='" + str(tid) + "'"))
            address = a_ll[2]
            coin = a_ll[8]
            phone = a_ll[4]
            amount = ab + sp[0]

            if coin is None:
                coin = 'BIP'
                sql_base.sqlupdate("UPDATE history SET coin='BIP' WHERE id='" + str(a_ll[0]) + "'")

            if coin != 'BIP':
                comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.11, 4)
                amount_in_coin = (float(amount) - float(comis)) / functions.get_price(coin)
            elif coin == 'BIP':
                comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.01, 4)
                amount_in_coin = float(amount) - float(comis)
            addr_spl = address.replace(str(address)[5:37], '....')

            amount_in_coin_tru = functions.truncate(amount_in_coin)

            min_sum = functions.truncate(const.min_mob * functions.buy_price() * functions.usd_rate(curr))
            max_sum = functions.truncate(const.mobile * functions.buy_price() * functions.usd_rate(curr))
            total = functions.truncate(
                (float(amount) - float(comis)) * functions.buy_price() * functions.usd_rate(curr))

            keyb = InlineKeyboardMarkup()
            keyb.add(InlineKeyboardButton(text='Оплата монетой: ' + coin, callback_data='summ_coin'))
            keyb.add(
                *[InlineKeyboardButton(text=name, callback_data=call.data[:4] + '_' + name + '_' + amount) for name in
                  a])
            keyb.add(InlineKeyboardButton(text='Отмена', callback_data='summ_cancel'),
                     InlineKeyboardButton(text='0', callback_data=call.data[:4] + '_0_' + amount),
                     InlineKeyboardButton(text='Очистить', callback_data='summ_clean'))
            keyb.add(InlineKeyboardButton(text='Готово', callback_data=call.data[:4] + '_ready_' + amount))

            sql_base.sqlupdate("UPDATE history SET sum='" +
                               str(float(amount)) + "', in_coin='" +
                               str(float(amount_in_coin)) + "' WHERE id='" + str(a_ll[0]) + "'")

            wallet = sql_base.sqlrequest("SELECT * FROM wallets WHERE address='" + str(address) + "'")
            if wallet is not None:
                name = '*Со счёта:* [%s](https://minterscan.net/address/%s) (%s)\n' % (addr_spl, address, wallet[2])
            elif wallet is None:
                name = '*Со счёта:* [%s](https://minterscan.net/address/%s)\n' % (addr_spl, address)

            bot.edit_message_text('💸 *Сумма пополнения*\n\n'
                                  '*Мин. сумма:* %s BIP (%s %s)\n'
                                  '*Макс. сумма:* %s BIP (%s %s)\n'
                                  '*Комиссия:* %s BIP\n\n'
                                  '📲 *Пополнение телефона*\n\n'
                                  '%s'
                                  '*Номер телефона:* %s\n'
                                  '*Итого сумма:* %s %s (%s %s)\n\n'
                                  '*Ввод:* %s BIP' % (const.min_mob, min_sum, curr, const.mobile, max_sum, curr, comis,
                                                      name, phone, amount_in_coin_tru, coin, total, curr, amount),
                                  cid, mid, reply_markup=keyb, parse_mode='markdown', disable_web_page_preview=True)
        elif sp[0] == 'cancel':
            bot.delete_message(cid, mid)
            start(cid, tid)
        elif sp[0] == 'coin':
            address = str(*sql_base.sqlrequest("SELECT wallet FROM history WHERE tid='"
                                               + str(tid) + "' and type='mobile' ORDER BY id DESC"))
            a_ll = sql_base.sqlrequest(
                "SELECT * FROM history WHERE tid='" + str(tid) + "' and type='mobile' ORDER BY id DESC")
            address = address.split(',')[0]
            PARAMS = {'address': address}
            r = requests.get(url=const.node_url + '/address', params=PARAMS)
            js = r.json()['result']['balance']
            coins = []
            kcoins = []

            for (k, v) in js.items():
                v = float(v) / 1000000000000000000
                amo = functions.truncate(v, 2)
                if amo == 0.00:
                    amo = v
                coin = '*%s* %s' % (k, amo)
                if k == a_ll[8]:
                    cho = '☑️ '
                else:
                    cho = ''
                if k == 'BIP':
                    kcoins.insert(0, [cho + k, k])
                else:
                    kcoins.append([cho + k, k])

                if k == 'BIP':
                    coin += '\n'
                    coins.insert(0, coin)
                else:
                    amincoin = functions.truncate(v * functions.get_price(k), 2)
                    coin += ' (%s BIP)\n' % amincoin
                    coins.append(coin)

            text_coin = ''

            keyb = InlineKeyboardMarkup(row_width=2)
            keyb.add(*[InlineKeyboardButton(text=a, callback_data='summ_chocoin_' + b) for (a, b) in kcoins])

            for i in coins:
                text_coin += i

            bot.edit_message_text(text_coin, cid, mid, reply_markup=keyb, parse_mode='markdown')
        elif sp[0] == 'chocoin':
            a_ll = sql_base.sqlrequest(
                "SELECT * FROM history WHERE tid='" + str(tid) + "' and type='mobile' ORDER BY id DESC")

            curr = str(*sql_base.sqlrequest("SELECT currency FROM users WHERE tid='" + str(tid) + "'"))
            address = a_ll[2]
            coin = sp[1]
            phone = a_ll[4]
            addr_spl = address.replace(str(address)[5:37], '....')

            sum = a_ll[5]
            if sum is None:
                sum = 0
                cb = 'pass'
            else:
                cb = call.data[:4] + '_0_' + str(sum)

            amount = sum

            if coin != 'BIP':
                comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.11, 4)
                amount_in_coin = (float(amount) - float(comis)) / functions.get_price(coin)
            elif coin == 'BIP':
                comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.01, 4)
                amount_in_coin = float(amount) - float(comis)

            sql_base.sqlupdate("UPDATE history SET coin='" + str(sp[1]) + "', in_coin='" +
                               str(amount_in_coin) + "' WHERE id='" + str(a_ll[0]) + "'")

            min_sum = functions.truncate(const.min_mob * functions.buy_price() * functions.usd_rate(curr))
            max_sum = functions.truncate(const.mobile * functions.buy_price() * functions.usd_rate(curr))
            total = functions.truncate(
                (float(amount) - float(comis)) * functions.buy_price() * functions.usd_rate(curr))

            if sum == 0:
                itogo = '0 %s (0 %s)' % (coin, curr)
            else:
                amo = functions.truncate(amount_in_coin, 2)
                if amo == 0.00:
                    amo = amount_in_coin
                itogo = '%s %s (%s %s)' % (amo, coin, total, curr)

            keyb = InlineKeyboardMarkup()
            keyb.add(InlineKeyboardButton(text='Оплата монетой: ' + coin, callback_data='summ_coin'))
            keyb.add(*[InlineKeyboardButton(text=name, callback_data='summ_' + name) for name in a])
            keyb.add(InlineKeyboardButton(text='Отмена', callback_data='summ_cancel'),
                     InlineKeyboardButton(text='0', callback_data=cb),
                     InlineKeyboardButton(text='Очистить', callback_data='summ_clean'))
            if sum != 0 and sum != '0':
                keyb.add(InlineKeyboardButton(text='Готово', callback_data=call.data[:4] + '_ready_' + str(sum)))
            else:
                keyb.add(InlineKeyboardButton(text='Готово', callback_data='pass'))

            wallet = sql_base.sqlrequest("SELECT * FROM wallets WHERE address='" + str(address) + "'")
            if wallet is not None:
                name = '*Со счёта:* [%s](https://minterscan.net/address/%s) (%s)\n' % (addr_spl, address, wallet[2])
            elif wallet is None:
                name = '*Со счёта:* [%s](https://minterscan.net/address/%s)\n' % (addr_spl, address)

            bot.edit_message_text('💸 *Сумма пополнения*\n\n'
                                  '*Мин. сумма:* %s BIP (%s %s)\n'
                                  '*Макс. сумма:* %s BIP (%s %s)\n'
                                  '*Комиссия:* %s BIP\n\n'
                                  '📲 *Пополнение телефона*\n\n'
                                  '%s'
                                  '*Номер телефона:* %s\n'
                                  '*Итого сумма:* %s\n\n'
                                  '*Ввод:* %s BIP' % (const.min_mob, min_sum, curr, const.mobile, max_sum, curr, comis,
                                                      name, phone, itogo, sum),
                                  cid, mid, reply_markup=keyb, parse_mode='markdown', disable_web_page_preview=True)
        elif sp[0] == 'clean':
            try:
                a_ll = sql_base.sqlrequest(
                    "SELECT * FROM history WHERE tid='" + str(tid) + "' and type='mobile' ORDER BY id DESC")
                curr = str(*sql_base.sqlrequest("SELECT currency FROM users WHERE tid='" + str(tid) + "'"))
                address = a_ll[2]
                phone = a_ll[4]
                coin = a_ll[8]
                addr_spl = address.replace(str(address)[5:37], '....')
                sql_base.sqlupdate("UPDATE history SET sum='0' WHERE id='" + str(a_ll[0]) + "'")

                if coin != 'BIP':
                    comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.11, 4)
                elif coin == 'BIP':
                    comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.01, 4)
                min_sum = functions.truncate(const.min_mob * functions.buy_price() * functions.usd_rate(curr))
                max_sum = functions.truncate(const.mobile * functions.buy_price() * functions.usd_rate(curr))

                keyb = InlineKeyboardMarkup()
                keyb.add(InlineKeyboardButton(text='Оплата монетой: ' + coin, callback_data='summ_coin'))
                keyb.add(*[InlineKeyboardButton(text=name, callback_data='summ_' + name) for name in a])
                keyb.add(InlineKeyboardButton(text='Отмена', callback_data='summ_cancel'),
                         InlineKeyboardButton(text='0', callback_data='pass'),
                         InlineKeyboardButton(text='Очистить', callback_data='summ_clean'),
                         InlineKeyboardButton(text='Готово', callback_data='pass'))

                wallet = sql_base.sqlrequest("SELECT * FROM wallets WHERE address='" + str(address) + "'")
                if wallet is not None:
                    name = '*Со счёта:* [%s](https://minterscan.net/address/%s) (%s)\n' % (addr_spl, address, wallet[2])
                elif wallet is None:
                    name = '*Со счёта:* [%s](https://minterscan.net/address/%s)\n' % (addr_spl, address)

                bot.edit_message_text('💸 *Сумма пополнения*\n\n'
                                      '*Мин. сумма:* %s BIP (%s %s)\n'
                                      '*Макс. сумма:* %s BIP (%s %s)\n'
                                      '*Комиссия:* %s BIP\n\n'
                                      '📲 *Пополнение телефона*\n\n'
                                      '%s'
                                      '*Номер телефона:* %s\n'
                                      '*Итого сумма:* 0 %s (0 %s)\n\n'
                                      '*Ввод:* 0 BIP' % (
                                      const.min_mob, min_sum, curr, const.mobile, max_sum, curr, comis,
                                      name, phone, coin, curr),
                                      cid, mid, reply_markup=keyb, parse_mode='markdown', disable_web_page_preview=True)
            except telebot.apihelper.ApiException:
                bot.answer_callback_query(call.id, 'Очищено', show_alert=True)
        elif sp[0] == 'ready':
            a_ll = sql_base.sqlrequest(
                "SELECT * FROM history WHERE tid='" + str(tid) + "' and type='mobile' ORDER BY id DESC")
            curr = str(*sql_base.sqlrequest("SELECT currency FROM users WHERE tid='" + str(tid) + "'"))
            address = a_ll[2]
            phone = a_ll[4]
            coin = a_ll[8]
            summ_in_bip = a_ll[5]
            PARAMS = {'address': a_ll[2]}
            r = requests.get(url=const.node_url + '/address', params=PARAMS)
            js = r.json()['result']['balance']
            for (k, v) in js.items():
                v = float(v) / 1000000000000000000
                if k == a_ll[8]:
                    amount = v
                    if const.mobile < float(a_ll[5]) or const.min_mob > float(a_ll[5]):
                        bot.answer_callback_query(call.id, '⚠️ Сумма платежа выходит за пределы лимитов',
                                                  show_alert=True)
                        if coin is None:
                            coin = 'BIP'
                        addr_spl = address.replace(str(address)[5:37], '....')
                        sql_base.sqlupdate("UPDATE history SET sum='0', in_coin='0' WHERE id='" + str(a_ll[0]) + "'")

                        min_sum = functions.truncate(const.min_mob * functions.buy_price() * functions.usd_rate(curr))
                        max_sum = functions.truncate(const.mobile * functions.buy_price() * functions.usd_rate(curr))

                        if coin != 'BIP':
                            comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.11, 4)
                        elif coin == 'BIP':
                            comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.01, 4)

                        keyb = InlineKeyboardMarkup()
                        keyb.add(InlineKeyboardButton(text='Оплата монетой: ' + coin, callback_data='summ_coin'))
                        keyb.add(*[InlineKeyboardButton(text=name, callback_data='summ_' + name) for name in a])
                        keyb.add(InlineKeyboardButton(text='Отмена', callback_data='summ_cancel'),
                                 InlineKeyboardButton(text='0', callback_data='pass'),
                                 InlineKeyboardButton(text='Очистить', callback_data='summ_clean'),
                                 InlineKeyboardButton(text='Готово', callback_data='pass'))

                        wallet = sql_base.sqlrequest("SELECT * FROM wallets WHERE address='" + str(address) + "'")
                        if wallet is not None:
                            name = '*Со счёта:* [%s](https://minterscan.net/address/%s) (%s)\n' % (
                                addr_spl, address, wallet[2])
                        elif wallet is None:
                            name = '*Со счёта:* [%s](https://minterscan.net/address/%s)\n' % (addr_spl, address)

                        bot.edit_message_text('💸 *Сумма пополнения*\n\n'
                                              '*Мин. сумма:* %s BIP (%s %s)\n'
                                              '*Макс. сумма:* %s BIP (%s %s)\n'
                                              '*Комиссия:* %s BIP\n\n'
                                              '📲 *Пополнение телефона*\n\n'
                                              '%s'
                                              '*Номер телефона:* %s\n'
                                              '*Итого сумма:* 0 %s (0 %s)\n\n'
                                              '*Ввод:* 0 BIP' % (const.min_mob,
                                                                 min_sum, curr, const.mobile, max_sum, curr, comis,
                                                                 name,
                                                                 phone, coin, curr),
                                              cid, mid, reply_markup=keyb, parse_mode='markdown',
                                              disable_web_page_preview=True)
                    elif float(amount) < float(a_ll[9]):
                        amo = float(a_ll[9]) - float(amount)
                        bot.answer_callback_query(call.id, 'На вашем счете недостаточно %s %s' % (amo, k),
                                                  show_alert=True)
                        if coin is None:
                            coin = 'BIP'
                        addr_spl = address.replace(str(address)[5:37], '....')
                        sql_base.sqlupdate("UPDATE history SET sum='0', in_coin='0' WHERE id='" + str(a_ll[0]) + "'")

                        min_sum = functions.truncate(const.min_mob * functions.buy_price() * functions.usd_rate(curr))
                        max_sum = functions.truncate(const.mobile * functions.buy_price() * functions.usd_rate(curr))

                        if coin != 'BIP':
                            comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.11, 4)
                        elif coin == 'BIP':
                            comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.01, 4)

                        keyb = InlineKeyboardMarkup()
                        keyb.add(InlineKeyboardButton(text='Оплата монетой: ' + coin, callback_data='summ_coin'))
                        keyb.add(*[InlineKeyboardButton(text=name, callback_data='summ_' + name) for name in a])
                        keyb.add(InlineKeyboardButton(text='Отмена', callback_data='summ_cancel'),
                                 InlineKeyboardButton(text='0', callback_data='pass'),
                                 InlineKeyboardButton(text='Очистить', callback_data='summ_clean'),
                                 InlineKeyboardButton(text='Готово', callback_data='pass'))

                        wallet = sql_base.sqlrequest("SELECT * FROM wallets WHERE address='" + str(address) + "'")
                        if wallet is not None:
                            name = '*Со счёта:* [%s](https://minterscan.net/address/%s) (%s)\n' % (
                                addr_spl, address, wallet[2])
                        elif wallet is None:
                            name = '*Со счёта:* [%s](https://minterscan.net/address/%s)\n' % (addr_spl, address)

                        bot.edit_message_text('💸 *Сумма пополнения*\n\n'
                                              '*Мин. сумма:* %s BIP (%s %s)\n'
                                              '*Макс. сумма:* %s BIP (%s %s)\n'
                                              '*Комиссия:* %s BIP\n\n'
                                              '📲 *Пополнение телефона*\n\n'
                                              '%s'
                                              '*Номер телефона:* %s\n'
                                              '*Итого сумма:* 0 %s (0 %s)\n\n'
                                              '*Ввод:* 0 BIP' % (const.min_mob, min_sum, curr, const.mobile, max_sum,
                                                                 curr, comis, name, phone, coin, curr),
                                              cid, mid, reply_markup=keyb, parse_mode='markdown',
                                              disable_web_page_preview=True)
                    elif (const.min_mob <= int(sp[1]) <= const.mobile) and float(amount) >= float(a_ll[9]):
                        summ_in_bip = float(summ_in_bip)
                        if coin == 'BIP':
                            comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.01, 4)
                            in_coin = str(summ_in_bip - comis)
                            in_curr = str(functions.buy_price() * (summ_in_bip - comis) * functions.usd_rate(curr))
                        else:
                            comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.11, 4)
                            in_coin = str((summ_in_bip - comis) / functions.get_price(coin))
                            in_curr = str(functions.buy_price() * (summ_in_bip - comis) * functions.usd_rate(curr))
                        sql_base.sqlupdate("UPDATE history SET in_curr='" +
                                           in_curr + "', in_coin='" + in_coin + "', curr='"
                                           + curr + "' WHERE id='" + str(a_ll[0]) + "'")
                        return sp[1]

    def pin_verify(call):
        message = call.message
        cid = message.chat.id
        mid = message.message_id
        tid = call.from_user.id
        r = call.data[8:]
        sp = r.split('_')
        if sp[0].isdigit():
            sp_ = s_p(sp)
            pin = sp_[0]
            ab = sp_[1]

            if pin == '●●●●':
                password = str(sp[1] + sp[0]).encode('utf-8')
                addr = str(
                    *sql_base.sqlrequest("SELECT wallet FROM history WHERE tid='" + str(tid) + "' ORDER BY id DESC"))
                info_wal = sql_base.sqlrequest("SELECT addresses, mnemonics FROM users WHERE tid='" + str(tid) + "'")
                mnem = info_wal[1].split(',')
                i_mnem = info_wal[0].split(',').index(addr)
                mnemonic = mnem[i_mnem]
                try:
                    mnemonic = functions.decrypt(password, mnemonic.encode('utf-8')).decode('utf-8')
                    return mnemonic
                except:
                    bot.answer_callback_query(call.id, '🚫 PIN-код неверный! Попробуйте снова.', show_alert=True)
                    a = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
                    keyb = InlineKeyboardMarkup()
                    keyb.add(*[InlineKeyboardButton(text=name, callback_data='ver_pin_' + name) for name in a])
                    keyb.add(InlineKeyboardButton(text='Отмена', callback_data='ver_pin_cancel'),
                             InlineKeyboardButton(text='0', callback_data='ver_pin_0'),
                             InlineKeyboardButton(text='Очистить', callback_data='ver_pin_clean'))
                    bot.edit_message_text('🔐 *Пинкод для подтверждения*\n'
                                          '💼 [%s](https://minterscan.net/address/%s)\n\n'
                                          '*PIN:* ○○○○' % (addr.replace(addr[5:37], '....'), addr), cid, mid,
                                          reply_markup=keyb, parse_mode='markdown', disable_web_page_preview=True)
            else:
                addr = str(
                    *sql_base.sqlrequest("SELECT wallet FROM history WHERE tid='" + str(tid) + "' ORDER BY id DESC"))
                a = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
                keyb = InlineKeyboardMarkup()
                keyb.add(
                    *[InlineKeyboardButton(text=name, callback_data='ver_pin_' + name + '_' + ab + sp[0]) for name
                      in a])
                keyb.add(InlineKeyboardButton(text='Отмена', callback_data='ver_pin_cancel'),
                         InlineKeyboardButton(text='0', callback_data='ver_pin_0_' + ab + sp[0]),
                         InlineKeyboardButton(text='Очистить', callback_data='ver_pin_clean'))
                bot.edit_message_text('🔐 *Пинкод для подтверждения*\n'
                                      '💼 [%s](https://minterscan.net/address/%s)\n\n'
                                      '*PIN:* %s' % (addr.replace(addr[5:37], '....'), addr, pin), cid, mid,
                                      parse_mode='markdown', reply_markup=keyb, disable_web_page_preview=True)
        elif sp[0] == 'cancel':
            bot.delete_message(cid, mid)
            start(cid, tid)
        elif sp[0] == 'clean':
            try:
                addr = str(
                    *sql_base.sqlrequest("SELECT wallet FROM history WHERE tid='" + str(tid) + "' ORDER BY id DESC"))
                a = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
                keyb = InlineKeyboardMarkup()
                keyb.add(*[InlineKeyboardButton(text=name, callback_data='ver_pin_' + name) for name in a])
                keyb.add(InlineKeyboardButton(text='Отмена', callback_data='ver_pin_cancel'),
                         InlineKeyboardButton(text='0', callback_data='ver_pin_0'),
                         InlineKeyboardButton(text='Очистить', callback_data='ver_pin_clean'))
                bot.edit_message_text('🔐 *Пинкод для подтверждения*\n'
                                      '💼 [%s](https://minterscan.net/address/%s)\n\n'
                                      '*PIN:* ○○○○' % (addr.replace(addr[5:37], '....'), addr), cid, mid,
                                      reply_markup=keyb, parse_mode='markdown', disable_web_page_preview=True)
            except telebot.apihelper.ApiException:
                bot.answer_callback_query(call.id, 'Очищено', show_alert=True)

    def edit_pin(call):
        message = call.message
        cid = message.chat.id
        mid = message.message_id
        tid = call.from_user.id
        r = call.data[8:]
        sp = r.split('_')
        a = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
        if sp[0].isdigit():
            sp_ = s_p(sp)
            pin = sp_[0]
            ab = sp_[1]

            if pin == '●●●●':
                password = str(sp[1] + sp[0]).encode('utf-8')
                addr = str(
                    *sql_base.sqlrequest("SELECT wallet FROM history WHERE tid='" + str(tid) + "' ORDER BY id DESC"))
                info_wal = sql_base.sqlrequest("SELECT addresses, mnemonics FROM users WHERE tid='" + str(tid) + "'")
                mnem = info_wal[1].split(',')
                i_mnem = info_wal[0].split(',').index(addr)
                mnemonic = mnem[i_mnem]
                try:
                    mnemonic = functions.decrypt(password, mnemonic.encode('utf-8')).decode('utf-8')
                    return mnemonic
                except:
                    bot.answer_callback_query(call.id, '🚫 PIN-код не верный! Попробуйте снова.', show_alert=True)
                    keyb = InlineKeyboardMarkup()
                    keyb.add(*[InlineKeyboardButton(text=name, callback_data='ver_pin_' + name) for name in a])
                    keyb.add(InlineKeyboardButton(text='Отмена', callback_data='ver_pin_cancel'),
                             InlineKeyboardButton(text='0', callback_data='ver_pin_0'),
                             InlineKeyboardButton(text='Очистить', callback_data='ver_pin_clean'))
                    bot.edit_message_text('🔐 *Пинкод для подтверждения*', cid, mid, reply_markup=keyb,
                                          parse_mode='markdown')
            else:
                keyb = InlineKeyboardMarkup()
                keyb.add(
                    *[InlineKeyboardButton(text=name, callback_data='ver_pin_' + name + '_' + ab + sp[0]) for name
                      in a])
                keyb.add(InlineKeyboardButton(text='Отмена', callback_data='ver_pin_cancel'),
                         InlineKeyboardButton(text='0', callback_data='ver_pin_0_' + ab + sp[0]),
                         InlineKeyboardButton(text='Очистить', callback_data='ver_pin_clean'))
                bot.edit_message_text('🔐 *Пинкод для подтверждения*\n\n'
                                      '*PIN:* ' + pin, cid, mid, parse_mode='markdown', reply_markup=keyb)
        elif sp[0] == 'cancel':
            bot.delete_message(cid, mid)
            start(cid, tid)
        elif sp[0] == 'clean':
            try:
                keyb = InlineKeyboardMarkup()
                keyb.add(*[InlineKeyboardButton(text=name, callback_data='ver_pin_' + name) for name in a])
                keyb.add(InlineKeyboardButton(text='Отмена', callback_data='ver_pin_cancel'),
                         InlineKeyboardButton(text='0', callback_data='ver_pin_0'),
                         InlineKeyboardButton(text='Очистить', callback_data='ver_pin_clean'))
                bot.edit_message_text('🔐 *Пинкод для подтверждения*', cid, mid, reply_markup=keyb,
                                      parse_mode='markdown')
            except telebot.apihelper.ApiException:
                bot.answer_callback_query(call.id, 'Очищено', show_alert=True)

    def s_p(sp):
        if len(sp) == 1:
            sup = len(sp)
        elif len(sp) == 2:
            sup = len(sp[1] + sp[0])

        if sup == 1:
            ab = ''
            pin = '●○○○'
        elif sup == 2:
            ab = sp[1]
            pin = '●●○○'
        elif sup == 3:
            ab = sp[1]
            pin = '●●●○'
        elif sup == 4:
            ab = sp[1]
            pin = '●●●●'
        return pin, ab
