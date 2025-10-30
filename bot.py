#!/usr/bin/env python3
# coding: utf-8

import os
import csv
import json
import threading
import time
import requests
import telebot
from telebot import types
from flask import Flask, request

# ================== НАСТРОЙКИ ==================
TOKEN = "8396029873:AAHeu1coggukcGVMwCMx-nmm36VzVo7fuoo"
ADMIN_ID = 7798853644
CSV_FILE = "ankety.csv"
GSHEET_NAME = "AsylumBotData"

# ================== GOOGLE SHEETS (опционально) ==================
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if creds_json:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(creds_json), scope)
        client = gspread.authorize(creds)
        sheet = client.open(GSHEET_NAME).sheet1
        print("Google Sheets подключён")
    else:
        sheet = None
except Exception as e:
    print("Google Sheets отключён:", e)
    sheet = None

# ================== БОТ + FLASK ==================
bot = telebot.TeleBot(TOKEN)
user_data = {}
app = Flask(__name__)

# --- Пингер ---
def keep_awake():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'mybot-c8cm.onrender.com')}.onrender.com/"
    while True:
        time.sleep(300)
        try: requests.get(url, timeout=10)
        except: pass
threading.Thread(target=keep_awake, daemon=True).start()

@app.route('/') ; def index(): return "Bot alive!", 200
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid', 403

# ================== СОХРАНЕНИЕ ==================
def save_data(data):
    headers = ["Способ связи","Контакт","Имя","Причина","Гражданство","ВНЖ","2-е гражданство","Регион","Где в ЕС","Шенген","Маршрут ЕС","Консультация ЕС","В США","План США","Койоты","Маршрут Мексика","Консультация Мексика","Тур. виза","I-589","Декларация","Интервью","Как въехали"]
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists: writer.writeheader()
        writer.writerow({h: data.get(h, "-") for h in headers})

    if sheet:
        try:
            sheet.append_row([data.get(k, "-") for k in [
                "Способ связи","Контакт","Имя","Причина","Гражданство","ВНЖ","2-е гражданство","Регион","Где в ЕС","Шенген","Маршрут ЕС","Консультация ЕС","В США","План США","Койоты","Маршрут Мексика","Консультация Мексика","Тур. виза","I-589","Декларация","Интервью","Как въехали"
            ]])
        except: pass

# ================== НАЗАД ==================
def go_back(m, step):
    user_data[m.from_user.id]["step"] = step
    if step == 0: start(m)
    elif step == 1: step1(m)
    elif step == 2: step2(m)
    elif step == 3: step3(m)
    elif step == 4: step4(m)
    elif step == 5: step5(m)
    elif step == 6: step6(m)
    elif step == 7: step7(m)

# ================== СТАРТ ==================
@bot.message_handler(commands=['start'])
def start(m):
    user_data[m.from_user.id] = {"step": 0}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Начать анкету", callback_data="go"))
    bot.send_message(m.chat.id, "*Привет!* Я помогу подать заявку на убежище.", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "go")
def go(c):
    user_data[c.from_user.id]["step"] = 1
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Telegram", "WhatsApp", "Назад")
    bot.send_message(c.message.chat.id, "*Как с вами связаться?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(c.message, step1)

# ================== ШАГИ ==================
def step1(m):
    if m.text == "Назад": return start(m)
    user_data[m.from_user.id]["Способ связи"] = m.text
    if "Telegram" in m.text and m.from_user.username:
        user_data[m.from_user.id]["Контакт"] = f"@{m.from_user.username}"
        bot.send_message(m.chat.id, f"Отлично! Логин: *@{m.from_user.username}*", parse_mode="Markdown")
    else:
        bot.send_message(m.chat.id, "Укажи номер WhatsApp:", parse_mode="Markdown")
        return bot.register_next_step_handler(m, lambda x: (user_data[m.from_user.id].update(Контакт=x.text), step2(x)))
    step2(m)

def step2(m):
    user_data[m.from_user.id]["Имя"] = m.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("ЛГБТК+", "Религия", "Политика", "Дом/насилие", "Не знаю", "Назад")
    bot.send_message(m.chat.id, "*Причина убежища?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(m, step3)

def step3(m):
    if m.text == "Назад": return step1(m)
    user_data[m.from_user.id]["Причина"] = m.text
    bot.send_message(m.chat.id, "*Гражданство?*", parse_mode="Markdown")
    bot.register_next_step_handler(m, step4)

def step4(m):
    user_data[m.from_user.id]["Гражданство"] = m.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Да", "Нет", "Назад")
    bot.send_message(m.chat.id, "*ВНЖ или 2-е гражданство?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(m, step5)

def step5(m):
    if m.text == "Назад": return step3(m)
    user_data[m.from_user.id]["ВНЖ"] = m.text
    if "да" in m.text.lower():
        bot.send_message(m.chat.id, "*Страна ВНЖ?*", parse_mode="Markdown")
        bot.register_next_step_handler(m, lambda x: (user_data[m.from_user.id].update(**{"2-е гражданство": x.text}), step6(x)))
    else:
        user_data[m.from_user.id]["2-е гражданство"] = "-"
        step6(m)

def step6(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Евросоюз", "США", "Назад")
    bot.send_message(m.chat.id, "*Регион?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(m, step7)

def step7(m):
    if m.text == "Назад": return step5(m)
    user_data[m.from_user.id]["Регион"] = m.text
    if "Евросоюз" in m.text:
        bot.send_message(m.chat.id, "*Где в ЕС?*", parse_mode="Markdown")
        bot.register_next_step_handler(m, lambda x: (user_data[m.from_user.id].update(**{"Где в ЕС": x.text}), step8_eu(x)))
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Да", "Нет", "Назад")
        bot.send_message(m.chat.id, "*Ты уже в США?*", parse_mode="Markdown", reply_markup=markup)
        bot.register_next_step_handler(m, step8_usa)

def step8_usa(m):
    if m.text == "Назад": return step7(m)
    user_data[m.from_user.id]["В США"] = m.text
    finalize(m)

def step8_eu(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Есть", "Нет", "Назад")
    bot.send_message(m.chat.id, "*Шенген?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(m, lambda x: (user_data[m.from_user.id].update(Шенген=x.text), finalize(x)))

# ================== ФИНАЛ ==================
def finalize(m):
    d = user_data[m.from_user.id]
    save_data(d)
    bot.send_message(ADMIN_ID, f"*Новая анкета*\nИмя: {d.get('Имя','-')}\nРегион: {d.get('Регион','-')}", parse_mode="Markdown")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Группа", url="https://t.me/asylun_usa"))
    markup.add(types.InlineKeyboardButton("Консультация", url="https://calendly.com/asylumeasy/30min"))
    bot.send_message(m.chat.id, "*Спасибо! Анкета отправлена.*", reply_markup=markup, parse_mode="Markdown")
    user_data.pop(m.from_user.id, None)

# ================== АДМИНКА ==================
@bot.message_handler(commands=['admin'])
def admin(m):
    if m.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Последние", callback_data="last"))
    markup.add(types.InlineKeyboardButton("CSV", callback_data="csv"))
    bot.send_message(m.chat.id, "*Админ*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data in ["last", "csv"])
def admin_action(c):
    if c.from_user.id != ADMIN_ID: return
    if c.data == "last" and os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()[-5:]
        bot.send_message(c.message.chat.id, "<pre>" + "".join(lines) + "</pre>", parse_mode="HTML")
    elif c.data == "csv" and os.path.exists(CSV_FILE):
        with open(CSV_FILE, "rb") as f:
            bot.send_document(c.message.chat.id, f)

# ================== WEBHOOK ==================
def set_webhook():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'mybot-c8cm.onrender.com')}/webhook"
    bot.remove_webhook()
    time.sleep(2)
    bot.set_webhook(url=url)
    print(f"Webhook: {url}")

if __name__ == '__main__':
    set_webhook()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
