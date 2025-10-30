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
RENDER_URL = "https://mybot-c8cm.onrender.com"

# ================== GOOGLE SHEETS ==================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = os.getenv("GOOGLE_CREDENTIALS")
if creds_json:
    try:
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open(GSHEET_NAME).sheet1
        print("Google Sheets подключён!")
    except Exception as e:
        print(f"Ошибка Google Sheets: {e}")
        sheet = None
else:
    print("GOOGLE_CREDENTIALS не найден!")
    sheet = None

# ================== БОТ + FLASK ==================
bot = telebot.TeleBot(TOKEN)
user_data = {}
app = Flask(__name__)

# --- Пингер ---
def keep_awake():
    while True:
        time.sleep(300)
        try:
            requests.get(RENDER_URL, timeout=10)
            print(f"Пинг: {RENDER_URL}")
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
    headers = [
        "Способ связи", "Контакт", "Имя", "Причина", "Гражданство (основное)",
        "ВНЖ/2-е гражданство (есть ли)", "2-е гражданство / страна ВНЖ",
        "Регион (ЕС/США)", "Где именно (ЕС)", "Шенген", "Известен маршрут в ЕС",
        "Нужна консультация по маршруту ЕС", "Уже в США", "План в США",
        "Через койотов (метка)", "Известен маршрут в Мексику",
        "Нужна консультация по маршруту (Мексика)", "Туристическая виза (есть ли)",
        "I-589", "Декларация (есть ли)", "Интервью (страх/пытки)", "Как попали в США"
    ]
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            k: data_dict.get(k.lower().replace(" ", "_").replace("(", "").replace(")", ""), "-")
            for k in headers
        })
    if sheet:
        try:
            row = [data_dict.get(k.lower().replace(" ", "_").replace("(", "").replace(")", ""), "-") for k in headers]
            sheet.append_row(row)
        except Exception as e:
            print("Ошибка Google Sheets:", e)

# ================== СТАРТ ==================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user_data[user_id] = {}
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("Начать анкету", callback_data="start_anketa")
    markup.add(btn)
    bot.send_message(
        message.chat.id,
        "*Привет!* Я помогу подать заявку на убежище в ЕС или США.\n\nНажми кнопку ниже, чтобы начать:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "start_anketa")
def start_anketa(call):
    user_id = call.from_user.id
    user_data[user_id] = {}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Telegram", "WhatsApp")
    bot.send_message(call.message.chat.id, "*Как с вами связаться?*", reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler(call.message, handle_contact_method)

# ================== КОНТАКТ ==================
def handle_contact_method(message):
    user_id = message.from_user.id
    method = message.text.strip()
    user_data[user_id]["contact_method"] = method
    if "Telegram" in method and message.from_user.username:
        user_data[user_id]["contact_info"] = f"@{message.from_user.username}"
        bot.send_message(message.chat.id, f"Отлично! Твой логин: *@{message.from_user.username}*", parse_mode="Markdown")
        ask_name(message)
    else:
        bot.send_message(message.chat.id, "Укажи номер WhatsApp (например *+7 999 123-45-67*):", parse_mode="Markdown")
        bot.register_next_step_handler(message, handle_contact_info)

def handle_contact_info(message):
    user_id = message.from_user.id
    user_data[user_id]["contact_info"] = message.text.strip()
    ask_name(message)

# ================== ИМЯ И ПРИЧИНА ==================
def ask_name(message):
    bot.send_message(message.chat.id, "*Как тебя зовут?*", parse_mode="Markdown")
    bot.register_next_step_handler(message, handle_name)

def handle_name(message):
    user_id = message.from_user.id
    user_data[user_id]["name"] = message.text.strip()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("ЛГБТК+", "Религия", "Политика", "Дом/насилие", "Не знаю")
    bot.send_message(message.chat.id, "*По какой причине ты хочешь получить убежище?*", reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler(message, handle_reason)

def handle_reason(message):
    user_id = message.from_user.id
    user_data[user_id]["reason"] = message.text.strip()
    bot.send_message(message.chat.id, "*Гражданином какой страны ты являешься?*", parse_mode="Markdown")
    bot.register_next_step_handler(message, handle_citizenship)

def handle_citizenship(message):
    user_id = message.from_user.id
    user_data[user_id]["citizenship"] = message.text.strip()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Да", "Нет")
    bot.send_message(message.chat.id, "*Есть ли у тебя ВНЖ или гражданство второй страны?*", reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler(message, handle_second_citizenship_flag)

# ================== ВНЖ / 2-е ГРАЖДАНСТВО ==================
def handle_second_citizenship_flag(message):
    user_id = message.from_user.id
    user_data[user_id]["residence"] = message.text.strip()
    if "да" in message.text.lower():
        bot.send_message(message.chat.id, "*Укажи страну ВНЖ / 2-е гражданство:*", parse_mode="Markdown")
        bot.register_next_step_handler(message, handle_second_citizenship_country)
    else:
        user_data[user_id]["second_citizenship"] = "-"
        ask_region(message)

def handle_second_citizenship_country(message):
    user_id = message.from_user.id
    user_data[user_id]["second_citizenship"] = message.text.strip()
    ask_region(message)

# ================== РЕГИОН ==================
def ask_region(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Евросоюз", "США")
    bot.send_message(message.chat.id, "*Куда ты хочешь подать на убежище?*", reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler(message, handle_region)

def handle_region(message):
    user_id = message.from_user.id
    user_data[user_id]["target_country"] = message.text.strip()
    if "Евросоюз" in message.text:
        bot.send_message(message.chat.id, "*Где именно в ЕС?*", parse_mode="Markdown")
        bot.register_next_step_handler(message, handle_where_eu)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Да", "Нет")
        bot.send_message(message.chat.id, "*Ты уже в США?*", reply_markup=markup, parse_mode="Markdown")
        bot.register_next_step_handler(message, handle_already_in_usa)

# ================== ЕС ==================
def handle_where_eu(message):
    user_id = message.from_user.id
    user_data[user_id]["where_exact"] = message.text.strip()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Есть", "Нет")
    bot.send_message(message.chat.id, "*Есть ли у тебя Шенген?*", reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler(message, lambda m: finalize_and_thanks(m))

# ================== США ==================
def handle_already_in_usa(message):
    user_id = message.from_user.id
    user_data[user_id]["already_in_usa"] = message.text.strip()
    if "да" in message.text.lower():
        finalize_and_thanks(message)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Через Мексику", "По тур. визе", "Мексика + койоты")
        bot.send_message(message.chat.id, "*Как ты планируешь попасть в США?*", reply_markup=markup, parse_mode="Markdown")
        bot.register_next_step_handler(message, handle_plan_to_usa)

def handle_plan_to_usa(message):
    user_id = message.from_user.id
    user_data[user_id]["plan_to_usa"] = message.text.strip()
    finalize_and_thanks(message)

# ================== ФИНАЛ ==================
def finalize_and_thanks(message):
    user_id = message.from_user.id
    data = user_data.get(user_id, {})
    save_data(data)
    summary = (
        f"*Новая анкета*\n"
        f"Связь: {data.get('contact_method','-')} | {data.get('contact_info','-')}\n"
        f"Имя: *{data.get('name','-')}*\n"
        f"Причина: {data.get('reason','-')}\n"
        f"Гражданство: {data.get('citizenship','-')}\n"
        f"Регион: {data.get('target_country','-')}"
    )
    try:
        bot.send_message(ADMIN_ID, summary, parse_mode="Markdown")
    except Exception as e:
        print("Ошибка админу:", e)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Группа", url="https://t.me/asylun_usa"))
    markup.add(types.InlineKeyboardButton("Консультация", url="https://calendly.com/asylumeasy/30min"))
    bot.send_message(
        message.chat.id,
        "*Спасибо! Анкета отправлена.*\n\nСкоро свяжемся!",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    user_data.pop(user_id, None)

# ================== АДМИНКА ==================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Доступ запрещён.")
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Последние", callback_data="show_last"))
    markup.add(types.InlineKeyboardButton("CSV", callback_data="download_csv"))
    bot.send_message(message.chat.id, "*Админ-панель*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data in ["show_last", "download_csv"])
def admin_action(c):
    if c.from_user.id != ADMIN_ID: return
    if c.data == "show_last" and os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()[-5:]
        bot.send_message(c.message.chat.id, "<pre>" + "".join(lines) + "</pre>", parse_mode="HTML")
    elif c.data == "download_csv" and os.path.exists(CSV_FILE):
        with open(CSV_FILE, "rb") as f:
            bot.send_document(c.message.chat.id, f)

# ================== ЗАПУСК ==================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
