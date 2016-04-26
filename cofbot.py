# -*- coding: utf-8 -*-

import shelve
import config
import telebot
from telebot import types
import re
from config import shelve_name
from SQLighter import SQLighter

bot = telebot.TeleBot(config.token)

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start', 'order'])
def send_welcome(message):


    markup = generate_markup('1')
    bot.send_message(message.chat.id, 'Привет, ' + message.chat.first_name + '. Я - бот "Кофе и Пончики", тут ты можешь заказать кофе. Просто нажми кнопку Заказ и напиши, какой кофе и когда хочешь', reply_markup=markup)

# Handle all other messages with content_type 'text' (content_types defaults to ['text'])

@bot.message_handler(commands=['where'])
def send_venue(message):
    bot.send_message(message.chat.id, 'Адрес: г. Москва, ул. Перовская 61А. ')
    bot.send_location(message.chat.id, 55.745275, 37.797442)


def set_storage(chat, mes):
    with shelve.open(shelve_name) as stor:
        if (str(chat) in stor):
            stor[str(chat)]= stor[str(chat)] + mes
        else: stor[str(chat)] = mes


def get_storage(chat):
    with shelve.open(shelve_name) as storage:
        try:
            answer = storage[str(chat)]
            return answer
        # Если человек не играет, ничего не возвращаем
        except KeyError:
            return None

def del_storage(id):
    with shelve.open(shelve_name) as storage:
        if (str(id) in storage):
            del storage[str(id)]

def end_dialog(message):
    markup = generate_markup('5')
    with shelve.open(shelve_name) as storage:
        if (str(message.chat.id) in storage):
            bot.send_message(message.chat.id, get_storage(message.chat.id) + '. Мы начали готовить ваш заказ. Если вы просто хотели протестировать как работает бот, нажмите кнопку "Отмена!"', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, 'Мы начали готовить ваш заказ. Если вы просто хотели протестировать как работает бот, нажмите кнопку "Отмена!"', reply_markup=markup)
    del_storage(message.chat.id)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    db_worker = SQLighter(config.database_name)
    db_worker.set_client_phone(message.contact, message.from_user.username)
    db_worker.close()
    end_dialog(message)

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    if message.text == 'Капучино' or message.text == 'Латте' or message.text == 'Американо':
        markup = generate_markup('2')
        set_storage(message.chat.id, message.text + ', ')
        bot.send_message(message.chat.id, 'Ок, ' + message.text +  '. Какой размер?', reply_markup=markup)
    elif message.text == '*** Большой ***' or message.text == '** Средний **':
        markup = generate_markup('3')
        set_storage(message.chat.id, message.text + ', ')
        bot.send_message(message.chat.id, 'Через сколько минут вас ждать?', reply_markup=markup)
    elif re.match(r'\d+', message.text) or message.text == 'я уже тут!':
        set_storage(message.chat.id, message.text)
        db_worker = SQLighter(config.database_name)
        if db_worker.check_exist_client(message.from_user.id) == False:
            markup = generate_markup('4')
            bot.send_message(message.chat.id, 'Вы ещё не заказывали у нас ничего. ' +
                                              'Пришлите ваш номер телнефона. '
                                              'Звонить и спамить не будем (честно) ', reply_markup=markup)
        else:
            end_dialog(message)

        db_worker.new_client(message.from_user.id, message.chat.username, message.chat.first_name)
        db_worker.close()
        del_storage(message.chat.id)
    elif message.text == 'Отмена!':
        markup = generate_markup('1')
        del_storage(message.chat.id)
        bot.send_message(message.chat.id, 'Вы можете оформить новый заказ: ', reply_markup=markup)
    elif message.text == 'Все в силе!':
        del_storage(message.chat.id)
        markup = types.ReplyKeyboardHide()
        bot.send_message(message.chat.id, 'Ждем вас снова', reply_markup=markup )
    elif message.text == 'Не хочу':
        end_dialog(message)

        

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



bot.polling()