#!/usr/bin/env python3
import os, csv, threading, time, requests, json
import telebot
from telebot import types
from flask import Flask, request

# ================== НАСТРОЙКИ ==================
TOKEN = "8396029873:AAHeu1coggukcGVMwCMx-nmm36VzVo7fuoo"
ADMIN_ID = 7798853644
CSV_FILE = "ankety.csv"
RENDER_URL = "https://mybot-c8cm.onrender.com"  # ЖЁСТКО ПРОПИСАНО

bot = telebot.TeleBot(TOKEN)
user_data = {}
app = Flask(__name__)

# ================== ПИНГЕР 24/7 ==================
def keep_awake():
    url = RENDER_URL
    while True:
        time.sleep(300)
        try:
            requests.get(url, timeout=10)
            print(f"Пинг: {url}")
        except:
            pass
threading.Thread(target=keep_awake, daemon=True).start()

@app.route('/') ; def index(): return "Bot alive! 24/7", 200
@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200

# ================== СОХРАНЕНИЕ В CSV ==================
def save_data(d):
    headers = [
        "Способ связи", "Контакт", "Имя", "Причина", "Гражданство",
        "ВНЖ/2-е гражданство", "2-е гражданство", "Регион", "Где в ЕС",
        "Шенген", "Маршрут ЕС", "Консультация ЕС", "Уже в США", "План в США",
        "Через койотов", "Маршрут Мексика", "Консультация Мексика", "Тур. виза",
        "I-589", "Декларация", "Интервью", "Как попали"
    ]
    with open(CSV_FILE, "a", newline='', encoding="utf-8") as f:
        w = csv.DictWriter(f, headers)
        if not os.path.isfile(CSV_FILE): w.writeheader()
        w.writerow({h: d.get(h, "-") for h in headers})

# ================== НАЗАД ==================
def back(m, step):
    user_data[m.from_user.id]["step"] = step
    if step == 0: start(m)
    elif step == 1: s1(m)
    elif step == 2: s2(m)
    elif step == 3: s3(m)
    elif step == 4: s4(m)
    elif step == 5: s5(m)
    elif step == 6: s6(m)
    elif step == 7: s7(m)

# ================== СТАРТ ==================
@bot.message_handler(commands=['start'])
def start(m):
    user_data[m.from_user.id] = {"step": 0}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Начать анкету", callback_data="go"))
    bot.send_message(m.chat.id, "*Привет!* Я помогу с убежищем в ЕС или США.", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "go")
def go(c):
    user_data[c.from_user.id]["step"] = 1
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Telegram", "WhatsApp", "Назад")
    bot.send_message(c.message.chat.id, "*Как с вами связаться?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(c.message, s1)

# ================== ШАГИ ==================
def s1(m):
    if m.text == "Назад": return start(m)
    user_data[m.from_user.id]["Способ связи"] = m.text
    if "Telegram" in m.text and m.from_user.username:
        user_data[m.from_user.id]["Контакт"] = f"@{m.from_user.username}"
        bot.send_message(m.chat.id, f"Логин: *@{m.from_user.username}*", parse_mode="Markdown")
    else:
        bot.send_message(m.chat.id, "Номер WhatsApp:", parse_mode="Markdown")
        return bot.register_next_step_handler(m, lambda x: (user_data[m.from_user.id].update(Контакт=x.text), s2(x)))
    s2(m)

def s2(m):
    user_data[m.from_user.id]["Имя"] = m.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("ЛГБТК+", "Религия", "Политика", "Дом/насилие", "Не знаю", "Назад")
    bot.send_message(m.chat.id, "*Причина убежища?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(m, s3)

def s3(m):
    if m.text == "Назад": return s1(m)
    user_data[m.from_user.id]["Причина"] = m.text
    bot.send_message(m.chat.id, "*Гражданство?*", parse_mode="Markdown")
    bot.register_next_step_handler(m, s4)

def s4(m):
    user_data[m.from_user.id]["Гражданство"] = m.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Да", "Нет", "Назад")
    bot.send_message(m.chat.id, "*ВНЖ или 2-е гражданство?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(m, s5)

def s5(m):
    if m.text == "Назад": return s3(m)
    user_data[m.from_user.id]["ВНЖ/2-е гражданство"] = m.text
    if "да" in m.text.lower():
        bot.send_message(m.chat.id, "*Страна ВНЖ?*", parse_mode="Markdown")
        bot.register_next_step_handler(m, lambda x: (user_data[m.from_user.id].update(**{"2-е гражданство": x.text}), s6(x)))
    else:
        user_data[m.from_user.id]["2-е гражданство"] = "-"
        s6(m)

def s6(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Евросоюз", "США", "Назад")
    bot.send_message(m.chat.id, "*Регион?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(m, s7)

def s7(m):
    if m.text == "Назад": return s5(m)
    user_data[m.from_user.id]["Регион"] = m.text
    if "Евросоюз" in m.text:
        bot.send_message(m.chat.id, "*Где в ЕС?*", parse_mode="Markdown")
        bot.register_next_step_handler(m, lambda x: (user_data[m.from_user.id].update(**{"Где в ЕС": x.text}), s8_eu(x)))
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Да", "Нет", "Назад")
        bot.send_message(m.chat.id, "*Ты уже в США?*", parse_mode="Markdown", reply_markup=markup)
        bot.register_next_step_handler(m, s8_usa)

# ВЕТКА США
def s8_usa(m):
    if m.text == "Назад": return s7(m)
    user_data[m.from_user.id]["Уже в США"] = m.text
    finalize(m)

# ВЕТКА ЕС
def s8_eu(m):
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

# ================== ЗАПУСК ==================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
