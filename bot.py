#!/usr/bin/env python3
# coding: utf-8

import os, csv, json, threading, time, requests
import telebot
from telebot import types
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request

# ================== НАСТРОЙКИ ==================
TOKEN = "8396029873:AAHeu1coggukcGVMwCMx-nmm36VzVo7fuoo"
ADMIN_ID = 7798853644
CSV_FILE = "ankety.csv"
GSHEET_NAME = "AsylumBotData"

# ================== GOOGLE SHEETS ==================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = os.getenv("GOOGLE_CREDENTIALS")
sheet = None
if creds_json:
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(creds_json), scope)
        sheet = gspread.authorize(creds).open(GSHEET_NAME).sheet1
        print("Google Sheets OK")
    except: sheet = None

# ================== БОТ + FLASK ==================
bot = telebot.TeleBot(TOKEN)
user_data = {}
app = Flask(__name__)

# --- Пингер ---
def keep_awake():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'mybot-c8cm.onrender.com')}.onrender.com/"
    while True: time.sleep(300); requests.get(url, timeout=10)
threading.Thread(target=keep_awake, daemon=True).start()

@app.route('/') ; def index(): return "OK", 200
@app.route('/webhook', methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return '', 200

# ================== СОХРАНЕНИЕ ==================
def save_data(d):
    headers = ["Способ связи","Контакт","Имя","Причина","Гражданство (основное)","ВНЖ/2-е гражданство (есть ли)","2-е гражданство / страна ВНЖ","Регион (ЕС/США)","Где именно (ЕС)","Шенген","Известен маршрут в ЕС","Нужна консультация по маршруту ЕС","Уже в США","План в США","Через койотов (метка)","Известен маршрут в Мексику","Нужна консультация по маршруту (Мексика)","Туристическая виза (есть ли)","I-589","Декларация (есть ли)","Интервью (страх/пытки)","Как попали в США"]
    with open(CSV_FILE, "a", newline='', encoding="utf-8") as f:
        w = csv.DictWriter(f, headers)
        if not os.path.isfile(CSV_FILE): w.writeheader()
        w.writerow({k: d.get(k, "-") for k in headers})
    if sheet:
        try: sheet.append_row([d.get(k, "-") for k in ["contact_method","contact_info","name","reason","citizenship","residence","second_citizenship","target_country","where_exact","schengen","known_route_eu","need_route_consultation_eu","already_in_usa","plan_to_usa","via_coyotes","known_route_mexico","need_route_consultation","tourist_visa","i589","declaration","interview","how_entered_usa"]])
        except: pass

# ================== НАЗАД ==================
def back(m, s): user_data[m.from_user.id]["step"] = s; globals()[f"step{s}"](m)

# ================== СТАРТ ==================
@bot.message_handler(commands=['start'])
def start(m):
    user_data[m.from_user.id] = {"step": 0}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Начать анкету", callback_data="go"))
    bot.send_message(m.chat.id, "*Привет!* Я помогу с убежищем.", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "go")
def go(c):
    user_data[c.from_user.id]["step"] = 1
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Telegram", "WhatsApp", "Назад")
    bot.send_message(c.message.chat.id, "*Как связаться?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(c.message, step1)

# ================== ШАГИ ==================
def step1(m):
    if m.text == "Назад": return start(m)
    user_data[m.from_user.id]["contact_method"] = m.text
    if "Telegram" in m.text and m.from_user.username:
        user_data[m.from_user.id]["contact_info"] = f"@{m.from_user.username}"
        bot.send_message(m.chat.id, f"Логин: *@{m.from_user.username}*", parse_mode="Markdown")
    else:
        bot.send_message(m.chat.id, "Номер WhatsApp:", parse_mode="Markdown")
        return bot.register_next_step_handler(m, lambda x: (user_data[m.from_user.id].update(contact_info=x.text), step2(x)))
    step2(m)

def step2(m):
    user_data[m.from_user.id]["name"] = m.text if "contact_info" in user_data[m.from_user.id] else m.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("ЛГБТК+", "Религия", "Политика", "Дом/насилие", "Не знаю", "Назад")
    bot.send_message(m.chat.id, "*Причина убежища?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(m, step3)

def step3(m):
    if m.text == "Назад": return step1(m)
    user_data[m.from_user.id]["reason"] = m.text
    bot.send_message(m.chat.id, "*Гражданство?*", parse_mode="Markdown")
    bot.register_next_step_handler(m, step4)

def step4(m):
    user_data[m.from_user.id]["citizenship"] = m.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Да", "Нет", "Назад")
    bot.send_message(m.chat.id, "*ВНЖ или 2-е гражданство?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(m, step5)

def step5(m):
    if m.text == "Назад": return step3(m)
    user_data[m.from_user.id]["residence"] = m.text
    if "да" in m.text.lower():
        bot.send_message(m.chat.id, "*Страна ВНЖ?*", parse_mode="Markdown")
        bot.register_next_step_handler(m, lambda x: (user_data[m.from_user.id].update(second_citizenship=x.text), step6(x)))
    else:
        user_data[m.from_user.id]["second_citizenship"] = "-"
        step6(m)

def step6(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Евросоюз", "США", "Назад")
    bot.send_message(m.chat.id, "*Регион?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(m, step7)

def step7(m):
    if m.text == "Назад": return step5(m)
    user_data[m.from_user.id]["target_country"] = m.text
    if "Евросоюз" in m.text:
        bot.send_message(m.chat.id, "*Где в ЕС?*", parse_mode="Markdown")
        bot.register_next_step_handler(m, lambda x: (user_data[m.from_user.id].update(where_exact=x.text), step8_eu(x)))
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Да", "Нет", "Назад")
        bot.send_message(m.chat.id, "*Ты уже в США?*", parse_mode="Markdown", reply_markup=markup)
        bot.register_next_step_handler(m, step8_usa)

# ================== ВЕТКА США ==================
def step8_usa(m):
    if m.text == "Назад": return step7(m)
    user_data[m.from_user.id]["already_in_usa"] = m.text
    if "да" in m.text.lower():
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Да", "Нет", "Назад")
        bot.send_message(m.chat.id, "*Шенген при въезде?*", parse_mode="Markdown", reply_markup=markup)
        bot.register_next_step_handler(m, step9_usa)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Через Мексику", "По тур. визе", "Мексика, кайоты", "Назад")
        bot.send_message(m.chat.id, "*План в США?*", parse_mode="Markdown", reply_markup=markup)
        bot.register_next_step_handler(m, step10_usa)

def step9_usa(m):
    if m.text == "Назад": return step8_usa(m)
    user_data[m.from_user.id]["schengen"] = m.text
    finalize(m)

def step10_usa(m):
    if m.text == "Назад": return step8_usa(m)
    user_data[m.from_user.id]["plan_to_usa"] = m.text
    finalize(m)

# ================== ВЕТКА ЕС ==================
def step8_eu(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Есть", "Нет", "Назад")
    bot.send_message(m.chat.id, "*Шенген?*", parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(m, lambda x: (user_data[m.from_user.id].update(schengen=x.text), finalize(x) if "есть" in x.text.lower() else step9_eu(x)))

def step9_eu(m):
    if m.text == "Назад": return step8_eu(m)
    finalize(m)

# ================== ФИНАЛ ==================
def finalize(m):
    d = user_data[m.from_user.id]
    save_data(d)
    bot.send_message(ADMIN_ID, f"*Новая анкета*\nИмя: {d.get('name','-')}\nРегион: {d.get('target_country','-')}", parse_mode="Markdown")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Подписаться на группу", url="https://t.me/asylun_usa"))
    markup.add(types.InlineKeyboardButton("Запись на консультацию", url="https://calendly.com/asylumeasy/30min"))
    bot.send_message(m.chat.id, "*Спасибо! Скоро свяжемся.*", reply_markup=markup, parse_mode="Markdown")
    user_data.pop(m.from_user.id, None)

# ================== АДМИНКА ==================
@bot.message_handler(commands=['admin'])
def admin(m):
    if m.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("CSV", callback_data="csv"))
    bot.send_message(m.chat.id, "*Админ*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "csv")
def send_csv(c):
    if c.from_user.id != ADMIN_ID: return
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "rb") as f: bot.send_document(c.message.chat.id, f)
    else: bot.send_message(c.message.chat.id, "Пусто")

# ================== WEBHOOK ==================
def set_webhook():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'mybot-c8cm.onrender.com')}/webhook"
    bot.remove_webhook(); time.sleep(2); bot.set_webhook(url=url); print(f"Webhook: {url}")

if __name__ == '__main__':
    set_webhook()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
