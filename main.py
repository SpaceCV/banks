# -*- coding: utf-8 -*-
import datetime
from uuid import getnode as get_mac

import qrcode
import telebot

import const
import functions
import modules_old
import sqlhelper
from mintersdk.minterapi import MinterAPI
from mintersdk.sdk.transactions import MinterSendCoinTx, MinterBuyCoinTx
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
    modules_old.Modules(message).start()


@bot.message_handler(commands=['admin'])
def command_admin(message):
    cid = message.chat.id
    tid = message.from_user.id

    if tid in const.admins:
        adm = modules_old.admin()

        bot.send_message(cid, adm[0], reply_markup=adm[1])


@bot.message_handler(commands=['cu'])
def command_admin(message):
    modules_old.Modules(message).cu()


@bot.message_handler(content_types=["text"])
def text(message):
    tid = message.from_user.id
    cid = message.chat.id
    cbt = functions.cbt(tid)
    if (message.chat.type == 'private' or tid in const.admins) and cbt is True:
        mtext = message.text
        if mtext == 'Кабинет':
            modules_old.Modules(message).cab_btn()
        elif mtext == 'Платежи':
            modules_old.pays(message, 1)
        elif mtext == 'История':
            modules_old.history(message)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        cid = call.message.chat.id
        mid = call.message.message_id
        tid = call.from_user.id
        data = call.data
        mdls = modules_old.Modules(call)

        cbt = functions.cbt(tid)
        if (call.message.chat.type == 'private' or tid in const.admins) and cbt is True:
            if call.data[:2] == 'a_':
                a_(tid, cid, mid, call.data[2:])
            elif call.data.startswith('Mx'):
                mdls.mx()
            elif data[:5] == 'name_':
                modules_old.name_(call)
            elif call.data[:6] == 'valut_':
                curr = call.data[6:]
                sql_base.sqlupdate(
                    "UPDATE users SET currency='" + curr + "' WHERE tid='" + str(tid) + "'")
                bot.edit_message_text('Валюта успешно изменена на ' + curr, cid, mid, parse_mode='markdown')
            elif call.data[:7] == 'choose_':
                address = call.data[7:]
                adr_info = sql_base.sqlrequest("SELECT addresses, mnemonics FROM users WHERE tid='" + str(tid) + "'")
                addresses = adr_info[0].split(',')
                i_mnem = addresses.index(address)
                addresses.remove(address)
                addresses.insert(0, address)

                mnemonics = adr_info[1].split(',')
                mnem = mnemonics[i_mnem]
                mnemonics.remove(mnem)
                mnemonics.insert(0, mnem)

                adrs = ''
                for i in addresses:
                    if i == addresses[0]:
                        adrs += i
                    else:
                        adrs += ',' + i

                mnems = ''
                for i in mnemonics:
                    if i == mnemonics[0]:
                        mnems += i
                    else:
                        mnems += ',' + i

                sql_base.sqlupdate(
                    "UPDATE users SET addresses='" + adrs + "', mnemonics='" + mnems + "' WHERE tid='" + str(tid) + "'")

                bot.answer_callback_query(call.id, 'Счет %s выбран основным' % address, show_alert=True)

                cabi = modules_old.cab(tid)

                bot.edit_message_text(cabi[0], cid, mid,
                                      reply_markup=cabi[1], parse_mode='markdown', disable_web_page_preview=True)
            elif call.data == 'mobile':
                addresses = str(*sql_base.sqlrequest("SELECT addresses FROM users WHERE tid='" + str(tid) + "'"))
                addresses = addresses.split(',')
                sql_base.sqlupdate(
                    "INSERT INTO history (tid, status, type, date) VALUES ('"
                    + str(tid) + "', 'wait', 'mobile', CURRENT_TIMESTAMP)")
                if len(addresses) > 1:
                    result = []
                    keyboard = InlineKeyboardMarkup(row_width=2)
                    for i in addresses:
                        if addresses[0] == i:
                            text = '☑️ '
                        else:
                            text = ''

                        wallet = sql_base.sqlrequest("SELECT * FROM wallets WHERE address='" + str(i) + "'")
                        if wallet is not None:
                            name = wallet[2]
                        elif wallet is None:
                            name = i.replace(i[5:37], '....')
                        keb = InlineKeyboardButton(text=text + name, callback_data='a_' + i)
                        result.append(keb)

                    keyboard.add(*result)
                    bot.edit_message_text('💼 *Выберите счет для оплаты*', cid, mid, parse_mode='markdown',
                                          reply_markup=keyboard)
                else:
                    a_(tid, cid, mid, addresses[0])
            elif call.data[:5] == 'input':
                msg = bot.edit_message_text('📱 *Номер телефона*\n\n'
                                            '*Доступно:* Россия, Казахстан\n'
                                            '*Формат:* +79991234567', cid, mid, parse_mode='markdown')
                bot.register_next_step_handler(msg, number)
            elif call.data[:5] == 'phone':
                phone = call.data[5:]
                ks = keyboard_start(tid, phone)

                bot.edit_message_text(ks[0], cid, mid, reply_markup=ks[1], parse_mode='markdown',
                                      disable_web_page_preview=True)
            elif call.data in const.langs:
                sql_base.sqlupdate(
                    "INSERT INTO users (tid, lang, status, rd) VALUES ('" + str(tid) + "', '"
                    + str(call.data) + "', 'active', CURRENT_TIMESTAMP)")
                keyb = InlineKeyboardMarkup()
                keyb.add(*[InlineKeyboardButton(text=name, callback_data=name) for name in const.currency])

                bot.edit_message_text('Выберите валюту', cid, mid, reply_markup=keyb)
            elif call.data in const.currency:
                sql_base.sqlupdate("UPDATE users SET currency='" + str(call.data) + "' WHERE tid='" + str(tid) + "'")
                keyb = InlineKeyboardMarkup()
                keyb.add(InlineKeyboardButton(text='Прочитал', callback_data='read'))
                bot.edit_message_text('*Что такое ПИН-код и зачем он нужен?*\n\n'
                                      'ПИН-код – это секретный защитный код счета из 4х цифр. Он шифрует seed-фразу и '
                                      'таким образом никто не имеет доступа к счету, а также понадобится при '
                                      'платежных операциях\n'
                                      'Придумайте собственный ПИН-код, который вы точно не забудете!',
                                      cid, mid, parse_mode='markdown', reply_markup=keyb)
            elif data == 'read':
                a = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
                keyb = InlineKeyboardMarkup()
                keyb.add(*[InlineKeyboardButton(text=name, callback_data='pin_' + name) for name in a])
                keyb.add(InlineKeyboardButton(text='0', callback_data='pin_0_0'),
                         InlineKeyboardButton(text='Очистить', callback_data='pin_clean'))
                bot.edit_message_text('🔐 *Установите PIN-код для вашего счета*\n\n'
                                      '*PIN:* ○○○○', cid, mid, reply_markup=keyb, parse_mode='markdown')
            elif call.data[:4] == 'pin_':
                verify = pin(call)
                if verify is not None:
                    if verify[0] == 1:
                        sql_base.sqlupdate("UPDATE users SET addresses='" + str(verify[1]) + "', mnemonics='" + str(
                            verify[2]) + "' WHERE tid='" + str(tid) + "'")

                        bot.edit_message_text('✅ Счет создан и защищен!', cid, mid)
                        start(cid, tid)
            elif call.data[:7] == 'deposit':
                address = call.data[8:]
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=12,
                    border=5,
                )

                qr.add_data(address)
                qr.make(fit=True)

                img = qr.make_image(fill_color="black", back_color="white")
                path = const.qr_path + str(tid) + '.png'
                img.save(path)

                bot.send_photo(cid, open(path, 'rb'), caption='Переведите монеты на этот кошелек:')
                bot.send_message(cid, '`%s`' % address, parse_mode='markdown')
            elif call.data[:7] == 'ver_pin':
                mnemonic = pin_verify(call)
                if mnemonic is not None:
                    status_qiwi = str(*sql_base.sqlrequest("SELECT qiwi FROM status"))
                    if status_qiwi == '1':
                        tr = sql_base.sqlrequest(
                            "SELECT * FROM history WHERE tid='" + str(tid) + "' and status='wait' ORDER BY id DESC")
                        curr = str(*sql_base.sqlrequest("SELECT currency FROM users WHERE tid='" + str(tid) + "'"))
                        coin = tr[8]
                        summ = float(tr[5])
                        addr = tr[2]
                        rub5 = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price(), 4)
                        if coin == 'BIP':
                            comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.01, 4)
                            coms = 0.01
                            in_coin = functions.truncate((float(tr[5]) - coms), 4)
                            summ_p = ((summ - comis) / 100) * 102
                            summ_m = ((summ - comis) / 100) * 98
                        else:
                            comis = functions.truncate(5 / functions.usd_rate('RUB') / functions.buy_price() + 0.11, 4)
                            coms = 0.11
                            in_coin = functions.truncate((float(tr[5]) - coms) / functions.get_price(coin))
                            summ_p = ((summ - comis) / functions.get_price(coin)) / 100 * 102
                            summ_m = ((summ - comis) / functions.get_price(coin)) / 100 * 98
                            in_bip = (float(tr[5]) - coms) * functions.get_price(coin)
                        usd = functions.buy_price() * (float(tr[5]) - coms)
                        if float(summ_m) < float(tr[9]) < float(summ_p):
                            sum_for_pay = usd * functions.usd_rate('RUB') - rub5
                            sum_in_curr = usd * functions.usd_rate(curr) - rub5
                            sql_base.sqlupdate("UPDATE history SET curr='" + str(curr) + "', in_curr='" + str(
                                functions.truncate(sum_in_curr)) + "' WHERE id='" + str(tr[0]) + "'")
                            oid = Utils.detect_mobile(str(tr[4]))
                            bot.edit_message_text('🕑 Подождите... Операция выполняется', cid, mid)
                            minter = MinterAPI(api_url=const.node_url)

                            p_code = functions.num_ver(oid[0], 4)

                            if p_code == 'KZ':
                                bot.edit_message_text('Сервис временно недоступен', cid, mid)
                            elif p_code == 'RU':
                                # CONVERT COIN
                                if coin != 'BIP':
                                    try:
                                        addr = functions.get_address(mnemonic)
                                        pk = functions.private_key(mnemonic)
                                        nonce = minter.get_nonce(address=addr)
                                        convert = MinterBuyCoinTx(coin_to_buy='BIP',
                                                                  value_to_buy=functions.truncate(summ, 4) - coms,
                                                                  coin_to_sell=coin,
                                                                  max_value_to_sell=1000000000000000000,
                                                                  nonce=nonce, gas_coin=coin)
                                        convert.sign(pk)
                                        convert = minter.send_transaction(convert.signed_tx)
                                        hash = 'Mt' + convert['result']['hash'].lower()
                                        sql_base.sqlupdate("UPDATE history SET c_hash='"
                                                           + str(hash) + "' WHERE id='" + str(tr[0]) + "'")
                                    except Exception as e:
                                        print('Ошибка в конвертации ', e)

                                block = minter.get_status()['result']['latest_block_height']

                                # SEND COIN
                                try:
                                    a = True
                                    while a:
                                        block1 = minter.get_status()['result']['latest_block_height']
                                        if block == block1:
                                            a = True
                                        else:
                                            break
                                    pk = functions.private_key(mnemonic)
                                    nonce = minter.get_nonce(address=addr)
                                    tx = MinterSendCoinTx(coin='BIP', to=functions.get_address(const.mnemonic),
                                                          value=summ - coms, nonce=nonce, gas_coin=coin)
                                    tx.sign(pk)
                                    send = minter.send_transaction(tx.signed_tx)
                                    hash = 'Mt' + send['result']['hash'].lower()
                                    sql_base.sqlupdate("UPDATE history SET s_hash='"
                                                       + str(hash) + "' WHERE id='" + str(tr[0]) + "'")
                                    status_qiwi = str(*sql_base.sqlrequest("SELECT qiwi FROM status"))
                                    pay = qiwi_pay.pay(str(oid[0]).replace('7', '', 1), oid[1], sum_for_pay)
                                    pay_js = pay.json()
                                    if pay.status_code == 200:
                                        sql_base.sqlupdate(
                                            "UPDATE history SET status='done', date=CURRENT_TIMESTAMP WHERE id='"
                                            + str(tr[0]) + "'")
                                        bot.edit_message_text('✅ Оплата прошла успешно!', cid, mid)
                                        for i in const.admins:
                                            User = bot.get_chat_member(tid, tid).user
                                            first_name = User.first_name
                                            last_name = User.last_name
                                            username = User.username
                                            bot.send_message(i, '*Совершена оплата*\n'
                                                                '*Пользователь:* [%s %s](t.me/%s) (id=%s)\n'
                                                                '*Сумма:* %s RUB %s BIP\n'
                                                                '*Телефон:* %s' % (first_name, last_name, username, tid,
                                                                                   sum_for_pay, summ,
                                                                                   oid[0]),
                                                             parse_mode='markdown',
                                                             disable_web_page_preview=True)
                                    elif ('errorCode' or 'code') in pay_js:
                                        if pay_js['code'] == 'QWPRC-220':
                                            bot.edit_message_text('Сервис временно недоступен', cid, mid)
                                            for i in const.admins:
                                                bot.send_message(i, 'На киви закончились деньги')
                                except Exception as e:
                                    print('Ошибка в оплате ', e)
                                    bot.edit_message_text('Оплата не прошла', cid, mid)
                        else:
                            bot.edit_message_text('Цена этой монеты изменилась. Попробуйте еще раз.', cid, mid)
                    elif status_qiwi == '0':
                        bot.edit_message_text('Сервис временно недоступен', cid, mid)
            elif call.data[:4] == 'summ':
                summ = KeyBoard(call)
                if summ is not None:
                    tr = sql_base.sqlrequest(
                        "SELECT * FROM history WHERE tid='" + str(tid) + "' and status='wait' ORDER BY id DESC")
                    a = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
                    keyb = InlineKeyboardMarkup()
                    keyb.add(*[InlineKeyboardButton(text=name, callback_data='ver_pin_' + name) for name in a])
                    keyb.add(InlineKeyboardButton(text='Отмена', callback_data='ver_pin_cancel'),
                             InlineKeyboardButton(text='0', callback_data='ver_pin_0_0'),
                             InlineKeyboardButton(text='Очистить', callback_data='ver_pin_clean'))
                    bot.edit_message_text('🔐 *Пинкод для подтверждения*\n'
                                          '💼 [%s](https://minterscan.net/address/%s)\n\n'
                                          '*PIN:* ○○○○' %
                                          (tr[2].replace(str(tr[2])[5:37], '....'), tr[2]), cid, mid,
                                          parse_mode='markdown', reply_markup=keyb, disable_web_page_preview=True)
            elif call.data == 'pass':
                pass
            elif call.data[:7] == 'history':
                i_d = str(call.data[7:])
                keyb = InlineKeyboardMarkup(row_width=2)
                keyb.add(InlineKeyboardButton(text='Поделиться', switch_inline_query='receipt ' + i_d),
                         InlineKeyboardButton(text='🚫 Повторить', callback_data='try'),
                         InlineKeyboardButton(text='Назад', callback_data='back_history'),
                         InlineKeyboardButton(text='🚫 Автоплатеж', callback_data='auto'))

                bot.edit_message_text(modules_old.receipt(i_d), cid, mid, parse_mode='markdown', reply_markup=keyb,
                                      disable_web_page_preview=True)
            elif call.data == 'back_history':
                history = sql_base.sqlrequestall("SELECT * FROM history WHERE tid='" + str(tid) + "' AND status='done'")
                keyboard = InlineKeyboardMarkup(row_width=2)

                if not history:
                    bot.send_message(cid, 'Вы не совершали никаких операций.')
                elif history:
                    for i in history:
                        dt = datetime.datetime.strptime(i[7], '%Y-%m-%d %H:%M:%S')
                        keyboard.add(InlineKeyboardButton(text=str(dt.date()), callback_data='history' + str(i[0])),
                                     InlineKeyboardButton(text='Сотовая связь', callback_data='history' + str(i[0])))
                    bot.edit_message_text('🧾 *История операций*', cid, mid, parse_mode='markdown',
                                          reply_markup=keyboard)
            elif call.data == 'stats':
                keyb = InlineKeyboardMarkup()
                keyb.add(InlineKeyboardButton(text='Реф. система', callback_data='ref'),
                         InlineKeyboardButton(text='Пользователи', callback_data='users'),
                         InlineKeyboardButton(text='Финансы', callback_data='finance'),
                         InlineKeyboardButton(text='Назад', callback_data='back_admin'))
                bot.edit_message_text('Статистика', cid, mid, reply_markup=keyb)
            elif call.data == 'back_admin':
                adm = admin()

                bot.edit_message_text(adm[0], cid, mid, reply_markup=adm[1])
            elif call.data == 'edit_rate':
                p_p = sql__base.sqlrequest("SELECT pbuy, psell FROM status")
                buy_rub = functions.truncate(functions.buy_price() * functions.usd_rate('RUB'), 4)
                sell_rub = functions.truncate(functions.sell_price() * functions.usd_rate('RUB'), 4)
                buy_price = functions.truncate(functions.buy_price(), 4)
                sell_price = functions.truncate(functions.sell_price(), 4)

                r = requests.get(url=const.btc1001)
                pp = sql__base.sqlrequest("SELECT p_buy, p_sell FROM status")
                pbuy_price = (float(r.json()['bip2btc']) / 100) * (100 + float(pp[0]))
                psell_price = (float(r.json()['btc2bip']) / 100) * (100 + float(pp[1]))
                pbuy_rub = functions.truncate(pbuy_price * functions.usd_rate('RUB'), 4)
                psell_rub = functions.truncate(psell_price * functions.usd_rate('RUB'), 4)

                keyb = InlineKeyboardMarkup()
                keyb.row(InlineKeyboardButton(text='Покупка', callback_data='buy'),
                         InlineKeyboardButton(text='Продажа', callback_data='sell'))
                keyb.row(InlineKeyboardButton(text='+ 1%', callback_data='pass'),
                         InlineKeyboardButton(text='- 1%', callback_data='pass'),
                         InlineKeyboardButton(text='+ 0.1%', callback_data='pass'),
                         InlineKeyboardButton(text='- 0.1%', callback_data='pass'))
                keyb.row(InlineKeyboardButton(text='Сброс до 1001', callback_data='rate_reset'),
                         InlineKeyboardButton(text='Очистить', callback_data='rate_res'),
                         InlineKeyboardButton(text='Готово', callback_data='rate_ready'))

                bot.edit_message_text('Действующий курс:\n'
                                      '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                      '📉 *Продажа:* $%s (%s RUB) %s%%\n\n'
                                      'Изменяем на:\n'
                                      '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                      '📉 *Продажа:* $%s (%s RUB) %s%%' % (
                                          buy_price, buy_rub, p_p[0], sell_price, sell_rub, p_p[1],
                                          functions.truncate(pbuy_price, 4), pbuy_rub, pp[0],
                                          functions.truncate(psell_price, 4), psell_rub, pp[1]),
                                      cid, mid, reply_markup=keyb, parse_mode='markdown')
            elif call.data == 'rate_reset':
                sql__base.sqlupdate("UPDATE status SET psell='0', pbuy='0', status='2'")
                bot.answer_callback_query(call.id, 'Сброшено до 1001', show_alert=True)

                p_p = sql__base.sqlrequest("SELECT pbuy, psell FROM status")
                buy_rub = functions.truncate(functions.buy_price() * functions.usd_rate('RUB'), 4)
                sell_rub = functions.truncate(functions.sell_price() * functions.usd_rate('RUB'), 4)
                buy_price = functions.truncate(functions.buy_price(), 4)
                sell_price = functions.truncate(functions.sell_price(), 4)

                r = requests.get(url=const.btc1001)
                pp = sql__base.sqlrequest("SELECT p_buy, p_sell FROM status")
                pbuy_price = (float(r.json()['bip2btc']) / 100) * (100 + float(p_p[0]))
                psell_price = (float(r.json()['btc2bip']) / 100) * (100 + float(p_p[1]))
                pbuy_rub = functions.truncate(pbuy_price * functions.usd_rate('RUB'), 4)
                psell_rub = functions.truncate(psell_price * functions.usd_rate('RUB'), 4)

                keyb = InlineKeyboardMarkup()
                keyb.row(InlineKeyboardButton(text='Покупка', callback_data='buy'),
                         InlineKeyboardButton(text='Продажа', callback_data='sell'))
                keyb.row(InlineKeyboardButton(text='+ 1%', callback_data='pass'),
                         InlineKeyboardButton(text='- 1%', callback_data='pass'),
                         InlineKeyboardButton(text='+ 0.1%', callback_data='pass'),
                         InlineKeyboardButton(text='- 0.1%', callback_data='pass'))
                keyb.row(InlineKeyboardButton(text='Очистить', callback_data='rate_res'),
                         InlineKeyboardButton(text='Готово', callback_data='rate_ready'))

                bot.edit_message_text('Действующий курс:\n'
                                      '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                      '📉 *Продажа:* $%s (%s RUB) %s%%\n\n'
                                      'Изменяем на:\n'
                                      '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                      '📉 *Продажа:* $%s (%s RUB) %s%%' % (
                                          buy_price, buy_rub, p_p[0], sell_price, sell_rub, p_p[1],
                                          functions.truncate(pbuy_price, 4), pbuy_rub,
                                          pp[0], functions.truncate(psell_price, 4), psell_rub, pp[1]),
                                      cid, mid, reply_markup=keyb, parse_mode='markdown')
            elif call.data == 'rate_res':
                sql__base.sqlupdate("UPDATE status SET p_sell='0', p_buy='0'")
                bot.answer_callback_query(call.id, 'Очищено', show_alert=True)

                p_p = sql__base.sqlrequest("SELECT pbuy, psell FROM status")
                buy_rub = functions.truncate(functions.buy_price() * functions.usd_rate('RUB'), 4)
                sell_rub = functions.truncate(functions.sell_price() * functions.usd_rate('RUB'), 4)
                buy_price = functions.truncate(functions.buy_price(), 4)
                sell_price = functions.truncate(functions.sell_price(), 4)

                r = requests.get(url=const.btc1001)
                pp = sql__base.sqlrequest("SELECT p_buy, p_sell FROM status")
                pbuy_price = (float(r.json()['bip2btc']) / 100) * (100 + float(p_p[0]))
                psell_price = (float(r.json()['btc2bip']) / 100) * (100 + float(p_p[1]))
                pbuy_rub = functions.truncate(pbuy_price * functions.usd_rate('RUB'), 4)
                psell_rub = functions.truncate(psell_price * functions.usd_rate('RUB'), 4)

                keyb = InlineKeyboardMarkup()
                keyb.row(InlineKeyboardButton(text='Покупка', callback_data='buy'),
                         InlineKeyboardButton(text='Продажа', callback_data='sell'))
                keyb.row(InlineKeyboardButton(text='+ 1%', callback_data='pass'),
                         InlineKeyboardButton(text='- 1%', callback_data='pass'),
                         InlineKeyboardButton(text='+ 0.1%', callback_data='pass'),
                         InlineKeyboardButton(text='- 0.1%', callback_data='pass'))
                keyb.add(InlineKeyboardButton(text='Сброс до 1001', callback_data='rate_reset'))

                bot.edit_message_text('Действующий курс:\n'
                                      '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                      '📉 *Продажа:* $%s (%s RUB) %s%%\n\n'
                                      'Изменяем на:\n'
                                      '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                      '📉 *Продажа:* $%s (%s RUB) %s%%' % (
                                          buy_price, buy_rub, p_p[0], sell_price, sell_rub, p_p[1],
                                          functions.truncate(pbuy_price, 4), pbuy_rub,
                                          pp[0], functions.truncate(psell_price, 4), psell_rub, pp[1]),
                                      cid, mid, reply_markup=keyb, parse_mode='markdown')
            elif call.data == 'buy':
                try:
                    p_p = sql__base.sqlrequest("SELECT pbuy, psell FROM status")
                    buy_rub = functions.truncate(functions.buy_price() * functions.usd_rate('RUB'), 4)
                    sell_rub = functions.truncate(functions.sell_price() * functions.usd_rate('RUB'), 4)
                    buy_price = functions.truncate(functions.buy_price(), 4)
                    sell_price = functions.truncate(functions.sell_price(), 4)

                    r = requests.get(url=const.btc1001)
                    pp = sql__base.sqlrequest("SELECT p_buy, p_sell FROM status")
                    pbuy_price = (float(r.json()['bip2btc']) / 100) * (100 + float(pp[0]))
                    psell_price = (float(r.json()['btc2bip']) / 100) * (100 + float(pp[1]))
                    pbuy_rub = functions.truncate(pbuy_price * functions.usd_rate('RUB'), 4)
                    psell_rub = functions.truncate(psell_price * functions.usd_rate('RUB'), 4)

                    keyb = InlineKeyboardMarkup()
                    keyb.row(InlineKeyboardButton(text='☑️ Покупка', callback_data='buy'),
                             InlineKeyboardButton(text='Продажа', callback_data='sell'))
                    keyb.row(InlineKeyboardButton(text='+ 1%', callback_data='buy_p'),
                             InlineKeyboardButton(text='- 1%', callback_data='buy_m'),
                             InlineKeyboardButton(text='+ 0.1%', callback_data='buy_m1'),
                             InlineKeyboardButton(text='- 0.1%', callback_data='buy_p1'))
                    keyb.row(InlineKeyboardButton(text='Сброс до 1001', callback_data='rate_reset'),
                             InlineKeyboardButton(text='Очистить', callback_data='rate_res'),
                             InlineKeyboardButton(text='Готово', callback_data='rate_ready'))

                    bot.edit_message_text('Действующий курс:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%\n\n'
                                          'Изменяем на:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%' % (
                                              buy_price, buy_rub, p_p[0],
                                              sell_price, sell_rub, p_p[1],
                                              functions.truncate(pbuy_price, 4), pbuy_rub, pp[0],
                                              functions.truncate(psell_price, 4), psell_rub, pp[1]),
                                          cid, mid, reply_markup=keyb, parse_mode='markdown')
                except:
                    pass
            elif call.data == 'sell':
                try:
                    p_p = sql__base.sqlrequest("SELECT pbuy, psell FROM status")
                    buy_rub = functions.truncate(functions.buy_price() * functions.usd_rate('RUB'), 4)
                    sell_rub = functions.truncate(functions.sell_price() * functions.usd_rate('RUB'), 4)
                    buy_price = functions.truncate(functions.buy_price(), 4)
                    sell_price = functions.truncate(functions.sell_price(), 4)

                    r = requests.get(url=const.btc1001)
                    pp = sql__base.sqlrequest("SELECT p_buy, p_sell FROM status")
                    pbuy_price = (float(r.json()['bip2btc']) / 100) * (100 + float(pp[0]))
                    psell_price = (float(r.json()['btc2bip']) / 100) * (100 + float(pp[1]))
                    pbuy_rub = functions.truncate(pbuy_price * functions.usd_rate('RUB'), 4)
                    psell_rub = functions.truncate(psell_price * functions.usd_rate('RUB'), 4)

                    keyb = InlineKeyboardMarkup()
                    keyb.row(InlineKeyboardButton(text='Покупка', callback_data='buy'),
                             InlineKeyboardButton(text='☑️ Продажа', callback_data='sell'))
                    keyb.row(InlineKeyboardButton(text='+ 1%', callback_data='sell_p'),
                             InlineKeyboardButton(text='- 1%', callback_data='sell_m'),
                             InlineKeyboardButton(text='+ 0.1%', callback_data='sell_m1'),
                             InlineKeyboardButton(text='- 0.1%', callback_data='sell_p1'))
                    keyb.row(InlineKeyboardButton(text='Сброс до 1001', callback_data='rate_reset'),
                             InlineKeyboardButton(text='Очистить', callback_data='rate_res'),
                             InlineKeyboardButton(text='Готово', callback_data='rate_ready'))

                    bot.edit_message_text('Действующий курс:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%\n\n'
                                          'Изменяем на:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%' % (
                                              buy_price, buy_rub, p_p[0], sell_price, sell_rub, p_p[1],
                                              functions.truncate(pbuy_price, 4), pbuy_rub,
                                              pp[0], functions.truncate(psell_price, 4), psell_rub, pp[1]),
                                          cid, mid, reply_markup=keyb, parse_mode='markdown')
                except:
                    pass
            elif call.data == 'buy_p':
                try:
                    sql__base.sqlupdate("UPDATE status SET status='0'")
                    p_p = sql__base.sqlrequest("SELECT p_buy, p_sell FROM status")
                    p_buy = functions.truncate(float(p_p[0]), 1) + 1
                    sql__base.sqlupdate("UPDATE status SET p_buy='" + str(p_buy) + "'")

                    r = requests.get(url=const.btc1001)
                    pp = sql__base.sqlrequest("SELECT pbuy, psell FROM status")
                    pbuy_price = functions.truncate(functions.buy_price(), 4)
                    psell_price = functions.truncate(functions.sell_price(), 4)
                    pbuy_rub = functions.truncate(functions.buy_price() * functions.usd_rate('RUB'), 4)
                    psell_rub = functions.truncate(functions.sell_price() * functions.usd_rate('RUB'), 4)
                    buy_price = (float(r.json()['bip2btc']) / 100) * (100 + p_buy)
                    sell_price = (float(r.json()['btc2bip']) / 100) * (100 + float(p_p[1]))
                    buy_rub = functions.truncate(buy_price * functions.usd_rate('RUB'), 4)
                    sell_rub = functions.truncate(sell_price * functions.usd_rate('RUB'), 4)

                    keyb = InlineKeyboardMarkup()
                    keyb.row(InlineKeyboardButton(text='☑️ Покупка', callback_data='buy'),
                             InlineKeyboardButton(text='Продажа', callback_data='sell'))
                    keyb.row(InlineKeyboardButton(text='+ 1%', callback_data='buy_p'),
                             InlineKeyboardButton(text='- 1%', callback_data='buy_m'),
                             InlineKeyboardButton(text='+ 0.1%', callback_data='buy_m1'),
                             InlineKeyboardButton(text='- 0.1%', callback_data='buy_p1'))
                    keyb.row(InlineKeyboardButton(text='Сброс до 1001', callback_data='rate_reset'),
                             InlineKeyboardButton(text='Очистить', callback_data='rate_res'),
                             InlineKeyboardButton(text='Готово', callback_data='rate_ready'))

                    bot.edit_message_text('Действующий курс:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%\n\n'
                                          'Изменяем на:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%' % (
                                              functions.truncate(pbuy_price, 4), pbuy_rub, pp[0],
                                              functions.truncate(psell_price, 4), psell_rub, pp[1],
                                              functions.truncate(buy_price, 4), buy_rub, float(p_p[0] + 1),
                                              functions.truncate(sell_price, 4), sell_rub, p_p[1]),
                                          cid, mid, reply_markup=keyb, parse_mode='markdown')
                except:
                    pass
            elif call.data == 'buy_m':
                try:
                    sql__base.sqlupdate("UPDATE status SET status='0'")
                    p_p = sql__base.sqlrequest("SELECT p_buy, p_sell FROM status")
                    p_buy = functions.truncate(float(p_p[0]), 1) - 1
                    sql__base.sqlupdate("UPDATE status SET p_buy='" + str(p_buy) + "'")

                    r = requests.get(url=const.btc1001)
                    pp = sql__base.sqlrequest("SELECT pbuy, psell FROM status")
                    pbuy_price = functions.truncate(functions.buy_price(), 4)
                    psell_price = functions.truncate(functions.sell_price(), 4)
                    pbuy_rub = functions.truncate(pbuy_price * functions.usd_rate('RUB'), 4)
                    psell_rub = functions.truncate(psell_price * functions.usd_rate('RUB'), 4)
                    buy_price = (float(r.json()['bip2btc']) / 100) * (100 + p_buy)
                    sell_price = (float(r.json()['btc2bip']) / 100) * (100 + float(p_p[1]))
                    buy_rub = functions.truncate(buy_price * functions.usd_rate('RUB'), 4)
                    sell_rub = functions.truncate(sell_price * functions.usd_rate('RUB'), 4)

                    keyb = InlineKeyboardMarkup()
                    keyb.row(InlineKeyboardButton(text='☑️ Покупка', callback_data='buy'),
                             InlineKeyboardButton(text='Продажа', callback_data='sell'))
                    keyb.row(InlineKeyboardButton(text='+ 1%', callback_data='buy_p'),
                             InlineKeyboardButton(text='- 1%', callback_data='buy_m'),
                             InlineKeyboardButton(text='+ 0.1%', callback_data='buy_m1'),
                             InlineKeyboardButton(text='- 0.1%', callback_data='buy_p1'))
                    keyb.row(InlineKeyboardButton(text='Сброс до 1001', callback_data='rate_reset'),
                             InlineKeyboardButton(text='Очистить', callback_data='rate_res'),
                             InlineKeyboardButton(text='Готово', callback_data='rate_ready'))

                    bot.edit_message_text('Действующий курс:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%\n\n'
                                          'Изменяем на:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%' % (
                                              functions.truncate(pbuy_price, 4), pbuy_rub, pp[0],
                                              functions.truncate(psell_price, 4), psell_rub, pp[1],
                                              functions.truncate(buy_price, 4), buy_rub, float(p_p[0] - 1),
                                              functions.truncate(sell_price, 4), sell_rub, p_p[1]),
                                          cid, mid, reply_markup=keyb, parse_mode='markdown')
                except:
                    pass
            elif call.data == 'buy_p1':
                try:
                    sql__base.sqlupdate("UPDATE status SET status='0'")
                    p_p = sql__base.sqlrequest("SELECT p_buy, p_sell FROM status")
                    p_buy = functions.truncate(float(p_p[0]), 1) - 0.1
                    sql__base.sqlupdate("UPDATE status SET p_buy='" + str(p_buy) + "'")

                    r = requests.get(url=const.btc1001)
                    pp = sql__base.sqlrequest("SELECT pbuy, psell FROM status")
                    pbuy_price = functions.truncate(functions.buy_price(), 4)
                    psell_price = functions.truncate(functions.sell_price(), 4)
                    pbuy_rub = functions.truncate(pbuy_price * functions.usd_rate('RUB'), 4)
                    psell_rub = functions.truncate(psell_price * functions.usd_rate('RUB'), 4)
                    buy_price = (float(r.json()['bip2btc']) / 100) * (100 + p_buy)
                    sell_price = (float(r.json()['btc2bip']) / 100) * (100 + float(p_p[1]))
                    buy_rub = functions.truncate(buy_price * functions.usd_rate('RUB'), 4)
                    sell_rub = functions.truncate(sell_price * functions.usd_rate('RUB'), 4)

                    keyb = InlineKeyboardMarkup()
                    keyb.row(InlineKeyboardButton(text='☑️ Покупка', callback_data='buy'),
                             InlineKeyboardButton(text='Продажа', callback_data='sell'))
                    keyb.row(InlineKeyboardButton(text='+ 1%', callback_data='buy_p'),
                             InlineKeyboardButton(text='- 1%', callback_data='buy_m'),
                             InlineKeyboardButton(text='+ 0.1%', callback_data='buy_m1'),
                             InlineKeyboardButton(text='- 0.1%', callback_data='buy_p1'))
                    keyb.row(InlineKeyboardButton(text='Сброс до 1001', callback_data='rate_reset'),
                             InlineKeyboardButton(text='Очистить', callback_data='rate_res'),
                             InlineKeyboardButton(text='Готово', callback_data='rate_ready'))

                    bot.edit_message_text('Действующий курс:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%\n\n'
                                          'Изменяем на:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%' % (
                                              functions.truncate(pbuy_price, 4), pbuy_rub, pp[0],
                                              functions.truncate(psell_price, 4), psell_rub, pp[1],
                                              functions.truncate(buy_price, 4), buy_rub, float(p_p[0] - 0.1),
                                              functions.truncate(sell_price, 4), sell_rub, p_p[1]),
                                          cid, mid, reply_markup=keyb, parse_mode='markdown')
                except:
                    pass
            elif call.data == 'buy_m1':
                try:
                    sql__base.sqlupdate("UPDATE status SET status='0'")
                    p_p = sql__base.sqlrequest("SELECT p_buy, p_sell FROM status")
                    p_buy = functions.truncate(float(p_p[0]), 1) + 0.1
                    sql__base.sqlupdate("UPDATE status SET p_buy='" + str(p_buy) + "'")

                    r = requests.get(url=const.btc1001)
                    pp = sql__base.sqlrequest("SELECT pbuy, psell FROM status")
                    pbuy_price = functions.truncate(functions.buy_price(), 4)
                    psell_price = functions.truncate(functions.sell_price(), 4)
                    pbuy_rub = functions.truncate(pbuy_price * functions.usd_rate('RUB'), 4)
                    psell_rub = functions.truncate(psell_price * functions.usd_rate('RUB'), 4)
                    buy_price = (float(r.json()['bip2btc']) / 100) * (100 + p_buy)
                    sell_price = (float(r.json()['btc2bip']) / 100) * (100 + float(p_p[1]))
                    buy_rub = functions.truncate(buy_price * functions.usd_rate('RUB'), 4)
                    sell_rub = functions.truncate(sell_price * functions.usd_rate('RUB'), 4)

                    keyb = InlineKeyboardMarkup()
                    keyb.row(InlineKeyboardButton(text='☑️ Покупка', callback_data='buy'),
                             InlineKeyboardButton(text='Продажа', callback_data='sell'))
                    keyb.row(InlineKeyboardButton(text='+ 1%', callback_data='buy_p'),
                             InlineKeyboardButton(text='- 1%', callback_data='buy_m'),
                             InlineKeyboardButton(text='+ 0.1%', callback_data='buy_m1'),
                             InlineKeyboardButton(text='- 0.1%', callback_data='buy_p1'))
                    keyb.row(InlineKeyboardButton(text='Сброс до 1001', callback_data='rate_reset'),
                             InlineKeyboardButton(text='Очистить', callback_data='rate_res'),
                             InlineKeyboardButton(text='Готово', callback_data='rate_ready'))

                    bot.edit_message_text('Действующий курс:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%\n\n'
                                          'Изменяем на:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%' % (
                                              functions.truncate(pbuy_price, 4), pbuy_rub, pp[0],
                                              functions.truncate(psell_price, 4), psell_rub, pp[1],
                                              functions.truncate(buy_price, 4), buy_rub, float(p_p[0] + 0.1),
                                              functions.truncate(sell_price, 4), sell_rub, p_p[1]),
                                          cid, mid, reply_markup=keyb, parse_mode='markdown')
                except:
                    pass
            elif call.data == 'sell_m':
                try:
                    sql__base.sqlupdate("UPDATE status SET status='0'")
                    p_p = sql__base.sqlrequest("SELECT p_buy, p_sell FROM status")
                    p_sell = functions.truncate(float(p_p[1]), 1) - 1
                    sql__base.sqlupdate("UPDATE status SET p_sell='" + str(p_sell) + "'")

                    r = requests.get(url=const.btc1001)
                    pp = sql__base.sqlrequest("SELECT pbuy, psell FROM status")
                    pbuy_price = functions.truncate(functions.buy_price(), 4)
                    psell_price = functions.truncate(functions.sell_price(), 4)
                    pbuy_rub = functions.truncate(pbuy_price * functions.usd_rate('RUB'), 4)
                    psell_rub = functions.truncate(psell_price * functions.usd_rate('RUB'), 4)
                    buy_price = (float(r.json()['bip2btc']) / 100) * (100 + float(p_p[0]))
                    sell_price = (float(r.json()['btc2bip']) / 100) * (100 + p_sell)
                    buy_rub = functions.truncate(buy_price * functions.usd_rate('RUB'), 4)
                    sell_rub = functions.truncate(sell_price * functions.usd_rate('RUB'), 4)

                    keyb = InlineKeyboardMarkup()
                    keyb.row(InlineKeyboardButton(text='Покупка', callback_data='buy'),
                             InlineKeyboardButton(text='☑️ Продажа', callback_data='sell'))
                    keyb.row(InlineKeyboardButton(text='+ 1%', callback_data='sell_p'),
                             InlineKeyboardButton(text='- 1%', callback_data='sell_m'),
                             InlineKeyboardButton(text='+ 0.1%', callback_data='sell_m1'),
                             InlineKeyboardButton(text='- 0.1%', callback_data='sell_p1'))
                    keyb.row(InlineKeyboardButton(text='Сброс до 1001', callback_data='rate_reset'),
                             InlineKeyboardButton(text='Очистить', callback_data='rate_res'),
                             InlineKeyboardButton(text='Готово', callback_data='rate_ready'))

                    bot.edit_message_text('Действующий курс:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%\n\n'
                                          'Изменяем на:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%' % (
                                              functions.truncate(pbuy_price, 4), pbuy_rub, pp[0],
                                              functions.truncate(psell_price, 4), psell_rub, pp[1],
                                              functions.truncate(buy_price, 4), buy_rub, p_p[0],
                                              functions.truncate(sell_price, 4), sell_rub, p_p[1] - 1),
                                          cid, mid, reply_markup=keyb, parse_mode='markdown')
                except:
                    pass
            elif call.data == 'sell_p':
                try:
                    sql__base.sqlupdate("UPDATE status SET status='0'")
                    p_p = sql__base.sqlrequest("SELECT p_buy, p_sell FROM status")
                    p_sell = functions.truncate(float(p_p[1]), 1) + 1
                    sql__base.sqlupdate("UPDATE status SET p_sell='" + str(p_sell) + "'")

                    r = requests.get(url=const.btc1001)
                    pp = sql__base.sqlrequest("SELECT pbuy, psell FROM status")
                    pbuy_price = functions.truncate(functions.buy_price(), 4)
                    psell_price = functions.truncate(functions.sell_price(), 4)
                    pbuy_rub = functions.truncate(pbuy_price * functions.usd_rate('RUB'), 4)
                    psell_rub = functions.truncate(psell_price * functions.usd_rate('RUB'), 4)
                    buy_price = (float(r.json()['bip2btc']) / 100) * (100 + float(p_p[0]))
                    sell_price = (float(r.json()['btc2bip']) / 100) * (100 + p_sell)
                    buy_rub = functions.truncate(buy_price * functions.usd_rate('RUB'), 4)
                    sell_rub = functions.truncate(sell_price * functions.usd_rate('RUB'), 4)

                    keyb = InlineKeyboardMarkup()
                    keyb.row(InlineKeyboardButton(text='Покупка', callback_data='buy'),
                             InlineKeyboardButton(text='☑️ Продажа', callback_data='sell'))
                    keyb.row(InlineKeyboardButton(text='+ 1%', callback_data='sell_p'),
                             InlineKeyboardButton(text='- 1%', callback_data='sell_m'),
                             InlineKeyboardButton(text='+ 0.1%', callback_data='sell_m1'),
                             InlineKeyboardButton(text='- 0.1%', callback_data='sell_p1'))
                    keyb.row(InlineKeyboardButton(text='Сброс до 1001', callback_data='rate_reset'),
                             InlineKeyboardButton(text='Очистить', callback_data='rate_res'),
                             InlineKeyboardButton(text='Готово', callback_data='rate_ready'))

                    bot.edit_message_text('Действующий курс:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%\n\n'
                                          'Изменяем на:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%' % (
                                              functions.truncate(pbuy_price, 4), pbuy_rub, pp[0],
                                              functions.truncate(psell_price, 4), psell_rub, pp[1],
                                              functions.truncate(buy_price, 4), buy_rub, p_p[0],
                                              functions.truncate(sell_price, 4), sell_rub, p_p[1] + 1),
                                          cid, mid, reply_markup=keyb, parse_mode='markdown')
                except:
                    pass
            elif call.data == 'sell_m1':
                try:
                    sql__base.sqlupdate("UPDATE status SET status='0'")
                    p_p = sql__base.sqlrequest("SELECT p_buy, p_sell FROM status")
                    p_sell = functions.truncate(float(p_p[1]), 1) + 0.1
                    sql__base.sqlupdate("UPDATE status SET p_sell='" + str(p_sell) + "'")

                    r = requests.get(url=const.btc1001)
                    pp = sql__base.sqlrequest("SELECT pbuy, psell FROM status")
                    pbuy_price = functions.truncate(functions.buy_price(), 4)
                    psell_price = functions.truncate(functions.sell_price(), 4)
                    pbuy_rub = functions.truncate(pbuy_price * functions.usd_rate('RUB'), 4)
                    psell_rub = functions.truncate(psell_price * functions.usd_rate('RUB'), 4)
                    buy_price = (float(r.json()['bip2btc']) / 100) * (100 + float(p_p[0]))
                    sell_price = (float(r.json()['btc2bip']) / 100) * (100 + p_sell)
                    buy_rub = functions.truncate(buy_price * functions.usd_rate('RUB'), 4)
                    sell_rub = functions.truncate(sell_price * functions.usd_rate('RUB'), 4)

                    keyb = InlineKeyboardMarkup()
                    keyb.row(InlineKeyboardButton(text='Покупка', callback_data='buy'),
                             InlineKeyboardButton(text='☑️ Продажа', callback_data='sell'))
                    keyb.row(InlineKeyboardButton(text='+ 1%', callback_data='sell_p'),
                             InlineKeyboardButton(text='- 1%', callback_data='sell_m'),
                             InlineKeyboardButton(text='+ 0.1%', callback_data='sell_m1'),
                             InlineKeyboardButton(text='- 0.1%', callback_data='sell_p1'))
                    keyb.row(InlineKeyboardButton(text='Сброс до 1001', callback_data='rate_reset'),
                             InlineKeyboardButton(text='Очистить', callback_data='rate_res'),
                             InlineKeyboardButton(text='Готово', callback_data='rate_ready'))

                    bot.edit_message_text('Действующий курс:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%\n\n'
                                          'Изменяем на:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%' % (
                                              functions.truncate(pbuy_price, 4), pbuy_rub, pp[0],
                                              functions.truncate(psell_price, 4), psell_rub, pp[1],
                                              functions.truncate(buy_price, 4), buy_rub, p_p[0],
                                              functions.truncate(sell_price, 4), sell_rub, p_p[1] + 0.1),
                                          cid, mid, reply_markup=keyb, parse_mode='markdown')
                except:
                    pass
            elif call.data == 'sell_p1':
                try:
                    sql__base.sqlupdate("UPDATE status SET status='0'")
                    p_p = sql__base.sqlrequest("SELECT p_buy, p_sell FROM status")
                    p_sell = functions.truncate(float(p_p[1]), 1) - 0.1
                    sql__base.sqlupdate("UPDATE status SET p_sell='" + str(p_sell) + "'")

                    r = requests.get(url=const.btc1001)
                    pp = sql__base.sqlrequest("SELECT pbuy, psell FROM status")
                    pbuy_price = functions.truncate(functions.buy_price(), 4)
                    psell_price = functions.truncate(functions.sell_price(), 4)
                    pbuy_rub = functions.truncate(pbuy_price * functions.usd_rate('RUB'), 4)
                    psell_rub = functions.truncate(psell_price * functions.usd_rate('RUB'), 4)
                    buy_price = (float(r.json()['bip2btc']) / 100) * (100 + float(p_p[0]))
                    sell_price = (float(r.json()['btc2bip']) / 100) * (100 + p_sell)
                    buy_rub = functions.truncate(buy_price * functions.usd_rate('RUB'), 4)
                    sell_rub = functions.truncate(sell_price * functions.usd_rate('RUB'), 4)

                    keyb = InlineKeyboardMarkup()
                    keyb.row(InlineKeyboardButton(text='Покупка', callback_data='buy'),
                             InlineKeyboardButton(text='☑️ Продажа', callback_data='sell'))
                    keyb.row(InlineKeyboardButton(text='+ 1%', callback_data='sell_p'),
                             InlineKeyboardButton(text='- 1%', callback_data='sell_m'),
                             InlineKeyboardButton(text='+ 0.1%', callback_data='sell_m1'),
                             InlineKeyboardButton(text='- 0.1%', callback_data='sell_p1'))
                    keyb.row(InlineKeyboardButton(text='Сброс до 1001', callback_data='rate_reset'),
                             InlineKeyboardButton(text='Очистить', callback_data='rate_res'),
                             InlineKeyboardButton(text='Готово', callback_data='rate_ready'))

                    bot.edit_message_text('Действующий курс:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%\n\n'
                                          'Изменяем на:\n'
                                          '📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                          '📉 *Продажа:* $%s (%s RUB) %s%%' % (
                                              functions.truncate(pbuy_price, 4), pbuy_rub, pp[0],
                                              functions.truncate(psell_price, 4), psell_rub, pp[1],
                                              functions.truncate(buy_price, 4), buy_rub, p_p[0],
                                              functions.truncate(sell_price, 4), sell_rub, p_p[1] - 0.1),
                                          cid, mid, reply_markup=keyb, parse_mode='markdown')
                except:
                    pass
            elif call.data == 'rate_ready':
                pp = sql__base.sqlrequest("SELECT p_sell, p_buy FROM status")
                sql__base.sqlupdate(
                    "UPDATE status SET status='1', psell='" + str(pp[0]) + "', pbuy='" + str(pp[1]) + "'")

                buy_rub = functions.truncate(functions.buy_price() * functions.usd_rate('RUB'), 4)
                sell_rub = functions.truncate(functions.sell_price() * functions.usd_rate('RUB'), 4)
                sell_price = functions.truncate(functions.sell_price(), 4)
                buy_price = functions.truncate(functions.buy_price(), 4)

                keyb = InlineKeyboardMarkup()
                keyb.row(InlineKeyboardButton(text='Покупка', callback_data='buy'),
                         InlineKeyboardButton(text='Продажа', callback_data='sell'))
                keyb.row(InlineKeyboardButton(text='+ 1%', callback_data='pass'),
                         InlineKeyboardButton(text='- 1%', callback_data='pass'),
                         InlineKeyboardButton(text='+ 0.1%', callback_data='pass'),
                         InlineKeyboardButton(text='- 0.1%', callback_data='pass'))
                keyb.row(InlineKeyboardButton(text='Сброс до 1001', callback_data='rate_reset'),
                         InlineKeyboardButton(text='Очистить', callback_data='rate_res'),
                         InlineKeyboardButton(text='Готово', callback_data='rate_ready'))

                bot.edit_message_text('📈 *Покупка:* $%s (%s RUB) %s%%\n'
                                      '📉 *Продажа:* $%s (%s RUB) %s%%\n' % (
                                          functions.truncate(buy_price, 4), buy_rub, pp[1],
                                          functions.truncate(sell_price, 4), sell_rub, pp[0]),
                                      cid, mid, reply_markup=keyb, parse_mode='markdown')
            elif call.data == 'ref':
                keyb = InlineKeyboardMarkup()
                keyb.add(InlineKeyboardButton(text='Назад', callback_data='stats'))

                refs = str(*sql_base.sqlrequest("SELECT COUNT(*) FROM refs"))

                bot.edit_message_text('👥 *Участники реф. системы:* %s\n'
                                      '*Кол-во участников 1 уровня:* 10000\n'
                                      '*Кол-во участников 2 уровня:* 5000\n'
                                      '*Кол-во участников 3 уровня:* 3000\n\n'
                                      '💎 *Заработано участниками:* 1800 BIP\n'
                                      '*Выплаты для 1 уровня:* 1000 BIP\n'
                                      '*Выплаты для 2 уровня:* 500 BIP\n'
                                      '*Выплаты для 3 уровня:* 300 BIP\n' % refs, cid, mid,
                                      parse_mode='markdown', reply_markup=keyb)
            elif call.data == 'users':
                users = str(*sql_base.sqlrequest("SELECT COUNT(*) FROM users"))
                blocked = str(*sql_base.sqlrequest("SELECT COUNT(*) FROM users WHERE status='blocked'"))

                keyb = InlineKeyboardMarkup()
                keyb.add(InlineKeyboardButton(text='Назад', callback_data='stats'))

                bot.edit_message_text('👥 *Количество пользователей:* %s\n'
                                      '🚫 *Заблокировали бота:* %s\n'
                                      '🆓 *Счетов открыто:* 100\n'
                                      'Ⓜ️ *Собственные кошельки:* 100' % (users, blocked), cid, mid,
                                      parse_mode='markdown', reply_markup=keyb)
            elif call.data == 'finance':
                bot.edit_message_text('Карточка Статистика финансов', cid, mid)
            elif call.data == 'partners':
                one = sql_base.sqlrequestall("SELECT tid FROM refs WHERE from_ref='" + str(tid) + "'")
                one_len = len(one)
                two = []
                for i in one:
                    tid_ref = sql_base.sqlrequestall("SELECT tid FROM refs WHERE from_ref='" + str(*i) + "'")
                    if tid_ref:
                        for i in tid_ref:
                            two.append(str(*i))
                two_len = len(two)
                three = []
                for i in two:
                    al_ll = sql_base.sqlrequestall("SELECT tid FROM refs WHERE from_ref='" + i + "'")
                    if al_ll:
                        for i in al_ll:
                            three.append(str(*i))
                three_len = len(three)

                keyb = InlineKeyboardMarkup()
                keyb.add(InlineKeyboardButton(text='Назад', callback_data='back_cabinet'),
                         InlineKeyboardButton(text='Поделиться', switch_inline_query=''))

                bot.edit_message_text('Приглашая партнеров, Вы получаете пассивный доход с их обмена.'
                                      'Партнерская программа бессрочна, не имеет лимита приглашений и начинает '
                                      'действовать моментально.\n\n'
                                      '🤝 *Приглашённые Вами партнёры:*\n\n'
                                      '*Уровень 1:* %s - Вы получаете *0.25%%*\n'
                                      '*Уровень 2:* %s - Вы получаете *0.15%%*\n'
                                      '*Уровень 3:* %s - Вы получаете *0.1%%*\n\n'
                                      '*Ваша ссылка для приглашения партнёров:* '
                                      't.me/OceanBankBot?start=ref%s' % (one_len, two_len, three_len, tid),
                                      cid, mid, parse_mode='markdown', reply_markup=keyb, disable_web_page_preview=True)
            elif call.data == 'back_cabinet':
                cabi = modules_old.cab(tid)

                bot.edit_message_text(cabi[0], cid, mid,
                                      reply_markup=cabi[1], parse_mode='markdown', disable_web_page_preview=True)
            elif call.data == 'my':
                modules_old.Modules(call).my()
            elif call.data == 'address_new':
                a = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
                keyb = InlineKeyboardMarkup()
                keyb.add(*[InlineKeyboardButton(text=name, callback_data='new_' + name) for name in a])
                keyb.add(InlineKeyboardButton(text='Отмена', callback_data='new_cancel'),
                         InlineKeyboardButton(text='0', callback_data='new_0_0'),
                         InlineKeyboardButton(text='Очистить', callback_data='new_clean'))
                bot.edit_message_text('🔐 *Установите PIN-код для вашего счета*\n\n'
                                      '*PIN:* ○○○○', cid, mid,
                                      parse_mode='markdown', reply_markup=keyb)
            elif call.data[:3] == 'new':
                verify = pin_new(call)
                if verify is not None:
                    if verify[0] == 1:
                        info = sql_base.sqlrequest(
                            "SELECT addresses, mnemonics FROM users WHERE tid='" + str(tid) + "'")
                        sql_base.sqlupdate("UPDATE users SET addresses='" + str(info[0]) + ',' +
                                           str(verify[1]) + "', mnemonics='" + str(info[1]) + ',' +
                                           str(verify[2]) + "' WHERE tid='" + str(tid) + "'")

                        bot.edit_message_text('✅ Счет открыт и защищен!', cid, mid)
            elif call.data == 'qiwi_on':
                sql_base.sqlupdate("UPDATE status SET qiwi='1'")
                adm = admin()
                bot.edit_message_text(adm[0], cid, mid, reply_markup=adm[1])
            elif call.data == 'qiwi_off':
                sql_base.sqlupdate("UPDATE status SET qiwi='0'")
                adm = admin()
                bot.edit_message_text(adm[0], cid, mid, reply_markup=adm[1])
            elif data[:5] == 'send_':
                address = data[5:]
                sql_base.sqlupdate(
                    "INSERT INTO history (tid, wallet, type, status, date) VALUES ('" + str(tid) + "', '"
                    + str(address) + "', 'send', 'wait', CURRENT_TIMESTAMP)")
                keyb = InlineKeyboardMarkup(row_width=2)
                # keyb.add(InlineKeyboardButton(text='Telegram', callback_data='telegram'),
                #          InlineKeyboardButton(text='Minter', callback_data='minter'),
                #          InlineKeyboardButton(text='Назад', callback_data='back_cabinet'),
                #          InlineKeyboardButton(text='Номер телефона', callback_data='number'))
                keyb.add(InlineKeyboardButton(text='Minter', callback_data='minter'),
                         InlineKeyboardButton(text='Telegram', callback_data='telegram'),
                         InlineKeyboardButton(text='Назад', callback_data='back_cabinet'))
                bot.edit_message_text('Выберите действие', cid, mid,
                                      parse_mode='markdown', reply_markup=keyb)
            elif data == 'minter':
                id = str(*sql_base.sqlrequest(
                    "SELECT id FROM history WHERE tid='" + str(tid) + "' AND type='send' ORDER by id DESC"))
                sql_base.sqlupdate("UPDATE history SET type='" + data + "' WHERE id='" + id + "'")
                msg = bot.edit_message_text('На какой кошелек отправим?', cid, mid)
                bot.register_next_step_handler(msg, send_coin, 'minter')
            elif data == 'telegram':
                id = str(*sql_base.sqlrequest(
                    "SELECT id FROM history WHERE tid='" + str(tid) + "' AND type='send' ORDER by id DESC"))
                sql_base.sqlupdate("UPDATE history SET type='" + data + "' WHERE id='" + id + "'")
                msg = bot.edit_message_text('Перешлите сообщение от пользователя, которому '
                                            'хотите отправить монеты', cid, mid)
                bot.register_next_step_handler(msg, send_coin, 'telegram')
            elif data == 'cbt':
                cbt = int(*sql_base.sqlrequest("SELECT cbt FROM status"))
                if cbt == 1:
                    sql_base.sqlupdate("UPDATE status SET cbt='0'")
                    bot.send_message(-1001386519148, 'Бот переведен в режим А-тестов')
                elif cbt == 0:
                    sql_base.sqlupdate("UPDATE status SET cbt='1'")
                    bot.send_message(-1001386519148, 'Бот переведен в режим Б-тестов')
            elif call.data == 'transfer':
                keyboard = InlineKeyboardMarkup(row_width=2)
                keyboard.add(InlineKeyboardButton(text='Платежи', callback_data='pays'),
                             InlineKeyboardButton(text='☑️ Переводы', callback_data='transfer'))
                keyboard.add(InlineKeyboardButton(text='Minter', callback_data='minter'),
                             InlineKeyboardButton(text='Telegram', callback_data='telegram'))
                bot.edit_message_text('💳 *Платежи и переводы*', cid, mid, reply_markup=keyboard, parse_mode='markdown')
            elif call.data == 'pays':
                keyboard = InlineKeyboardMarkup(row_width=2)
                keyboard.add(InlineKeyboardButton(text='☑️ Платежи', callback_data='pays'),
                             InlineKeyboardButton(text='Переводы', callback_data='transfer'))
                keyboard.add(InlineKeyboardButton(text='Мобильная связь', callback_data='mobile'))
                bot.edit_message_text('💳 *Платежи и переводы*', cid, mid, reply_markup=keyboard, parse_mode='markdown')


@bot.inline_handler(func=lambda query: len(query.query) >= 0)
def query_text(query):
    tid = query.from_user.id

    if len(query.query) == 0:
        ref = types.InlineQueryResultArticle(
            id='1', title='Порекомендовать банк', description='С Вашей персональной ссылкой',
            thumb_url='https://i.ibb.co/S6NvYmf/photo-2019-11-24-19-54-07.jpg',
            input_message_content=types.InputTextMessageContent(
                message_text='🌊 [OceanBank](t.me/OceanBankBot?start=ref%s) — Платежи любыми монетами Minter. '
                             'Выгодный обмен. Продвинутое управление кошельком. Первый криптобанк '
                             'Minter.Network.' % (str(tid)),
                parse_mode='markdown', disable_web_page_preview=True))
        bot.answer_inline_query(query.id, [ref], cache_time=1)
    elif query.query[:7] == 'receipt':
        if len(query.query) > 8:
            i_d = str(query.query[8:])

            a_ll = sql_base.sqlrequest("SELECT * FROM history WHERE id='" + i_d + "'")
            if a_ll is not None:
                if str(a_ll[1]) == str(tid) and a_ll[6] == 'done':
                    share = types.InlineQueryResultArticle(
                        id='1', title='Чек по операции №000' + i_d,
                        description='Сотовая связь\n%s %s' % (a_ll[5], a_ll[8]),
                        thumb_url='https://i.ibb.co/S6NvYmf/photo-2019-11-24-19-54-07.jpg',
                        input_message_content=types.InputTextMessageContent(
                            message_text=modules_old.receipt(i_d),
                            parse_mode='markdown', disable_web_page_preview=True))
                    bot.answer_inline_query(query.id, [share], cache_time=1)
        elif query.query == 'receipt':
            a_ll = sql_base.sqlrequestall("SELECT * FROM history WHERE tid='" + str(tid) + "' and status='done'")
            a = 1
            results = []
            for i in a_ll:
                share = types.InlineQueryResultArticle(
                    id=str(a), title='Чек по операции №000' + str(i[0]),
                    description='Сотовая связь\n%s %s' % (i[5], i[8]),
                    thumb_url='https://i.ibb.co/S6NvYmf/photo-2019-11-24-19-54-07.jpg',
                    input_message_content=types.InputTextMessageContent(
                        message_text=modules_old.receipt(str(i[0])),
                        parse_mode='markdown', disable_web_page_preview=True))
                results.append(share)
                a += 1
            bot.answer_inline_query(query.id, results, cache_time=1)


if __name__ == '__main__':
    bot.delete_webhook()
    bot.polling(none_stop=True)
