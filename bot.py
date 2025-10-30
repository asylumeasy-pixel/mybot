#!/usr/bin/env python3
import os, csv, threading, time, requests
import telebot
from telebot import types
from flask import Flask, request

TOKEN = "8396029873:AAHeu1coggukcGVMwCMx-nmm36VzVo7fuoo"
ADMIN_ID = 7798853644
CSV_FILE = "ankety.csv"
bot = telebot.TeleBot(TOKEN)
user_data = {}
app = Flask(__name__)

# Пингер
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

# Сохранение в CSV
def save_csv(d):
    headers = ["method","contact","name","reason","citizen","residence","second","region","in_usa"]
    with open(CSV_FILE, "a", newline='', encoding="utf-8") as f:
        w = csv.DictWriter(f, headers)
        if not os.path.isfile(CSV_FILE): w.writeheader()
        w.writerow(d)

# Старт
@bot.message_handler(commands=['start'])
def start(m):
    user_data[m.from_user.id] = {"step": 0}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Начать", callback_data="go"))
    bot.send_message(m.chat.id, "*Привет!*", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "go")
def go(c):
    user_data[c.from_user.id]["step"] = 1
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Telegram", "WhatsApp", "Назад")
    bot.send_message(c.message.chat.id, "*Как связаться?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(c.message, s1)

def s1(m):
    if m.text == "Назад": return start(m)
    user_data[m.from_user.id]["method"] = m.text
    if "Telegram" in m.text and m.from_user.username:
        user_data[m.from_user.id]["contact"] = f"@{m.from_user.username}"
    else:
        bot.send_message(m.chat.id, "Номер WhatsApp:")
        return bot.register_next_step_handler(m, lambda x: (user_data[m.from_user.id].update(contact=x.text), s2(x)))
    s2(m)

def s2(m):
    user_data[m.from_user.id]["name"] = m.text
    bot.send_message(m.chat.id, "*Регион?*", parse_mode="Markdown")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Евросоюз", "США", "Назад")
    bot.send_message(m.chat.id, "*Регион?*", reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler(m, s3)

def s3(m):
    if m.text == "Назад": return s1(m)
    user_data[m.from_user.id]["region"] = m.text
    if "США" in m.text:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Да", "Нет", "Назад")
        bot.send_message(m.chat.id, "*Ты уже в США?*", parse_mode="Markdown", reply_markup=markup)
        bot.register_next_step_handler(m, s4)
    else:
        finalize(m)

def s4(m):
    if m.text == "Назад": return s3(m)
    user_data[m.from_user.id]["in_usa"] = m.text
    finalize(m)

def finalize(m):
    d = user_data[m.from_user.id]
    save_csv(d)
    bot.send_message(ADMIN_ID, f"*Анкета*\nИмя: {d.get('name','-')}\nРегион: {d.get('region','-')}", parse_mode="Markdown")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Группа", url="https://t.me/asylun_usa"))
    bot.send_message(m.chat.id, "*Спасибо!*", reply_markup=markup, parse_mode="Markdown")
    user_data.pop(m.from_user.id, None)

def set_webhook():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'mybot-c8cm.onrender.com')}/webhook"
    bot.remove_webhook(); time.sleep(2); bot.set_webhook(url=url)

if __name__ == '__main__':
    set_webhook()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
