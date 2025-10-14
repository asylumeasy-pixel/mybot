#!/usr/bin/env python3
# coding: utf-8
from keep_alive import keep_alive
import telebot
import os
import csv
import telebot
from telebot import types
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ================== НАСТРОЙКИ ==================
TOKEN = "8396029873:AAHeu1coggukcGVMwCMx-nmm36VzVo7fuoo"   # <- вставь сюда токен от @BotFather
ADMIN_ID = 7798853644          # <- твой ADMIN_ID (числом)
CSV_FILE = "ankety.csv"
GSHEET_NAME = "AsylumBotData"  # <- имя Google Sheets

# ================== GOOGLE SHEETS SETUP ==================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
try:
    sheet = client.open(GSHEET_NAME).sheet1
except Exception as e:
    print(f"Ошибка при открытии Google Sheet '{GSHEET_NAME}': {e}")
    sheet = None

# ================== ИНИЦИАЛИЗАЦИЯ БОТА ==================
bot = telebot.TeleBot(TOKEN)
user_data = {}  # временное хранилище ответов по сессии {user_id: {field: value, ...}}

# ================== СОХРАНЕНИЕ ДАННЫХ ==================
def save_data(data_dict):
    """Сохраняет анкету в CSV и (если подключено) в Google Sheets."""
    headers = [
        "Способ связи", "Контакт", "Имя", "Причина", "Гражданство (основное)",
        "ВНЖ/2-е гражданство (есть ли)", "2-е гражданство / страна ВНЖ",
        "Регион (ЕС/США)", "Где именно (ЕС)", "Шенген", "Известен маршрут в ЕС",
        "Нужна консультация по маршруту ЕС",
        "Уже в США", "План в США", "Через койотов (метка)", "Известен маршрут в Мексику",
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

    # Отправка в Google Sheets (если подключено)
    if sheet is not None:
        try:
            sheet.append_row([
                data_dict.get("contact_method", "-"),
                data_dict.get("contact_info", "-"),
                data_dict.get("name", "-"),
                data_dict.get("reason", "-"),
                data_dict.get("citizenship", "-"),
                data_dict.get("residence", "-"),
                data_dict.get("second_citizenship", "-"),
                data_dict.get("target_country", "-"),
                data_dict.get("where_exact", "-"),
                data_dict.get("schengen", "-"),
                data_dict.get("known_route_eu", "-"),
                data_dict.get("need_route_consultation_eu", "-"),
                data_dict.get("already_in_usa", "-"),
                data_dict.get("plan_to_usa", "-"),
                data_dict.get("via_coyotes", "-"),
                data_dict.get("known_route_mexico", "-"),
                data_dict.get("need_route_consultation", "-"),
                data_dict.get("tourist_visa", "-"),
                data_dict.get("i589", "-"),
                data_dict.get("declaration", "-"),
                data_dict.get("interview", "-"),
                data_dict.get("how_entered_usa", "-"),
            ])
        except Exception as e:
            print("Ошибка при записи в Google Sheets:", e)

# ================== ДИАЛОГ =================================

# ---- /start ----
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data[user_id] = {}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("💬 Telegram", "📞 WhatsApp")
    bot.send_message(message.chat.id,
                     "👋 Привет! Добро пожаловать!\n\nВыбери удобный способ связи:",
                     reply_markup=markup)
    bot.register_next_step_handler(message, handle_contact_method)

# ---- Способ связи ----
def handle_contact_method(message):
    user_id = message.from_user.id
    method = message.text.strip()
    user_data[user_id]["contact_method"] = method
    if "Telegram" in method:
        bot.send_message(message.chat.id, "Укажи имя пользователя в Telegram (без @):")
    else:
        bot.send_message(message.chat.id, "Укажи номер телефона для WhatsApp (например +7...):")
    bot.register_next_step_handler(message, handle_contact_info)

def handle_contact_info(message):
    user_id = message.from_user.id
    user_data[user_id]["contact_info"] = message.text.strip()
    bot.send_message(message.chat.id, "Как вас зовут?")
    bot.register_next_step_handler(message, handle_name)

def handle_name(message):
    user_id = message.from_user.id
    user_data[user_id]["name"] = message.text.strip()
    # Причина убежища
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("🏳️‍🌈 ЛГБТК+", "✝️ Религия", "🗳 Политика", "🏠 Дом/насилие", "❓ Не знаю")
    bot.send_message(message.chat.id, "По какой причине вы хотите получить убежище?", reply_markup=markup)
    bot.register_next_step_handler(message, handle_reason)

def handle_reason(message):
    user_id = message.from_user.id
    user_data[user_id]["reason"] = message.text.strip()
    bot.send_message(message.chat.id, "Гражданином какой страны вы являетесь?")
    bot.register_next_step_handler(message, handle_citizenship)

def handle_citizenship(message):
    user_id = message.from_user.id
    user_data[user_id]["citizenship"] = message.text.strip()
    # Есть ли второе гражданство/ВНЖ
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("✅ Да", "❌ Нет")
    bot.send_message(message.chat.id,
                     "Есть ли у вас вид на жительство или гражданство второй страны, кроме вашей родной?",
                     reply_markup=markup)
    bot.register_next_step_handler(message, handle_second_citizenship_flag)

def handle_second_citizenship_flag(message):
    user_id = message.from_user.id
    ans = message.text.strip().lower()
    user_data[user_id]["residence"] = message.text.strip()  # Да/Нет
    if "да" in ans:
        bot.send_message(message.chat.id, "Укажите страну второго гражданства или страну, где у вас ВНЖ:")
        bot.register_next_step_handler(message, handle_second_citizenship)
    else:
        # ставим пустое поле для второго гражданства
        user_data[user_id]["second_citizenship"] = "-"
        ask_region(message)

def handle_second_citizenship(message):
    user_id = message.from_user.id
    user_data[user_id]["second_citizenship"] = message.text.strip()
    ask_region(message)

# ---- Регион (ЕС / США) ----
def ask_region(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("🇪🇺 Евросоюз", "🇺🇸 США")
    bot.send_message(message.chat.id, "В какой стране вы хотите получить убежище?", reply_markup=markup)
    bot.register_next_step_handler(message, handle_region)

def handle_region(message):
    user_id = message.from_user.id
    region = message.text.strip()
    user_data[user_id]["target_country"] = region
    if "Евросоюз" in region:
        ask_where_exact_eu(message)
    elif "США" in region:
        ask_already_in_usa(message)
    else:
        ask_region(message)

# ================== ВЕТКА ЕС ==================
def ask_where_exact_eu(message):
    bot.send_message(message.chat.id, "В какой стране или городе вы хотите получить убежище?")
    bot.register_next_step_handler(message, handle_where_exact_eu)

def handle_where_exact_eu(message):
    user_id = message.from_user.id
    user_data[user_id]["where_exact"] = message.text.strip()
    # Шенген
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("✅ Есть", "❌ Нет")
    bot.send_message(message.chat.id, "Есть ли у вас шенгенская виза?", reply_markup=markup)
    bot.register_next_step_handler(message, handle_schengen_eu)

def handle_schengen_eu(message):
    user_id = message.from_user.id
    user_data[user_id]["schengen"] = message.text.strip()
    if "есть" in message.text.lower():
        finalize_and_thanks(message)
    else:
        # вопрос про маршрут в ЕС
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("✅ Да", "❌ Нет")
        bot.send_message(message.chat.id, "Известен ли вам маршрут, каким можно попасть в Европу?", reply_markup=markup)
        bot.register_next_step_handler(message, handle_known_route_eu)

def handle_known_route_eu(message):
    user_id = message.from_user.id
    user_data[user_id]["known_route_eu"] = message.text.strip()
    if "да" in message.text.lower():
        finalize_and_thanks(message)
    else:
        # консультация по маршруту
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("✅ Да", "❌ Нет")
        bot.send_message(message.chat.id, "Нужна ли вам консультация по маршруту?", reply_markup=markup)
        bot.register_next_step_handler(message, handle_need_route_consultation_eu)

def handle_need_route_consultation_eu(message):
    user_id = message.from_user.id
    user_data[user_id]["need_route_consultation_eu"] = message.text.strip()
    finalize_and_thanks(message)

# ================== ВЕТКА США ==================
def ask_already_in_usa(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("✅ Да", "❌ Нет")
    bot.send_message(message.chat.id, "Вы уже находитесь в США?", reply_markup=markup)
    bot.register_next_step_handler(message, handle_already_in_usa)

def handle_already_in_usa(message):
    user_id = message.from_user.id
    ans = message.text.strip().lower()
    user_data[user_id]["already_in_usa"] = message.text.strip()
    if "да" in ans:
        # ветка для тех кто уже в США
        ask_schengen_when_entered(message)
    elif "нет" in ans:
        # ветка для тех кто ещё не в США
        ask_plan_to_usa(message)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, выберите 'Да' или 'Нет'.")
        ask_already_in_usa(message)

# ---- Для тех, кто уже в США ----
def ask_schengen_when_entered(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("✅ Да", "❌ Нет")
    bot.send_message(message.chat.id, "Была ли у вас шенгенская виза, когда вы попали в США?", reply_markup=markup)
    bot.register_next_step_handler(message, handle_schengen_when_entered)

def handle_schengen_when_entered(message):
    user_id = message.from_user.id
    user_data[user_id]["schengen"] = message.text.strip()
    # далее I-589
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("✅ Да", "❌ Нет")
    bot.send_message(message.chat.id, "Подана ли у вас форма I-589 (заявление на убежище)?", reply_markup=markup)
    bot.register_next_step_handler(message, handle_i589)

def handle_i589(message):
    user_id = message.from_user.id
    user_data[user_id]["i589"] = message.text.strip()
    # декларация
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("✅ Да", "❌ Нет")
    bot.send_message(message.chat.id, "Подана ли декларация (история)?", reply_markup=markup)
    bot.register_next_step_handler(message, handle_declaration)

def handle_declaration(message):
    user_id = message.from_user.id
    user_data[user_id]["declaration"] = message.text.strip()
    # интервью
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("✅ Да", "❌ Нет")
    bot.send_message(message.chat.id, "Проводили ли вам интервью на страх или пытки?", reply_markup=markup)
    bot.register_next_step_handler(message, handle_interview)

def handle_interview(message):
    user_id = message.from_user.id
    user_data[user_id]["interview"] = message.text.strip()
    # как попали
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("🛬 По визе", "🚧 Через забор", "🚗 На машине", "🌉 Через мост", "🚶 Пешком", "❓ Другое")
    bot.send_message(message.chat.id, "Как вы попали в США?", reply_markup=markup)
    bot.register_next_step_handler(message, handle_how_entered_usa)

def handle_how_entered_usa(message):
    user_id = message.from_user.id
    user_data[user_id]["how_entered_usa"] = message.text.strip()
    finalize_and_thanks(message)

# ---- Для тех, кто ещё не в США ----
def ask_plan_to_usa(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("🌎 Через Мексику", "✈️ По туристической визе в США", "🏃‍♂️ Через Мексику, но койотами")
    bot.send_message(message.chat.id, "Как вы собираетесь попасть в США?", reply_markup=markup)
    bot.register_next_step_handler(message, handle_plan_to_usa)

def handle_plan_to_usa(message):
    user_id = message.from_user.id
    plan = message.text.strip()
    user_data[user_id]["plan_to_usa"] = plan
    # пометка койотов
    user_data[user_id]["via_coyotes"] = "Да" if "койот" in plan.lower() else "Нет"
    if "мекс" in plan.lower() or "койот" in plan.lower():
        ask_known_route_mexico(message)
    elif "турист" in plan.lower():
        ask_tourist_visa(message)
    else:
        ask_plan_to_usa(message)

def ask_known_route_mexico(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("✅ Да", "❌ Нет")
    bot.send_message(message.chat.id, "Известен ли вам уже маршрут, как добраться до Мексики?", reply_markup=markup)
    bot.register_next_step_handler(message, handle_known_route_mexico)

def handle_known_route_mexico(message):
    user_id = message.from_user.id
    user_data[user_id]["known_route_mexico"] = message.text.strip()
    if "да" in message.text.lower():
        # спросим шенген и финал
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("✅ Есть", "❌ Нет")
        bot.send_message(message.chat.id, "Есть ли у вас шенгенская виза?", reply_markup=markup)
        bot.register_next_step_handler(message, handle_schengen_after_mexico_known)
    else:
        # спросим нужна ли консультация
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("✅ Да", "❌ Нет")
        bot.send_message(message.chat.id, "Нужна ли вам консультация по маршруту?", reply_markup=markup)
        bot.register_next_step_handler(message, handle_need_route_consultation)

def handle_schengen_after_mexico_known(message):
    user_id = message.from_user.id
    user_data[user_id]["schengen"] = message.text.strip()
    finalize_and_thanks(message)

def handle_need_route_consultation(message):
    user_id = message.from_user.id
    user_data[user_id]["need_route_consultation"] = message.text.strip()
    finalize_and_thanks(message)

def ask_tourist_visa(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("✅ Да", "❌ Нет")
    bot.send_message(message.chat.id, "У вас уже есть туристическая виза в США?", reply_markup=markup)
    bot.register_next_step_handler(message, handle_tourist_visa)

def handle_tourist_visa(message):
    user_id = message.from_user.id
    ans = message.text.strip().lower()
    user_data[user_id]["tourist_visa"] = message.text.strip()
    if "да" in ans:
        # спросить шенген
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("✅ Есть", "❌ Нет")
        bot.send_message(message.chat.id, "Есть ли у вас также шенгенская виза?", reply_markup=markup)
        bot.register_next_step_handler(message, handle_schengen_after_tourist)
    else:
        # спросим запись на собеседование
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("✅ Да", "❌ Нет")
        bot.send_message(message.chat.id, "Записались ли вы уже на собеседование в посольстве США?", reply_markup=markup)
        bot.register_next_step_handler(message, handle_visa_interview_registration)

def handle_schengen_after_tourist(message):
    user_id = message.from_user.id
    user_data[user_id]["schengen"] = message.text.strip()
    finalize_and_thanks(message)

def handle_visa_interview_registration(message):
    user_id = message.from_user.id
    user_data[user_id]["visa_interview_registered"] = message.text.strip()
    finalize_and_thanks(message)

# ================== ФИНАЛ И ОТПРАВКА ==================
def finalize_and_thanks(message):
    user_id = message.from_user.id
    data = user_data.get(user_id, {})
    # Сохраняем
    save_data(data)
    # Формируем читаемую сводку для админа
    summary_lines = [
        "📋 Новая анкета:",
        f"Способ связи: {data.get('contact_method','-')}",
        f"Контакт: {data.get('contact_info','-')}",
        f"Имя: {data.get('name','-')}",
        f"Причина: {data.get('reason','-')}",
        f"Гражданство (основное): {data.get('citizenship','-')}",
        f"2-е гражданство/ВНЖ: {data.get('second_citizenship','-')}",
        f"Регион: {data.get('target_country','-')}",
        f"Где (ЕС): {data.get('where_exact','-')}",
        f"Уже в США: {data.get('already_in_usa','-')}",
        f"План в США: {data.get('plan_to_usa','-')}",
        f"Турист. виза: {data.get('tourist_visa','-')}",
        f"I-589: {data.get('i589','-')}",
        f"Декларация: {data.get('declaration','-')}",
        f"Интервью: {data.get('interview','-')}",
        f"Как попал в США: {data.get('how_entered_usa','-')}",
    ]
    summary = "\n".join(summary_lines)
    # Отправляем админу (попробуем, но не упадём при ошибке)
    try:
        bot.send_message(ADMIN_ID, summary)
    except Exception as e:
        print("Ошибка отправки админу:", e)
    # Сообщение пользователю
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Вступить в группу", url="https://t.me/your_group_here"))
    markup.add(types.InlineKeyboardButton("📅 Записаться на консультацию", url="https://t.me/your_consultation_here"))
    bot.send_message(message.chat.id, "🎉 Спасибо! Ваша анкета успешно отправлена. Наш специалист свяжется с вами в ближайшее время.", reply_markup=markup)
    # очищаем сессию
    user_data.pop(user_id, None)

# ================== ПАНЕЛЬ АДМИНА ==================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 У вас нет доступа к панели администратора.")
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📄 Последние анкеты", callback_data="show_last"))
    markup.add(types.InlineKeyboardButton("📊 Скачать CSV", callback_data="download_csv"))
    markup.add(types.InlineKeyboardButton("🧹 Очистить базу", callback_data="clear_data"))
    bot.send_message(message.chat.id, "🛠 Панель администратора", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data in ["show_last", "download_csv", "clear_data"])
def handle_admin_actions(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Нет доступа 🚫", show_alert=True)
        return
    if call.data == "show_last":
        if not os.path.exists(CSV_FILE):
            bot.send_message(call.message.chat.id, "❌ База пуста.")
            return
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()[-6:]
        bot.send_message(call.message.chat.id, "<pre>" + "".join(lines) + "</pre>", parse_mode="HTML")
    elif call.data == "download_csv":
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, "rb") as f:
                bot.send_document(call.message.chat.id, f)
        else:
            bot.send_message(call.message.chat.id, "Файл не найден.")
    elif call.data == "clear_data":
        if os.path.exists(CSV_FILE):
            os.remove(CSV_FILE)
            bot.send_message(call.message.chat.id, "✅ База очищена.")
        else:
            bot.send_message(call.message.chat.id, "База уже пуста.")

# ================== ЗАПУСК ==================
if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
