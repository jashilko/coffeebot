# -*- coding: utf-8 -*-

import shelve
import config
import telebot
from telebot import types
import re
from config import shelve_name

bot = telebot.TeleBot(config.token)

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    markup = generate_markup('1')
    bot.send_message(message.chat.id, 'Привет. Я - бот "Кофе и Пончики", тут ты можешь заказать кофе. Просто нажми кнопку Заказ и напиши, какой кофе и когда хочешь', reply_markup=markup)


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])


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
        bot.send_message(message.chat.id, 'Ваш заказ готовиться: ' + get_storage(message.chat.id))
        del_storage(message.chat.id)
    elif message.text == 'Отмена!':
        markup = generate_markup('1')
        del_storage(message.chat.id)
        bot.send_message(message.chat.id, 'Вы можете оформить новый заказ: ', reply_markup=markup)

        

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
    return markup
    

bot.polling()