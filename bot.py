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

# === ПИНГЕР КАЖДЫЕ 5 МИНУТ (не даёт заснуть) ===
def keep_awake():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'mybot-c8cm.onrender.com')}.onrender.com/"
    while True:
        time.sleep(300)  # каждые 5 минут
        try:
            requests.get(url, timeout=10)
            print(f"Пинг: {url}")
        except:
            pass
threading.Thread(target=keep_awake, daemon=True).start()

@app.route('/') ; def index(): return "Bot alive!", 200
@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200

# === СОХРАНЕНИЕ ===
def save(d):
    headers = ["method","contact","name","region","in_usa"]
    with open(CSV_FILE, "a", newline='', encoding="utf-8") as f:
        w = csv.DictWriter(f, headers)
        if not os.path.isfile(CSV_FILE): w.writeheader()
        w.writerow(d)

# === СТАРТ ===
@bot.message_handler(commands=['start'])
def start(m):
    user_data[m.from_user.id] = {}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Начать", callback_data="go"))
    bot.send_message(m.chat.id, "*Привет!*", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "go")
def go(c):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Telegram", "WhatsApp")
    bot.send_message(c.message.chat.id, "*Как связаться?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(c.message, s1)

def s1(m):
    user_data[m.from_user.id]["method"] = m.text
    bot.send_message(m.chat.id, "*Имя?*", parse_mode="Markdown")
    bot.register_next_step_handler(m, s2)

def s2(m):
    user_data[m.from_user.id]["name"] = m.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Евросоюз", "США")
    bot.send_message(m.chat.id, "*Регион?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(m, s3)

def s3(m):
    user_data[m.from_user.id]["region"] = m.text
    if "США" in m.text:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Да", "Нет")
        bot.send_message(m.chat.id, "*Ты уже в США?*", parse_mode="Markdown", reply_markup=markup)
        bot.register_next_step_handler(m, s4)
    else:
        finalize(m)

def s4(m):
    user_data[m.from_user.id]["in_usa"] = m.text
    finalize(m)

def finalize(m):
    d = user_data[m.from_user.id]
    save(d)
    bot.send_message(ADMIN_ID, f"*Анкета*\nИмя: {d.get('name','-')}\nРегион: {d.get('region','-')}", parse_mode="Markdown")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Группа", url="https://t.me/asylun_usa"))
    bot.send_message(m.chat.id, "*Спасибо! Анкета сохранена.*", reply_markup=markup, parse_mode="Markdown")
    user_data.pop(m.from_user.id, None)

if __name__ == '__main__':
    # УСТАНОВИ WEBHOOK ВРУЧНУЮ ПОСЛЕ DEPLOY:
    # https://api.telegram.org/bot8396029873:AAHeu1coggukcGVMwCMx-nmm36VzVo7fuoo/setWebhook?url=https://mybot-c8cm.onrender.com/webhook
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
