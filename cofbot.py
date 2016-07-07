# -*- coding: utf-8 -*-

import shelve
import config
import telebot
from telebot import types
import re
from config import shelve_name
from config import shelve_dbid
from config import barphone
from PSQLighter import PSQLighter
from smsc_api import *
import time
import os
import flask
from flask import Flask, request

#Статусы заказа
Status_None = 0 #Новый заказ // Выводим список чего купить. 
Status_CoffeeChoosed = 1 # Выбрано Капучино // латте..Выводим вопрос с размером
Status_SizeChoosed = 2 # Выбран размер // Выводим вопрос со временем
Status_TimeChoose = 3 # Выбрано время // Выводим Подтверждение. 
Status_ConfirmChoose = 4 # Выбрано подтверждение // Выводим пока.
Status_OfferSandwich = 61 # Выбраны сэндвич + капучино // Выводим время.

#Настройки веб-сервера.
#WEBHOOK_HOST = 'coffee-bot-jashilko.c9users.io'
WEBHOOK_HOST = 'cofbot.herokuapp.com'
WEBHOOK_PORT = 80  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr
WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (config.token)

# Задаем имена переменных. 
bot = telebot.TeleBot(config.token)
app = flask.Flask(__name__)

# Process webhook calls
@app.route("/bot", methods=['POST'])
def getMessage():
    bot.process_new_messages(
        [telebot.types.Update.de_json(request.stream.read().decode("utf-8")).message
        ])
    return "!", 200

# Set to storage with name
def set_storage(name, id, mes):
    with shelve.open(name) as stor:
        stor[str(id)] = mes
        
# Записываем статус в хранилище.       
def set_storage_orderstat(id, mes):
    with shelve.open(shelve_name) as stor:
        stor[str(id)] = mes


# Получаем данные из хранилища name
def get_storage(name, id):
    with shelve.open(name) as storage:
        try:
            answer = storage[str(id)]
            return answer
        # Если человек не играет, ничего не возвращаем
        except KeyError:
            return None

# Удаляем данные из хранилища
def del_storage(name, id):
    with shelve.open(name) as storage:
        if (str(id) in storage):
            del storage[str(id)]

# Проверяем время (рано или поздно для работы бота)
def check_time():
    t1 = time.localtime()
    if (t1[3] < config.tbegin):
        return 0
    elif (t1[3] > config.tend):
        return 0
    else:
        return 0


# Handle '/start'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if check_time() == 0:
        # Записываем статус заказа 0 - начали общение
        set_storage_orderstat(message.chat.id, Status_None)
        
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
    try:
        bot.send_message(message.chat.id, 'Адрес: г. Москва, ул. Перовская 61А. ')
        bot.send_location(message.chat.id, 55.745275, 37.797442)
    except Exception as e:
        print("Ошибка commands=where : %s" %str(e))    

# Handle '/menu'
@bot.message_handler(commands=['menu'])
def send_menu(message):
    try:
        f = open('menu.txt')
        filetostr = f.read()
        f.close()
        bot.send_message(message.chat.id, filetostr)
    except Exception as e:
        print("Ошибка commands=menu : %s" %str(e))    
        
# Handle '/help'
@bot.message_handler(commands=['help'])
def send_help(message):
    try:
        f = open('help.txt')
        filetostr = f.read()
        f.close()
        bot.send_message(message.chat.id, filetostr)
    except Exception as e:
        print("Ошибка commands=help : %s" %str(e))      
        
# Завершаем заказ. 
def end_dialog(message):
    try:
        markup = generate_markup('5')
        with shelve.open(shelve_name) as storage:
            db_worker = PSQLighter()
            if (db_worker.get_order_string(get_storage(shelve_dbid, message.chat.id)) is not None):
                bot.send_message(message.chat.id, db_worker.get_order_string(get_storage(shelve_dbid, message.chat.id)) + '. Мы начали готовить ваш заказ. '
                                                  'Если вы просто хотели протестировать как работает бот, '
                                                  'нажмите кнопку "Отмена!"', reply_markup=markup)
            else:
                bot.send_message(message.chat.id, 'Мы начали готовить ваш заказ. '
                                                  'Если вы просто хотели протестировать как работает бот, '
                                                  'нажмите кнопку "Отмена!"', reply_markup=markup)
    except Exception as e:
        print("Ошибка end_dialog : %s" %str(e))      

# Handle type Contact
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    try:
        db_worker = PSQLighter()
        db_worker.set_client_phone(message.contact, message.from_user.username)
        db_worker.close()
        end_dialog(message)
    except Exception as e:
        print("Ошибка type=contact : %s" %str(e))            

# Обработка любого присланного текста
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

    db_worker = PSQLighter()

    #Получаем статус заказа. 
    idstatus = get_storage(shelve_name, message.chat.id)
    if idstatus is not None:
        print ("Begin status - " + str(idstatus))
    
    # Проверяем, не нажал ли пользователь "Отмену!"
    if message.text == 'Отмена!':
        try:
            markup = generate_markup('1')
            # Удаляем запись в БД, записи в обоих хранилищах.
            if (get_storage(shelve_dbid, message.chat.id) is not None):
                db_worker.del_order(int(get_storage(shelve_dbid, message.chat.id)))
            del_storage(shelve_name, message.chat.id)
            set_storage_orderstat(message.chat.id, Status_None)
            del_storage(shelve_dbid, message.chat.id)
            bot.send_message(message.chat.id, 'Вы можете оформить новый заказ: ', reply_markup=markup)
        except Exception as e:
            print("Ошибка Отмена! : %s" %str(e))     
        
    elif message.text == 'Капучино + Сэндвич = 250':
        try:
            # Записываем ИД запись в хранилище.
            id = db_worker.set_order(None, message.from_user.id, message.text, None, None)
            set_storage(shelve_dbid, message.chat.id, id)
    
            # Записываем статус 61 - выбран сэндвич.
            set_storage_orderstat(message.chat.id, Status_OfferSandwich)
            markup = generate_markup('3')
            bot.send_message(message.chat.id, 'Через сколько минут вас ждать?', reply_markup=markup)
        except Exception as e:
            print("Ошибка Капучино + Сэндвич : %s" %str(e))     
    
    # Первая стадия, выбор заказа.
    #if message.text == 'Капучино' or message.text == 'Латте' or message.text == 'Американо':
    elif (idstatus == Status_None):
        try:
            # Записываем ИД запись в хранилище.
            message.text.encode('cp1251')
            id = db_worker.set_order(None, message.from_user.id, message.text, None, None)
            set_storage(shelve_dbid, message.chat.id, id)
            # Записываем статус 1 - товар выбран
            set_storage_orderstat(message.chat.id, Status_CoffeeChoosed)
            # Выводим следующее сообщение
            markup = generate_markup('2')
            bot.send_message(message.chat.id, 'Ок, ' + message.text +  '. Какой размер?', reply_markup=markup)
        except Exception as e:
            print("Ошибка Status_None : %s" %str(e))  
            
    #elif message.text == '*** Большой ***' or message.text == '** Средний **':
    elif idstatus == Status_CoffeeChoosed:
        try:
            # Апдейтим в БД объем.
            message.text.encode('cp1251')
            id = get_storage(shelve_dbid, message.chat.id)
            if id is not None:
                db_worker.set_order(id, message.from_user.id, None, message.text, None)
    
            # Записываем статус 2 - выбран объем
            set_storage_orderstat(message.chat.id, Status_SizeChoosed)
    
            # Выводим следующее сообщение
            markup = generate_markup('3')
            bot.send_message(message.chat.id, 'Через сколько минут вас ждать?', reply_markup=markup)
        except Exception as e:
            print("Ошибка Status_CoffeeChoosed : %s" %str(e))          

    #elif re.match(r'\d+', message.text) or message.text == 'я уже тут!':
    elif (idstatus == Status_SizeChoosed) or (idstatus == Status_OfferSandwich): 
        try:
            # Апдейтим в БД время.
            id = get_storage(shelve_dbid, message.chat.id)
            if id is not None:
                db_worker.set_order(id, message.from_user.id, None, None, message.text)
    
            # Записываем статус 3 - выбрано время
            set_storage_orderstat(message.chat.id, Status_TimeChoose)
    
            # Запрашиваем у клиента телефон или завершаем заказ.
            if db_worker.check_exist_client(message.from_user.id) == False:
                markup = generate_markup('4')
                bot.send_message(message.chat.id, 'Вы ещё не заказывали у нас ничего. ' +
                                                  'Пришлите ваш номер телнефона. '
                                                  'Звонить и спамить не будем (честно) ', reply_markup=markup)
            else:
                end_dialog(message)
        except Exception as e:
            print("Ошибка Status_SizeChoosed : %s" %str(e))    

        #db_worker.new_client(message.from_user.id, message.chat.username, message.chat.first_name)
        #del_storage(shelve_name, message.chat.id)
        #del_storage(shelve_dbid, message.chat.id)
    
    #elif message.text == 'Все в силе!':
    elif idstatus == Status_TimeChoose: 
        try:
            if (db_worker.get_order_string(get_storage(shelve_dbid, message.chat.id)) is not None):
                send_sms(db_worker.get_order_string(get_storage(shelve_dbid, message.chat.id), 1))
            print(db_worker.get_order_string(get_storage(shelve_dbid, message.chat.id), 1))
            del_storage(shelve_name, message.chat.id)
            del_storage(shelve_dbid, message.chat.id)
            markup = types.ReplyKeyboardHide()
            bot.send_message(message.chat.id, 'Ждем вас снова', reply_markup=markup )
        except Exception as e:
            print("Ошибка Status_TimeChoose : %s" %str(e))      
            
    elif message.text == 'Не хочу':
        end_dialog(message)
    db_worker.close()
    
    #Получаем статус заказа. 
    idstatus = get_storage(shelve_name, message.chat.id)
    if idstatus is not None:
        print ("End status - " + str(idstatus))

        
# Генерация меню
def generate_markup(what):
    markup = types.ReplyKeyboardMarkup()
    if what == '1':
        markup.row('Капучино', 'Латте')
        markup.row("Американо")
        markup.row('Капучино + Сэндвич = 250')
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
    


app.run(host="0.0.0.0", port=os.environ.get('PORT', 5001))