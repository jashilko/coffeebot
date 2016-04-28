# -*- coding: utf-8 -*-

import shelve
import config
import telebot
from telebot import types
import re
from config import shelve_name
from config import shelve_dbid
from config import barphone
from SQLighter import SQLighter
from smsc_api import *
import time


bot = telebot.TeleBot(config.token)

# Set to storage
def set_storage(name, id, mes):
    with shelve.open(name) as stor:
        if (str(id) in stor):
            stor[str(id)]= stor[str(id)] + mes
        else: stor[str(id)] = mes


# Get from storage
def get_storage(name, id):
    with shelve.open(name) as storage:
        try:
            answer = storage[str(id)]
            return answer
        # Если человек не играет, ничего не возвращаем
        except KeyError:
            return None

# Del storage
def del_storage(name, id):
    with shelve.open(name) as storage:
        if (str(id) in storage):
            del storage[str(id)]

def check_time():
    t1 = time.localtime()
    if (t1[3] < config.tbegin):
        return 1
    elif (t1[3] > config.tend):
        return 2
    else:
        return 0



# Handle '/start'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if check_time() == 0:
        markup = generate_markup('1')
        bot.send_message(message.chat.id, 'Привет, ' + message.chat.first_name +
                         '/ Я - бот "Кофе и Пончики", тут ты можешь заказать кофе. '
                         'Просто нажми кнопку Заказ и напиши, какой кофе и когда хочешь', reply_markup=markup)
    elif check_time() == 1:
        markup = types.ReplyKeyboardHide()
        bot.send_message(message.chat.id, 'Привет, ' + message.chat.first_name +
                         '. Ещё рано, мы открываемся только в ' + str(config.tbegin) + ':00', reply_markup=markup)
    elif check_time() == 2:
        markup = types.ReplyKeyboardHide()
        bot.send_message(message.chat.id, 'Привет, ' + message.chat.first_name +
                         '. Уже поздно для кофе. Мы работаем до ' + str(config.tend) + ':00', reply_markup=markup)


# Handle '/where'
@bot.message_handler(commands=['where'])
def send_venue(message):
    bot.send_message(message.chat.id, 'Адрес: г. Москва, ул. Перовская 61А. ')
    bot.send_location(message.chat.id, 55.745275, 37.797442)

# Handle '/menu'
@bot.message_handler(commands=['menu'])
def send_venue(message):
    f = open('menu.txt')
    filetostr = f.read()
    f.close()
    bot.send_message(message.chat.id, filetostr)

# Handle '/help'
@bot.message_handler(commands=['help'])
def send_venue(message):
    f = open('help.txt')
    filetostr = f.read()
    f.close()
    bot.send_message(message.chat.id, filetostr)

def end_dialog(message):
    markup = generate_markup('5')
    with shelve.open(shelve_name) as storage:

        db_worker = SQLighter(config.database_name)
        if (db_worker.get_order_string(get_storage(shelve_dbid, message.chat.id)) is not None):
            bot.send_message(message.chat.id, db_worker.get_order_string(get_storage(shelve_dbid, message.chat.id)) + '. Мы начали готовить ваш заказ. '
                                              'Если вы просто хотели протестировать как работает бот, '
                                              'нажмите кнопку "Отмена!"', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, 'Мы начали готовить ваш заказ. '
                                              'Если вы просто хотели протестировать как работает бот, '
                                              'нажмите кнопку "Отмена!"', reply_markup=markup)

    db_worker.close()

# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    db_worker = SQLighter(config.database_name)
    db_worker.set_client_phone(message.contact, message.from_user.username)
    db_worker.close()
    end_dialog(message)

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    if check_time() == 1:
        markup = types.ReplyKeyboardHide()
        bot.send_message(message.chat.id, 'Привет, ' + message.chat.first_name +
                         '. Ещё рано, мы открываемся только в ' + str(config.tbegin) + ':00', reply_markup=markup)
        return None
    elif check_time() == 2:
        markup = types.ReplyKeyboardHide()
        bot.send_message(message.chat.id, 'Привет, ' + message.chat.first_name +
                         '. Уже поздно для кофе. Мы работаем до ' + str(config.tend) + ':00', reply_markup=markup)
        return None


    db_worker = SQLighter(config.database_name)

    # Первая стадия, выбор заказа.
    if message.text == 'Капучино' or message.text == 'Латте' or message.text == 'Американо':
        # Записываем ИД запись в хранилище.
        id = db_worker.set_order(None, message.from_user.id, message.text, None, None)
        set_storage(shelve_dbid, message.chat.id, id)

        # Записываем статус 1 - товар выбран
        set_storage(shelve_name, message.chat.id, "1")

        # Выводим следующее сообщение
        markup = generate_markup('2')
        bot.send_message(message.chat.id, 'Ок, ' + message.text +  '. Какой размер?', reply_markup=markup)
    elif message.text == '*** Большой ***' or message.text == '** Средний **':
        # Апдейтим в БД объем.
        id = get_storage(shelve_dbid, message.chat.id)
        if id is not None:
            db_worker.set_order(id, message.from_user.id, None, message.text, None)

        # Записываем статус 2 - выбран объем
        set_storage(shelve_name, message.chat.id, "2")

        # Выводим следующее сообщение
        markup = generate_markup('3')
        bot.send_message(message.chat.id, 'Через сколько минут вас ждать?', reply_markup=markup)

    elif re.match(r'\d+', message.text) or message.text == 'я уже тут!':
        # Апдейтим в БД время.
        id = get_storage(shelve_dbid, message.chat.id)
        if id is not None:
            db_worker.set_order(id, message.from_user.id, None, None, message.text)

        # Записываем статус 3 - выбрано время
        set_storage(shelve_name, message.chat.id, "3")

        # Запрашиваем у клиента телефон или завершаем заказ.
        if db_worker.check_exist_client(message.from_user.id) == False:
            markup = generate_markup('4')
            bot.send_message(message.chat.id, 'Вы ещё не заказывали у нас ничего. ' +
                                              'Пришлите ваш номер телнефона. '
                                              'Звонить и спамить не будем (честно) ', reply_markup=markup)
        else:
            end_dialog(message)


        db_worker.new_client(message.from_user.id, message.chat.username, message.chat.first_name)
        #del_storage(shelve_name, message.chat.id)
        #del_storage(shelve_dbid, message.chat.id)
    elif message.text == 'Отмена!':
        markup = generate_markup('1')
        del_storage(shelve_name, message.chat.id)
        del_storage(shelve_dbid, message.chat.id)
        bot.send_message(message.chat.id, 'Вы можете оформить новый заказ: ', reply_markup=markup)
    elif message.text == 'Все в силе!':
        if (db_worker.get_order_string(get_storage(shelve_dbid, message.chat.id)) is not None):
            send_sms(db_worker.get_order_string(get_storage(shelve_dbid, message.chat.id), 1))
        del_storage(shelve_name, message.chat.id)
        del_storage(shelve_dbid, message.chat.id)
        markup = types.ReplyKeyboardHide()
        bot.send_message(message.chat.id, 'Ждем вас снова', reply_markup=markup )
    elif message.text == 'Не хочу':
        end_dialog(message)
    db_worker.close()
        

def generate_markup(what):
    markup = types.ReplyKeyboardMarkup()
    if what == '1':
        markup.row('Капучино')
        markup.row('Латте')
        markup.row('Американо')
        markup.row('Отмена!')

    elif what == '2':
        markup.row('*** Большой ***')
        markup.row('** Средний **')
        markup.row('Отмена!')
    elif what == '3':
        markup.row('5', '10', '15')
        markup.row('я уже тут!')
        markup.row('Отмена!')
    elif what == '4':
        markup.add(types.KeyboardButton('Отправить номер телефона', True))
        markup.add(types.KeyboardButton('Не хочу'))
        markup.row('Отмена!')
    elif what == '5':
        markup.row('Все в силе!')
        markup.row('Отмена!')

    return markup

def send_sms(text):
    smsc = SMSC()
    smsc.send_sms(barphone, text, sender="sms")


bot.polling()