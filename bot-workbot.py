#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This is a simple echo bot using decorators and webhook with flask
# It echoes any incoming text messages and does not use the polling method.

import os
import flask
import telebot
from flask import Flask, request


API_TOKEN = '203989615:AAHTsB7KnVtPRNOZmMDSXJeomp6BgN-MDKM'

#WEBHOOK_HOST = 'coffee-bot-jashilko.c9users.io'
WEBHOOK_HOST = 'cofbot.herokuapp.com'
WEBHOOK_PORT = 80  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr

#WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
#WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Path to the ssl private key

# Quick'n'dirty SSL certificate generation:
#
# openssl genrsa -out webhook_pkey.pem 2048
# openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
#
# When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# with the same value in you put in WEBHOOK_HOST

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (API_TOKEN)


bot = telebot.TeleBot(API_TOKEN)

app = flask.Flask(__name__)


# Empty webserver index, return nothing, just http 200
@app.route('/', methods=['GET', 'HEAD'])
def index():
    return 'w'


# Process webhook calls
@app.route("/bot", methods=['POST'])
def getMessage():
    # Чтение данных от серверов telegram
    bot.process_new_messages(
        [telebot.types.Update.de_json(request.stream.read().decode("utf-8")).message
        ])
    return "!", 200


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message,
                 ("Hi there, I am EchoBot.\n"
                  "I am here to echo your kind words back to you."))


# Handle all other messages
@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    bot.reply_to(message, message.text)


# Remove webhook, it fails sometimes the set if there is a previous webhook
#bot.remove_webhook()

# Set webhook
#bot.set_webhook(url=WEBHOOK_URL_BASE+WEBHOOK_URL_PATH)

# Start flask server
app.run(host="0.0.0.0", port=os.environ.get('PORT', 5000))