#!/usr/bin/env python3
# coding: utf-8

import os
import telebot
from telebot import types
from flask import Flask, request
import threading
import time
import requests

TOKEN = "8396029873:AAHeu1coggukcGVMwCMx-nmm36VzVo7fuoo"
bot = telebot.TeleBot(TOKEN)
user_data = {}
app = Flask(__name__)

# Пингер
def keep_awake():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}.onrender.com/"
    while True:
        time.sleep(300)
        try:
            requests.get(url)
        except:
            pass
threading.Thread(target=keep_awake, daemon=True).start()

@app.route('/')
def index():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200

# Старт
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data[user_id] = {}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Начать", callback_data="go"))
    bot.send_message(message.chat.id, "*Привет!*", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id
    if call.data == "go":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Telegram", "WhatsApp")
        bot.send_message(call.message.chat.id, "*Способ связи?*", parse_mode="Markdown", reply_markup=markup)
        bot.register_next_step_handler(call.message, step1)

def step1(message):
    user_data[message.from_user.id]["method"] = message.text
    bot.send_message(message.chat.id, "*Имя?*", parse_mode="Markdown")
    bot.register_next_step_handler(message, step2)

def step2(message):
    user_data[message.from_user.id]["name"] = message.text
    bot.send_message(message.chat.id, "*Регион?* (ЕС/США)", parse_mode="Markdown")
    bot.register_next_step_handler(message, step3)

def step3(message):
    region = message.text.strip()
    if "США" in region:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Да", "Нет")
        bot.send_message(message.chat.id, "*Ты уже в США?*", parse_mode="Markdown", reply_markup=markup)
        bot.register_next_step_handler(message, step_usa)
    else:
        bot.send_message(message.chat.id, "Спасибо! Анкета отправлена.")

def step_usa(message):
    if "Да" in message.text:
        bot.send_message(message.chat.id, "Отлично! Мы свяжемся.")
    else:
        bot.send_message(message.chat.id, "Понял. Скоро поможем.")

# Webhook
def set_webhook():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}.onrender.com/webhook"
    bot.remove_webhook()
    time.sleep(2)
    bot.set_webhook(url=url)
    print(f"Webhook: {url}")

if __name__ == '__main__':
    set_webhook()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
