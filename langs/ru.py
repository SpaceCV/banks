ref1 = 'Вы уже были зарегистрированы в реферальной программе'
ref2 = 'Вы не можете пройти по реферальной программе от самого себя'
ref3 = 'Вы уже зарегистрированный пользователь Ocean Bank'

start1 = 'Русский'
start2 = 'Выберите язык / Choose language'

cu1 = 'Выберите валюту'
cu2 = 'Валюта успешно изменена на '

keyboard1 = 'Кабинет'
keyboard2 = 'Платежи'
keyboard3 = 'История'

main = ['Платежи', 'Кабинет', 'История', 'Обмен']

Mx1 = '👉 *Выберите действие*'
Mx2 = '🚫 Сменить пин'
Mx3 = '🚫 Закрыть счет'
Mx5 = 'Сделать основным'
Mx6 = 'Переименовать счет'
Mx7 = '💼 *Основной счет*'

name = '✏️ Введите название для счета'

choose = 'Счет {0} выбран основным'

mobile1 = '💼 *Выберите счет для оплаты*'
mobile2 = 'Ввести номер телефона'
mobile3 = '📱 *Выберите номер телефона или введите новый*'

input_number = '📱 *Номер телефона*\n\n' \
               '*Доступно:* Россия, Казахстан\n' \
               '*Формат:* +79991234567'

read = 'Прочитал'

pin_read = '*Что такое ПИН-код и зачем он нужен?*\n\n' \
           'ПИН-код – это секретный защитный код счета из 4х цифр. Он шифрует seed-фразу и ' \
           'таким образом никто не имеет доступа к счету, а также понадобится при ' \
           'платежных операциях\n' \
           'Придумайте собственный ПИН-код, который вы точно не забудете!'

clean = 'Очистить'
cancel = 'Отмена'
back = 'Назад'
share = 'Поделиться'
ready = 'Готово'

ms01 = '[{0}](https://minterscan.net/address/{1})'

wallet1 = '*Со счёта:* ' + ms01 + ' ({2})\n'
wallet2 = '*Со счёта:* ' + ms01 + '\n'

pin = '🔐 *Установите PIN-код для вашего счета*\n\n' \
      '*PIN:* ○○○○'

pin_verify = '✅ Счет создан и защищен!'

deposit = 'Переведите монеты на этот кошелек:'

pay1 = '🕑 Подождите... Операция выполняется'
pay2 = '✅ Оплата прошла успешно!'
pay3 = '🚫 Сервис временно недоступен'
pay4 = '🚫 Сервис временно недоступен'
pay5 = '❌ Оплата не прошла'

summ_pin = '🔐 *PIN для подтверждения*\n' \
           '💼 ' + ms01 + '\n\n' \
                        '*PIN:* ○○○○'

history2 = '🚫 Повторить'
history3 = '🚫 Автоплатеж'
history4 = 'Вы не совершали никаких операций.'
history5 = 'Сотовая связь'
history6 = '🧾 *История операций*'

partners = 'Приглашая партнеров, Вы получаете пассивный доход с их обмена. ' \
           'Партнерская программа бессрочна, не имеет лимита приглашений и начинает действовать моментально.\n\n' \
           '🤝 *Приглашённые Вами партнёры:*\n\n' \
           '*Уровень 1:* {0} - Вы получаете *0.25%*\n' \
           '*Уровень 2:* {1} - Вы получаете *0.15%*\n' \
           '*Уровень 3:* {2} - Вы получаете *0.1%*\n\n' \
           '*Ваша ссылка для приглашения партнёров:* ' \
           't.me/OceanBankBot?start=ref{3}'

my = '💼 *Выберите счет*'

address_new = '🔐 *Установите PIN-код для вашего счета*\n\n' \
              '*PIN:* ○○○○'
ver_add_new = '✅ Счет открыт и защищен!'

send1 = 'Выберите действие'
send2 = 'Сколько перешлем?'
send3 = 'Этот пользователь не зарегистрирован. Но мы можем создать чек и он будет автоматически активирован,' \
        ' когда пользователь зарегистрируется. Согласны?'
send4 = 'Я не могу принять это сообщение'
send7 = 'Оплата монетой: BIP'
send8 = '💸 *Сумма отправки*\n\n' \
        '*Мин. сумма:* 1 BIP ({0} {1})\n' \
        '*Макс. сумма:* {2} BIP ({3} {4})\n' \
        '*Комиссия:* 0.01 BIP\n\n' \
        '📲 *Пополнение телефона*\n\n' \
        '{5}' \
        '*Номер телефона:* {6}\n' \
        '*Итого сумма:* 0 {7} (0 {8})\n\n' \
        '*Ввод:* 0 BIP'
minter = 'На какой кошелек отправим?'
telegram = 'Перешлите сообщение от пользователя, которому хотите отправить монеты'

cbt0 = 'Бот переведен в режим Б-тестов'
cbt1 = 'Бот переведен в режим А-тестов'

inline1 = 'Порекомендовать банк'
inline2 = 'С Вашей персональной ссылкой'
inline3 = '🌊 [OceanBank](t.me/OceanBankBot?start=ref{0}) — Платежи любыми монетами Minter. ' \
          'Выгодный обмен. Продвинутое управление кошельком. Первый криптобанк ' \
          'Minter.Network.'
inline4 = 'Чек по операции №000'
inline5 = 'Сотовая связь\n{0} {1)'

rc012 = '*Сумма списания:* {0} {1} ({2} '
receipt1 = rc012 + 'BIP) ({3} {4})'
receipt2 = rc012 + '{3})'
receipt3 = ms01 + ' ({2})'
receipt4 = '✅ *Выполнено!* №000{0}\n\n' \
           '*Операция совершена:* {1} \n' \
           '*Счет списания:* {2}\n\n' \
           '*Счет зачисления:* {3}\n' \
           '*Описание:* Сотовая связь\n' \
           '{4}\n' \
           '*Комиссия:* {5} BIP'
receipt5 = '0.01'
receipt6 = '0.11'

pays1 = 'Мобильная связь'
pays2 = '💳 *Платежи и переводы*'
pays3 = '☑️ Платежи'
pays4 = 'Платежи'
pays5 = 'Переводы'
pays6 = '☑️ Переводы'
pays7 = 'Minter'
pays8 = 'Telegram'

cab1 = '📥 Пополнить'
cab2 = '📤 Перевести'
cab3 = 'Партнеры'
cab4 = 'Мои счета'
cab5 = 'Новый счет'
cab6 = '      • *{0}* {1} ({2} {3})\n'
cab7 = '*Счет:* ' + ms01 + ' ({2})\n'
cab8 = '*Счет:* ' + ms01 + '\n'
cab9 = '*Курс Банка*\n' \
       '📈 Покупка: ${0} ({1} {2})\n' \
       '📉 Продажа: ${3} ({4} {5})\n\n' \
       '{6}' \
       '*Баланс:* \n{7}' \
       '*Заработано:* 0\n'

number1 = 'Введенный номер не верен'
number2 = 'Возможно мы не поддерживаем этот номер, но вы можете помочь нам. Добавьтесь в этот чат и мы попробуем ' \
          'подключить ваш номер. https://t.me/joinchat/BqUygxQFE7MexVzRxZ5j2g'

ks1 = 'Оплата монетой: '
ks2 = '💸 *Сумма пополнения*\n\n' \
      '*Мин. сумма:* 10 BIP ({0} {1})\n' \
      '*Макс. сумма:* {2} BIP ({3} {4})\n' \
      '*Комиссия:* 0.01 BIP\n\n' \
      '📲 *Пополнение телефона*\n\n' \
      '{5}' \
      '*Номер телефона:* {6}\n' \
      '*Итого сумма:* 0 {7} (0 {8})\n\n' \
      '*Ввод:* 0 BIP'

start_cmd = '*Курс Банка*\n' \
            '📈 Покупка: ${0} ({1} {2})\n' \
            '📉 Продажа: ${3} ({4} {5})'

name_wal = '✅ Название присвоено!'

pin_set1 = '🔐 *Установите PIN-код для вашего счета*\n\n' \
           '*PIN:* '
pin_set2 = '🔐 *Установите PIN-код для вашего счета*\n\n' \
           '*PIN:* ○○○○'
pin_set3 = 'Очищено'