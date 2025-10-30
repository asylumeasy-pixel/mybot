#!/usr/bin/env python3
# coding: utf-8

import os
import csv
import telebot
from telebot import types
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request
import threading
import time
import requests
import json

# ================== НАСТРОЙКИ ==================
TOKEN = "8396029873:AAHeu1coggukcGVMwCMx-nmm36VzVo7fuoo"
ADMIN_ID = 7798853644
CSV_FILE = "ankety.csv"
GSHEET_NAME = "AsylumBotData"

# ================== GOOGLE SHEETS ==================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = os.getenv("GOOGLE_CREDENTIALS")
if creds_json:
    try:
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open(GSHEET_NAME).sheet1
    except Exception as e:
        print(f"Ошибка Google Sheets: {e}")
        sheet = None
else:
    print("GOOGLE_CREDENTIALS не найден!")
    sheet = None

# ================== БОТ ==================
bot = telebot.TeleBot(TOKEN)
user_data = {}

app = Flask(__name__)

# --- Пингер ---
def keep_awake():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}.onrender.com/"
    while True:
        time.sleep(300)
        try:
            requests.get(url, timeout=10)
            print("Пинг:", url)
        except:
            pass

threading.Thread(target=keep_awake, daemon=True).start()

@app.route('/')
def index():
    return "Bot is alive! Анкеты 24/7", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid', 403

# ================== СОХРАНЕНИЕ ==================
def save_data(data_dict):
    headers = [ ... ]  # ← оставь как есть
    # ... (тот же код save_data)

# ================== СТАРТ С КНОПКОЙ ==================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user_data[user_id] = {}

    markup = types.InlineKeyboardMarkup()
    start_btn = types.InlineKeyboardButton("Начать анкету", callback_data="start_anketa")
    markup.add(start_btn)

    bot.send_message(
        message.chat.id,
        "Привет! Я помогу подать заявку на убежище.\n\n"
        "Нажми кнопку ниже, чтобы начать:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "start_anketa")
def start_anketa(call):
    user_id = call.from_user.id
    user_data[user_id] = {}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Telegram", "WhatsApp")

    bot.send_message(
        call.message.chat.id,
        "Выбери удобный способ связи:",
        reply_markup=markup
    )
    bot.register_next_step_handler(call.message, handle_contact_method)

# ================== АВТОЛОГИН TELEGRAM ==================
def handle_contact_method(message):
    user_id = message.from_user.id
    method = message.text.strip()
    user_data[user_id]["contact_method"] = method

    if "Telegram" in method:
        username = message.from_user.username
        if username:
            user_data[user_id]["contact_info"] = f"@{username}"
            bot.send_message(message.chat.id, f"Отлично! Твой логин: @{username}")
            ask_name(message)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            btn = types.KeyboardButton("Отправить логин", request_contact=False)
            markup.add(btn)
            bot.send_message(
                message.chat.id,
                "Нажми кнопку, чтобы отправить свой логин:",
                reply_markup=markup
            )
            bot.register_next_step_handler(message, handle_telegram_username)
    else:
        bot.send_message(message.chat.id, "Укажи номер WhatsApp (например +7...):")
        bot.register_next_step_handler(message, handle_contact_info)

def handle_telegram_username(message):
    user_id = message.from_user.id
    if message.text and "@" in message.text:
        user_data[user_id]["contact_info"] = message.text.strip()
    elif message.from_user.username:
        user_data[user_id]["contact_info"] = f"@{message.from_user.username}"
    else:
        user_data[user_id]["contact_info"] = "не указан"
    ask_name(message)

def handle_contact_info(message):
    user_id = message.from_user.id
    user_data[user_id]["contact_info"] = message.text.strip()
    ask_name(message)

def ask_name(message):
    bot.send_message(message.chat.id, "Как тебя зовут?")
    bot.register_next_step_handler(message, handle_name)

# ================== ОСТАЛЬНЫЕ ФУНКЦИИ (без изменений) ==================
# ← Вставь сюда ВСЕ функции от handle_name до finalize_and_thanks
# (они у тебя уже есть — просто скопируй)

# ================== АДМИНКА ==================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Последние", callback_data="show_last"))
    markup.add(types.InlineKeyboardButton("CSV", callback_data="download_csv"))
    bot.send_message(message.chat.id, "Админка", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data in ["show_last", "download_csv"])
def admin_actions(call):
    if call.from_user.id != ADMIN_ID:
        return
    # ... (твой код)

# ================== WEBHOOK ==================
def set_webhook():
    hostname = os.getenv('RENDER_EXTERNAL_HOSTNAME', 'mybot-c8cm.onrender.com')
    url = f"https://{hostname}/webhook"
    bot.remove_webhook()
    time.sleep(2)
    result = bot.set_webhook(url=url)
    print(f"WEBHOOK: {url} → {result}")

if __name__ == '__main__':
    print("ЗАПУСК...")
    set_webhook()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
