import os.path
import telebot
from random import randint, choice
from PIL import Image
from datetime import datetime
from deep_translator import GoogleTranslator
import qrcode
from io import BytesIO
import requests
import string

TOKEN = "8640439979:AAHPZDig9HJtWcpx5HGTODlmk8LVMRDt9PI"

BUTTON_PASSWORD = "Пароль"
BUTTON_DAY = "День Недели"
BUTTON_TRANSLATE = "Перевод"
BUTTON_FACT = "Факт"
BUTTON_QR = "QR-код"
BUTTON_CURRENCY = "Курс валют"

USER_CURRENT_IMAGE_PATH = {}

bot = telebot.TeleBot(TOKEN)


def create_menu():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    button_password = telebot.types.KeyboardButton(BUTTON_PASSWORD)
    button_day = telebot.types.KeyboardButton(BUTTON_DAY)
    button_translate = telebot.types.KeyboardButton(BUTTON_TRANSLATE)
    button_fact = telebot.types.KeyboardButton(BUTTON_FACT)
    button_qr = telebot.types.KeyboardButton(BUTTON_QR)
    button_currency = telebot.types.KeyboardButton(BUTTON_CURRENCY)

    keyboard.add(button_password, button_fact)
    keyboard.add(button_day, button_translate)
    keyboard.add(button_qr, button_currency)

    return keyboard


def translate_russian_to_english(text):
    try:
        translator = GoogleTranslator(source='ru', target='en')
        translated = translator.translate(text)
        return translated
    except Exception as e:
        return f"Ошибка перевода: {str(e)}"


def create_filters_keyboard():
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)

    button_grayscale = telebot.types.InlineKeyboardButton(
        text="Черно-белый",
        callback_data="filter_grayscale"
    )
    button_sepia = telebot.types.InlineKeyboardButton(
        text="Сепия",
        callback_data="filter_sepia"
    )

    keyboard.add(button_grayscale, button_sepia)
    return keyboard


def apply_grayscale_filter(source_path, result_path):
    image = Image.open(source_path).convert("RGB")
    width, height = image.width, image.height

    for i in range(width):
        for j in range(height):
            r, g, b = image.getpixel((i, j))
            gray = (r + g + b) // 3
            image.putpixel((i, j), (gray, gray, gray))

    image.save(result_path)


def apply_sepia_filter(source_path, result_path):
    image = Image.open(source_path).convert("RGB")
    width, height = image.width, image.height

    for i in range(width):
        for j in range(height):
            r, g, b = image.getpixel((i, j))

            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
            tb = int(0.272 * r + 0.534 * g + 0.131 * b)

            tr = min(255, max(0, tr))
            tg = min(255, max(0, tg))
            tb = min(255, max(0, tb))

            image.putpixel((i, j), (tr, tg, tb))

    image.save(result_path)


def arrange_folders():
    if not os.path.exists("origins"):
        os.mkdir("origins")
    if not os.path.exists("results"):
        os.mkdir("results")


def get_currency_rates():
    try:
        response_usd = requests.get("https://api.nbrb.by/exrates/rates/USD?parammode=2")
        usd_data = response_usd.json()

        response_eur = requests.get("https://api.nbrb.by/exrates/rates/EUR?parammode=2")
        eur_data = response_eur.json()

        response_rub = requests.get("https://api.nbrb.by/exrates/rates/RUB?parammode=2")
        rub_data = response_rub.json()

        response_cny = requests.get("https://api.nbrb.by/exrates/rates/CNY?parammode=2")
        cny_data = response_cny.json()

        response_pln = requests.get("https://api.nbrb.by/exrates/rates/PLN?parammode=2")
        pln_data = response_pln.json()

        # Исправлено: сначала создаем переменную message, потом добавляем в нее
        message = f"Курсы валют к белорусскому рублю\n\n"
        message += f"Дата: {usd_data['Date']}\n\n"
        message += f"USD: {usd_data['Cur_OfficialRate']:.4f} BYN\n"
        message += f"EUR: {eur_data['Cur_OfficialRate']:.4f} BYN\n"
        message += f"RUB: {rub_data['Cur_OfficialRate']:.4f} BYN\n"
        message += f"CNY: {cny_data['Cur_OfficialRate']:.4f} BYN\n"
        message += f"PLN: {pln_data['Cur_OfficialRate']:.4f} BYN\n\n"

        return message

    except Exception as e:
        return f"Ошибка получения курсов: {str(e)}"


@bot.message_handler(func=lambda message: message.text == BUTTON_CURRENCY)
@bot.message_handler(commands=['currency', 'course'])
def handle_currency(message):
    bot.send_message(message.chat.id, "Получаю курсы валют...")
    currency_info = get_currency_rates()
    bot.send_message(message.chat.id, currency_info, reply_markup=create_menu())


@bot.message_handler(func=lambda message: message.text == BUTTON_QR)
@bot.message_handler(commands=['qr'])
def generate_qr(message):
    msg = bot.send_message(
        message.chat.id,
        "Введите текст или ссылку для создания QR-кода:",
        reply_markup=create_menu()
    )
    bot.register_next_step_handler(msg, create_qr)


def create_qr(message):
    text = message.text

    if text.startswith('/'):
        bot.send_message(message.chat.id, "Пожалуйста, введите текст, а не команду.", reply_markup=create_menu())
        return

    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(text)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        bio = BytesIO()
        bio.name = 'qr.png'
        img.save(bio, 'PNG')
        bio.seek(0)

        bot.send_photo(
            message.chat.id,
            bio,
            caption=f"QR-код для: {text[:50]}{'...' if len(text) > 50 else ''}",
            reply_markup=create_menu()
        )

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при создании QR-кода: {str(e)}", reply_markup=create_menu())


@bot.message_handler(commands=['start', 'help'])
def handle_start_and_help(message):
    bot.send_message(
        message.chat.id,
        "Привет! Мои команды:\n"
        "/start - запуск бота\n"
        "/help - справка\n"
        "/pass - Сгенерировать пароль\n"
        "/week - День недели\n"
        "/fact - Факт\n"
        "/translate - Переводчик с русского на английский\n"
        "/qr - Создать QR-код\n"
        "/currency - Курс валют\n\n"
        "Отправь мне фото для наложения фильтра (черно-белый или сепия)",
        reply_markup=create_menu()
    )


@bot.message_handler(func=lambda message: message.text == BUTTON_PASSWORD)
@bot.message_handler(commands=['pass'])
def Pasword(message):
    password = ''.join(choice(string.digits + string.ascii_letters + "!@#$%^&*") for _ in range(12))
    bot.send_message(
        message.chat.id,
        f"Ваш пароль: {password}",
        reply_markup=create_menu()
    )


@bot.message_handler(func=lambda message: message.text == BUTTON_FACT)
@bot.message_handler(commands=['fact'])
def Fact(message):
    facts = [
        'У собаки 4 лапы',
        'Минск столица РБ',
        'Свет от солнца до земли идет примерно 8 минут',
        'Солигорск - столица мира',
        'Пингвины могут подпрыгивать в высоту до 1.8 метра',
        'У осьминога три сердца',
        'Самая большая пицца в мире весила 26 тонн',
        'Более 90% людей проверяют телефон сразу после пробуждения',
        'Жирафы спят всего 30 минут в день',
        'Мед никогда не портится'
    ]
    fact = choice(facts)
    bot.send_message(message.chat.id, fact, reply_markup=create_menu())


@bot.message_handler(func=lambda message: message.text == BUTTON_DAY)
@bot.message_handler(commands=['week'])
def Date_now(message):
    now = datetime.now()
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    weekday_name = days[now.weekday()]
    bot.send_message(message.chat.id, f"Сегодня: {weekday_name}", reply_markup=create_menu())


# Вынесено из Date_now
@bot.message_handler(func=lambda message: message.text == BUTTON_TRANSLATE)
@bot.message_handler(commands=['translate'])
def handle_translate_command(message):
    msg = bot.send_message(
        message.chat.id,
        "Введите слово или фразу на русском языке для перевода на английский:",
        reply_markup=create_menu()
    )
    bot.register_next_step_handler(msg, process_translation)


# Вынесено из Date_now
def process_translation(message):
    russian_text = message.text
    translated_text = translate_russian_to_english(russian_text)
    bot.send_message(
        message.chat.id,
        f"Исходный текст: {russian_text}\nПеревод: {translated_text}",
        reply_markup=create_menu()
    )


@bot.message_handler(content_types=['text'])
def handle_any_text(message):
    if message.text.startswith('/'):
        return
    bot.send_message(
        message.chat.id,
        "Я вас не понял. Используйте команды /start или /help",
        reply_markup=create_menu()
    )


@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    arrange_folders()

    chat_id = message.chat.id
    photo_info = message.photo[len(message.photo) - 1]

    file_info = bot.get_file(photo_info.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_path = f"origins/{chat_id}_orig.jpg"

    with open(image_path, "wb") as image_file:
        image_file.write(downloaded_file)

    USER_CURRENT_IMAGE_PATH[chat_id] = image_path

    bot.send_message(
        chat_id,
        "Фото получено. Выберите фильтр:",
        reply_markup=create_filters_keyboard()
    )


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    callback_data = call.data
    chat_id = call.message.chat.id

    if callback_data == "filter_grayscale":
        if chat_id not in USER_CURRENT_IMAGE_PATH:
            bot.answer_callback_query(call.id, "Сначала отправьте картинку!")
            return

        source_path = USER_CURRENT_IMAGE_PATH[chat_id]
        result_path = f"results/{chat_id}_grayscale.jpg"

        apply_grayscale_filter(source_path, result_path)

        with open(result_path, "rb") as image_file:
            bot.send_photo(
                chat_id,
                image_file,
                caption="Готово! Черно-белый фильтр применен",
                reply_markup=create_menu()
            )

        USER_CURRENT_IMAGE_PATH.pop(chat_id)
        bot.answer_callback_query(call.id, "Фильтр применен")
        return

    elif callback_data == "filter_sepia":
        if chat_id not in USER_CURRENT_IMAGE_PATH:
            bot.answer_callback_query(call.id, "Сначала отправьте картинку!")
            return

        source_path = USER_CURRENT_IMAGE_PATH[chat_id]
        result_path = f"results/{chat_id}_sepia.jpg"

        apply_sepia_filter(source_path, result_path)

        with open(result_path, "rb") as image_file:
            bot.send_photo(
                chat_id,
                image_file,
                caption="Готово! Фильтр сепия применен",
                reply_markup=create_menu()
            )

        USER_CURRENT_IMAGE_PATH.pop(chat_id)
        bot.answer_callback_query(call.id, "Фильтр сепия применен")
        return

if __name__ == "__main__":
    bot.infinity_polling()