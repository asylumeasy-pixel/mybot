#!/usr/bin/env python3
# coding: utf-8

import os, csv, threading, time, requests, json
import telebot
from telebot import types
from flask import Flask, request

# ================== НАСТРОЙКИ ==================
TOKEN = "8396029873:AAHeu1coggukcGVMwCMx-nmm36VzVo7fuoo"
ADMIN_ID = 7798853644
CSV_FILE = "ankety.csv"

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

@app.route('/') ; def index(): return "OK", 200
@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200

# ================== СОХРАНЕНИЕ В CSV ==================
def save_to_csv(d):
    headers = ["method","contact","name","reason","citizen","residence","second","region","where_eu","schengen","route_eu","need_eu","in_usa","plan_usa","coyotes","route_mex","need_mex","tourist_visa","i589","decl","interview","how_entered"]
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists: writer.writeheader()
        writer.writerow({k: d.get(k, "-") for k in headers})

# ================== СТАРТ ==================
@bot.message_handler(commands=['start'])
def start(m):
    user_data[m.from_user.id] = {"step": 0}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Начать", callback_data="go"))
    bot.send_message(m.chat.id, "*Привет!* Я помогу с убежищем.", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def go(c):
    if c.data != "go": return
    user_data[c.from_user.id]["step"] = 1
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Telegram", "WhatsApp", "Назад")
    bot.send_message(c.message.chat.id, "*Как связаться?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(c.message, step1)

# ================== ШАГИ ==================
def step1(m):
    if m.text == "Назад": return start(m)
    user_data[m.from_user.id]["method"] = m.text
    if "Telegram" in m.text and m.from_user.username:
        user_data[m.from_user.id]["contact"] = f"@{m.from_user.username}"
        bot.send_message(m.chat.id, f"Логин: *@{m.from_user.username}*", parse_mode="Markdown")
    else:
        bot.send_message(m.chat.id, "Номер WhatsApp:", parse_mode="Markdown")
        return bot.register_next_step_handler(m, lambda x: (user_data[m.from_user.id].update(contact=x.text), step2(x)))
    step2(m)

def step2(m):
    user_data[m.from_user.id]["name"] = m.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("ЛГБТК+", "Религия", "Политика", "Дом/насилие", "Не знаю", "Назад")
    bot.send_message(m.chat.id, "*Причина?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(m, step3)

def step3(m):
    if m.text == "Назад": return step1(m)
    user_data[m.from_user.id]["reason"] = m.text
    bot.send_message(m.chat.id, "*Гражданство?*", parse_mode="Markdown")
    bot.register_next_step_handler(m, step4)

def step4(m):
    user_data[m.from_user.id]["citizen"] = m.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Да", "Нет", "Назад")
    bot.send_message(m.chat.id, "*ВНЖ или 2-е гражданство?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(m, step5)

def step5(m):
    if m.text == "Назад": return step3(m)
    user_data[m.from_user.id]["residence"] = m.text
    if "да" in m.text.lower():
        bot.send_message(m.chat.id, "*Страна ВНЖ?*", parse_mode="Markdown")
        bot.register_next_step_handler(m, lambda x: (user_data[m.from_user.id].update(second=x.text), step6(x)))
    else:
        user_data[m.from_user.id]["second"] = "-"
        step6(m)

def step6(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Евросоюз", "США", "Назад")
    bot.send_message(m.chat.id, "*Регион?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(m, step7)

def step7(m):
    if m.text == "Назад": return step5(m)
    user_data[m.from_user.id]["region"] = m.text
    if "Евросоюз" in m.text:
        bot.send_message(m.chat.id, "*Где в ЕС?*", parse_mode="Markdown")
        bot.register_next_step_handler(m, lambda x: (user_data[m.from_user.id].update(where_eu=x.text), step8_eu(x)))
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Да", "Нет", "Назад")
        bot.send_message(m.chat.id, "*Ты уже в США?*", parse_mode="Markdown", reply_markup=markup)
        bot.register_next_step_handler(m, step8_usa)

# ВЕТКА США
def step8_usa(m):
    if m.text == "Назад": return step7(m)
    user_data[m.from_user.id]["in_usa"] = m.text
    finalize(m)

# ВЕТКА ЕС
def step8_eu(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Есть", "Нет", "Назад")
    bot.send_message(m.chat.id, "*Шенген?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(m, lambda x: (user_data[m.from_user.id].update(schengen=x.text), finalize(x)))

# ФИНАЛ
def finalize(m):
    d = user_data[m.from_user.id]
    save_to_csv(d)
    bot.send_message(ADMIN_ID, f"*Анкета*\nИмя: {d.get('name','-')}\nРегион: {d.get('region','-')}", parse_mode="Markdown")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Группа", url="https://t.me/asylun_usa"))
    markup.add(types.InlineKeyboardButton("Консультация", url="https://calendly.com/asylumeasy/30min"))
    bot.send_message(m.chat.id, "*Спасибо! Скоро свяжемся.*", reply_markup=markup, parse_mode="Markdown")
    user_data.pop(m.from_user.id, None)

# ================== WEBHOOK ==================
def set_webhook():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'mybot-c8cm.onrender.com')}/webhook"
    bot.remove_webhook(); time.sleep(2); bot.set_webhook(url=url); print(f"Webhook: {url}")

if __name__ == '__main__':
    set_webhook()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
