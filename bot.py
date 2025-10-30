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
        print("Google Sheets подключён!")
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
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'mybot-c8cm.onrender.com')}.onrender.com/"
    while True:
        time.sleep(300)
        try:
            requests.get(url, timeout=10)
            print(f"Пинг: {url}")
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
    with open(CSV_FILE, mode="a", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "Способ связи": data_dict.get("contact_method", "-"),
            "Контакт": data_dict.get("contact_info", "-"),
            "Имя": data_dict.get("name", "-"),
            "Причина": data_dict.get("reason", "-"),
            "Гражданство (основное)": data_dict.get("citizenship", "-"),
            "ВНЖ/2-е гражданство (есть ли)": data_dict.get("residence", "-"),
            "2-е гражданство / страна ВНЖ": data_dict.get("second_citizenship", "-"),
            "Регион (ЕС/США)": data_dict.get("target_country", "-"),
            "Где именно (ЕС)": data_dict.get("where_exact", "-"),
            "Шенген": data_dict.get("schengen", "-"),
            "Известен маршрут в ЕС": data_dict.get("known_route_eu", "-"),
            "Нужна консультация по маршруту ЕС": data_dict.get("need_route_consultation_eu", "-"),
            "Уже в США": data_dict.get("already_in_usa", "-"),
            "План в США": data_dict.get("plan_to_usa", "-"),
            "Через койотов (метка)": data_dict.get("via_coyotes", "-"),
            "Известен маршрут в Мексику": data_dict.get("known_route_mexico", "-"),
            "Нужна консультация по маршруту (Мексика)": data_dict.get("need_route_consultation", "-"),
            "Туристическая виза (есть ли)": data_dict.get("tourist_visa", "-"),
            "I-589": data_dict.get("i589", "-"),
            "Декларация (есть ли)": data_dict.get("declaration", "-"),
            "Интервью (страх/пытки)": data_dict.get("interview", "-"),
            "Как попали в США": data_dict.get("how_entered_usa", "-"),
        })

    if sheet:
        try:
            sheet.append_row([data_dict.get(k, "-") for k in [
                "contact_method", "contact_info", "name", "reason", "citizenship",
                "residence", "second_citizenship", "target_country", "where_exact",
                "schengen", "known_route_eu", "need_route_consultation_eu",
                "already_in_usa", "plan_to_usa", "via_coyotes", "known_route_mexico",
                "need_route_consultation", "tourist_visa", "i589", "declaration",
                "interview", "how_entered_usa"
            ]])
        except Exception as e:
            print("Ошибка Google Sheets:", e)

# ================== НАЗАД ==================
def go_back(message, step):
    user_data[message.from_user.id]["step"] = step
    if step == 0: start_command(message)
    elif step == 1: start_anketa(types.CallbackQuery(id="", from_user=message.from_user, message=message, data="start_anketa"))
    elif step == 2: ask_name(message)
    elif step == 3: handle_name(message)
    elif step == 4: handle_reason(message)
    elif step == 5: handle_citizenship(message)
    elif step == 6: handle_second_citizenship_flag(message)
    elif step == 7: handle_second_citizenship(message)
    elif step == 8: ask_region(message)
    # Добавь при необходимости

# ================== СТАРТ ==================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user_data[user_id] = {"step": 0}

    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("Начать анкету", callback_data="start_anketa")
    markup.add(btn)

    bot.send_message(
        message.chat.id,
        "*Привет!* Я помогу подать заявку на убежище в ЕС или США.\n\n"
        "Нажми кнопку ниже, чтобы начать:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "start_anketa")
def start_anketa(call):
    user_id = call.from_user.id
    user_data[user_id] = {"step": 1}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Telegram", "WhatsApp")
    markup.add("Назад")

    bot.send_message(
        call.message.chat.id,
        "*Как с вами связаться?*",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(call.message, handle_contact_method)

# ================== ШАГИ С ЭМОДЗИ ==================
def handle_contact_method(message):
    user_id = message.from_user.id
    if message.text == "Назад":
        go_back(message, 0)
        return

    method = message.text.strip()
    user_data[user_id]["contact_method"] = method
    user_data[user_id]["step"] = 2

    if "Telegram" in method:
        username = message.from_user.username
        if username:
            user_data[user_id]["contact_info"] = f"@{username}"
            bot.send_message(message.chat.id, f"Отлично! Твой логин: *@{username}*", parse_mode="Markdown")
            ask_name(message)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add("Отправить логин")
            markup.add("Назад")
            bot.send_message(message.chat.id, "Нажми кнопку, чтобы отправить логин:", reply_markup=markup)
            bot.register_next_step_handler(message, handle_telegram_username)
    else:
        bot.send_message(message.chat.id, "Укажи номер WhatsApp (например *+7 999 123-45-67*):", parse_mode="Markdown")
        bot.register_next_step_handler(message, handle_contact_info)

def handle_telegram_username(message):
    user_id = message.from_user.id
    if message.text == "Назад":
        go_back(message, 1)
        return
    user_data[user_id]["contact_info"] = message.text.strip() or "не указан"
    ask_name(message)

def handle_contact_info(message):
    user_id = message.from_user.id
    user_data[user_id]["contact_info"] = message.text.strip()
    ask_name(message)

def ask_name(message):
    user_data[message.from_user.id]["step"] = 3
    bot.send_message(message.chat.id, "*Как тебя зовут?*", parse_mode="Markdown")
    bot.register_next_step_handler(message, handle_name)

def handle_name(message):
    user_id = message.from_user.id
    user_data[user_id]["name"] = message.text.strip()
    user_data[user_id]["step"] = 4

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    markup.add("ЛГБТК+", "Религия", "Политика", "Дом/насилие", "Не знаю")
    markup.add("Назад")

    bot.send_message(message.chat.id, "*По какой причине ты хочешь получить убежище?*", reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler(message, handle_reason)

def handle_reason(message):
    user_id = message.from_user.id
    if message.text == "Назад":
        go_back(message, 3)
        return
    user_data[user_id]["reason"] = message.text.strip()
    user_data[user_id]["step"] = 5
    bot.send_message(message.chat.id, "*Гражданином какой страны ты являешься?*", parse_mode="Markdown")
    bot.register_next_step_handler(message, handle_citizenship)

def handle_citizenship(message):
    user_id = message.from_user.id
    user_data[user_id]["citizenship"] = message.text.strip()
    user_data[user_id]["step"] = 6
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Да", "Нет")
    markup.add("Назад")
    bot.send_message(message.chat.id, "*Есть ли у тебя ВНЖ или гражданство второй страны?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(message, handle_second_citizenship_flag)

def handle_second_citizenship_flag(message):
    user_id = message.from_user.id
    if message.text == "Назад":
        go_back(message, 5)
        return
    ans = message.text.strip().lower()
    user_data[user_id]["residence"] = message.text.strip()
    if "да" in ans:
        user_data[user_id]["step"] = 7
        bot.send_message(message.chat.id, "*Укажи страну второго гражданства или ВНЖ:*", parse_mode="Markdown")
        bot.register_next_step_handler(message, handle_second_citizenship)
    else:
        user_data[user_id]["second_citizenship"] = "-"
        ask_region(message)

def handle_second_citizenship(message):
    user_id = message.from_user.id
    user_data[user_id]["second_citizenship"] = message.text.strip()
    ask_region(message)

def ask_region(message):
    user_data[message.from_user.id]["step"] = 8
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Евросоюз", "США")
    markup.add("Назад")
    bot.send_message(message.chat.id, "*В какой стране ты хочешь получить убежище?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(message, handle_region)

# === ОСТАЛЬНЫЕ ШАГИ (с эмодзи и "Назад") ===
# (все функции ниже — как в предыдущем коде, с *текстом* и кнопкой "Назад")

def handle_region(message):
    user_id = message.from_user.id
    if message.text == "Назад":
        go_back(message, 7 if user_data[user_id].get("residence") == "Да" else 6)
        return
    region = message.text.strip()
    user_data[user_id]["target_country"] = region
    if "Евросоюз" in region:
        bot.send_message(message.chat.id, "*В какой стране или городе ЕС?*", parse_mode="Markdown")
        bot.register_next_step_handler(message, handle_where_exact_eu)
    elif "США" in region:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Да", "Нет")
        markup.add("Назад")
        bot.send_message(message.chat.id, "*Ты уже в США?*", parse_mode="Markdown", reply_markup=markup)
        bot.register_next_step_handler(message, handle_already_in_usa)
    else:
        ask_region(message)

# ... (все остальные функции — с *Markdown* и "Назад")

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

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("Подписаться на группу", url="https://t.me/asylun_usa"))
    markup.add(types.InlineKeyboardButton("Запись на бесплатную консультацию", url="https://calendly.com/asylumeasy/30min"))

    bot.send_message(
        message.chat.id,
        "*Спасибо! Анкета отправлена.*\n\n"
        "Скоро с вами свяжемся. А пока:",
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
    markup.add(types.InlineKeyboardButton("Последние анкеты", callback_data="show_last"))
    markup.add(types.InlineKeyboardButton("Скачать CSV", callback_data="download_csv"))
    bot.send_message(message.chat.id, "*Админ-панель*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data in ["show_last", "download_csv"])
def admin_actions(call):
    if call.from_user.id != ADMIN_ID:
        return
    if call.data == "show_last":
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()[-6:]
            bot.send_message(call.message.chat.id, "<pre>" + "".join(lines) + "</pre>", parse_mode="HTML")
        else:
            bot.send_message(call.message.chat.id, "Пусто.")
    elif call.data == "download_csv":
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, "rb") as f:
                bot.send_document(call.message.chat.id, f)
        else:
            bot.send_message(call.message.chat.id, "Файл не найден.")

# ================== WEBHOOK ==================
def set_webhook():
    hostname = os.getenv('RENDER_EXTERNAL_HOSTNAME', 'mybot-c8cm.onrender.com')
    url = f"https://{hostname}/webhook"
    bot.remove_webhook()
    time.sleep(2)
    result = bot.set_webhook(url=url)
    print(f"WEBHOOK: {url} → {result}")

if __name__ == '__main__':
    print("ЗАПУСК БОТА...")
    set_webhook()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
