import asyncio
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from db import Database
import pandas as pd
from datetime import datetime, timezone, timedelta

API_TOKEN = '6804724660:AAGOns2OYhSTXNK7Y5VcPeBpnxhwDzBLJHk'
GROUP_ID = -4148945641
ADMIN_IDS = [6025479588]
SPREADSHEET_NAME = 'АБИТУРА 2024 КУРСОВОЙ ПРОЕКТ'

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('tgbot-abitura-e3882cb073ec.json', scope)
client = gspread.authorize(creds)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
db = Database('database.db')

user_states = {}

START_TEXT = "Привет, абитуриент! 👋🏻\n\n Я — бот помощник в процессе твоего поступления🎓\n\n Если у тебя есть какие-то вопросы, выбирай образовательную программу и пиши сообщение✉️, не стесняйся😊, наши помощники с радостью ответят на самые разные вопросы и помогут тебе разобраться в процессе поступления!🚀"

faq_text = """
***FAQ НИУ ВШЭ – Пермь***

***1. Какие образовательные программы предлагает НИУ ВШЭ – Пермь?***
НИУ ВШЭ в Перми предлагает программы бакалавриата, магистратуры, аспирантуры и дополнительные образовательные программы. Подробную информацию можно найти в каталоге образовательных программ на сайте университета.

***2. Как подать документы на поступление?***
Документы можно подать через онлайн-систему университета. Для бакалавриата, магистратуры и аспирантуры есть разные сроки и процедуры подачи. Рекомендуем ознакомиться с детальной информацией в соответствующих разделах сайта.

***3. Какие вступительные экзамены необходимо сдать?***  
Список вступительных экзаменов зависит от выбранной программы обучения. Информация о необходимых экзаменах доступна на страницах программ бакалавриата, магистратуры и аспирантуры.

***4. Какие льготы и стипендии предоставляет университет?***  
НИУ ВШЭ – Пермь предлагает различные виды стипендий, включая академические, социальные и специальные стипендии для иностранных студентов. Льготы также могут предоставляться победителям олимпиад и конкурсов.

***5. Какова стоимость обучения?***
Стоимость обучения варьируется в зависимости от программы и уровня подготовки. Подробную информацию о стоимости обучения можно найти на сайте в разделе [Поступающим](https://perm.hse.ru/admission).

***6. Какие есть возможности для иностранных студентов?***
Для иностранных студентов НИУ ВШЭ – Пермь предлагает специальные подготовительные курсы, программы по изучению русского языка и поддержку в процессе адаптации. Подробности можно найти в разделе для иностранных абитуриентов.

***7. Как можно подготовиться к поступлению?***  
Университет предлагает подготовительные курсы к ЕГЭ, факультет довузовской подготовки и различные мероприятия для школьников, такие как олимпиады и открытые дни. Информацию о них можно найти на сайте в разделе [Школьникам](https://perm.hse.ru/schoolchildren).

***8. Какие документы необходимы для поступления?***  
Для поступления необходимо предоставить паспорт, аттестат или диплом, результаты ЕГЭ (для бакалавриата), медицинскую справку и другие документы в зависимости от уровня образования. Полный список документов можно найти в разделе для абитуриентов.

***9. Как связаться с приемной комиссией?***  
Вы можете связаться с приемной комиссией по телефону (342) 205-52-50 или по электронной почте infoperm@hse.ru. Также доступны онлайн-консультации через вебинары.

***10. Где можно найти дополнительную информацию о кампусе?***  
Подробная информация о кампусе, общежитиях и других аспектах жизни студентов доступна на сайте в разделе [О Вышке](https://perm.hse.ru/info).
"""

# Главная клавиатура
start_keyboard = InlineKeyboardMarkup(row_width=1)
start_keyboard.add(
    InlineKeyboardButton("FAQ", callback_data='show_faq'),
    InlineKeyboardButton("Узнать рейтинг", callback_data='check_rating'),
    InlineKeyboardButton("Задать вопрос", callback_data='ask_question'),
    InlineKeyboardButton("Информация о ВУЗе", callback_data='info_v_vuze')
)

# Клавиатура с информацией о вузе
info_vuz_keyboard = InlineKeyboardMarkup(row_width=1)
info_vuz_keyboard.add(
    InlineKeyboardButton("Поступление", url='https://perm.hse.ru/bacalavr/'),
    InlineKeyboardButton("Общежитие", url='https://perm.hse.ru/dormitory'),
    InlineKeyboardButton("Образовательные программы", url='https://perm.hse.ru/bacalavr/#programmes'),
    InlineKeyboardButton("Военная кафедра", url='https://perm.hse.ru/martial/'),
    InlineKeyboardButton("Студенческая жизнь", url='http://students.perm.hse.ru/'),
    InlineKeyboardButton("Соц-сети", url='https://www.hse.ru/hse_community'),
    InlineKeyboardButton("Назад", callback_data='back_to_start')
)

programs_keyboard = InlineKeyboardMarkup(row_width=1)
programs = [
    "Программная инженерия",
    "Бизнес информатика",
    "Юриспруденция",
    "Лингвистика",
    "Дизайн",
    "Экономика",
    "Менеджмент"
]
for program in programs:
    programs_keyboard.add(InlineKeyboardButton(program, callback_data=f'program_{program}'))

# обработчик приветственного сообщения
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer(START_TEXT, reply_markup=start_keyboard)
    if message.chat.type == 'private':
        if not db.user_exists(message.from_user.id):
            db.add_user(message.from_user.id)

# обработчик команды рассылки
@dp.message_handler(commands=['send'])
async def send(message: types.Message):
    if message.chat.type == 'private':
        if message.from_user.id in ADMIN_IDS:
            text = message.text[6:]
            users = db.get_users()
            for row in users:
                try:
                    await bot.send_message(row[0], text)
                    if int(row[1]) != 1:
                        db.set_active(row[0], 1)
                except:
                    db.set_active(row[0], 0)
            await bot.send_message(message.from_user.id, "Рассылка отправлена!")
        else:
            await bot.send_message(message.from_user.id, "У вас нет прав для выполнения данной команды.")

# обработчик кнопки рейтинга
@dp.callback_query_handler(lambda c: c.data == 'check_rating')
async def process_check_rating(callback_query: types.CallbackQuery):
    user_states[callback_query.from_user.id] = 'check_rating'
    await bot.send_message(callback_query.from_user.id, "Введите номер паспорта и серию паспорта в формате 1111222222")
    await bot.answer_callback_query(callback_query.id)

# обработчик кнопки вопроса
@dp.callback_query_handler(lambda c: c.data == 'ask_question')
async def process_ask_question(callback_query: types.CallbackQuery):
    user_states[callback_query.from_user.id] = 'ask_question'
    await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text="Выберите образовательную программу:", reply_markup=programs_keyboard)
    await bot.answer_callback_query(callback_query.id)

# обработчик кнопки FAQ
@dp.callback_query_handler(lambda c: c.data == 'show_faq')
async def process_show_faq(callback_query: types.CallbackQuery):
    back_keyboard = InlineKeyboardMarkup(row_width=1)
    back_keyboard.add(InlineKeyboardButton("Назад", callback_data='back_to_start'))
    await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text=faq_text, reply_markup=back_keyboard, parse_mode="Markdown")
    await bot.answer_callback_query(callback_query.id)

# обработчик кнопки информации о вузе
@dp.callback_query_handler(lambda c: c.data == 'info_v_vuze')
async def process_info_v_vuze(callback_query: types.CallbackQuery):
    await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text="Выберите интересующий вас раздел:", reply_markup=info_vuz_keyboard)
    await bot.answer_callback_query(callback_query.id)

# обработчик кнопки возврата назад
@dp.callback_query_handler(lambda c: c.data == 'back_to_start')
async def process_back_to_start(callback_query: types.CallbackQuery):
    await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text=START_TEXT, reply_markup=start_keyboard)
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data.startswith('program_'))
async def process_program_choice(callback_query: types.CallbackQuery):
    program_name = callback_query.data.split('_')[1]
    user_states[callback_query.from_user.id] = f'ask_question_{program_name}'
    await bot.edit_message_text(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id, text=f"Вы выбрали образовательную программу: {program_name}\nНапишите ваш вопрос.")
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id)

    # обработка состояния check_rating
    if user_state == 'check_rating':
        passport_number = message.text.strip()
        if not passport_number.isdigit() or len(passport_number) != 10:
            await message.answer("Введены некорректные данные. Пожалуйста, введите номер паспорта в формате, например, XXXX - серия, XXXXXX - номер паспорта.")
            return

        processing_message = await message.answer("В обработке...")
        for i in range(3):
            await asyncio.sleep(1)
            await bot.edit_message_text(chat_id=message.chat.id, message_id=processing_message.message_id, text=f"Поиск по базе данных{'.' * (i % 3 + 1)}")

        spreadsheet = client.open(SPREADSHEET_NAME)
        results = []
        fio_output = None

        for sheet in spreadsheet.worksheets():
            data = sheet.get_all_values()
            df = pd.DataFrame(data[1:], columns=data[0])
            passport_column = df.columns[df.columns.str.contains('ПАСПОРТ', case=False)].values[0]
            if passport_column:
                user_data = df[df[passport_column] == passport_number]
                if not user_data.empty:
                    for _, row in user_data.iterrows():
                        if not fio_output:
                            fio_output = f"{row['ФИО']}\n"
                        program_name = sheet.title
                        result = f"\n{program_name}\n\n"
                        subject_scores = []
                        for column in df.columns:
                            if column not in ['НОМЕР ДОГОВОРА', 'ФИО', 'ПАСПОРТ', 'СУММА БАЛЛОВ', 'РЕЙТИНГ', 'УЧ. ЗАВЕДЕНИЕ', 'НОМЕР', 'ПОЧТА']:
                                subject_name = data[0][df.columns.get_loc(column)]
                                subject_score = row[column]
                                subject_scores.append(f"{subject_name.upper()}: {subject_score}")
                        result += '\n'.join(subject_scores)
                        total_score = row['СУММА БАЛЛОВ']
                        rating = row['РЕЙТИНГ']
                        result += f"\n\nСумма баллов: {total_score}\nМесто в рейтинге: {rating}\n"
                        results.append(result)

        if fio_output:
            final_output = fio_output + '\n'.join(results)
            await bot.edit_message_text(chat_id=message.chat.id, message_id=processing_message.message_id, text=final_output)
        else:
            await bot.edit_message_text(chat_id=message.chat.id, message_id=processing_message.message_id, text="Информация по данному паспорту не найдена.")
        user_states.pop(user_id, None)

    # обработка состояния ask_question
    elif user_state and user_state.startswith('ask_question_'):
        program_name = user_state.split('_')[2]
        tz = timezone(timedelta(hours=5))
        current_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
        user_info = (
            f"Время отправки: {current_time}\n"
            f"Username: @{message.from_user.username}\n"
            f"Образовательная программа: {program_name}\n"
            "Сообщение:\n"
            f"{message.text}"
        )

        sent_message = await bot.send_message(GROUP_ID, user_info)
        await message.answer("Ваш вопрос отправлен нашим кураторам. Ожидайте ответа.")
        user_states.pop(user_id, None)
    else:
        await message.answer("Пожалуйста, выберите действие:", reply_markup=start_keyboard)

# обработчики всевозможного ввода
@dp.message_handler(content_types=types.ContentType.ANY)
async def handle_any_message(message: types.Message):
    content_type = message.content_type
    if content_type == types.ContentType.PHOTO:
        await message.answer("Извините, я пока не умею обрабатывать картинки ;(")
    elif content_type == types.ContentType.VOICE:
        await message.answer("Извините, я пока не умею обрабатывать голосовые сообщения ;(")
    elif content_type == types.ContentType.STICKER:
        await message.answer("Извините, я пока не умею обрабатывать стикеры ;(")
    elif content_type == types.ContentType.DOCUMENT:
        await message.answer("Извините, я пока не умею обрабатывать документы ;(")
    elif content_type == types.ContentType.VIDEO:
        await message.answer("Извините, я пока не умею обрабатывать видео ;(")
    elif content_type == types.ContentType.AUDIO:
        await message.answer("Извините, я пока не умею обрабатывать аудиофайлы ;(")
    elif content_type == types.ContentType.CONTACT:
        await message.answer("Извините, я пока не умею обрабатывать контакты ;(")
    elif content_type == types.ContentType.LOCATION:
        await message.answer("Извините, я пока не умею обрабатывать локации ;(")
    elif content_type == types.ContentType.VIDEO_NOTE:
        await message.answer("Извините, я пока не умею обрабатывать видеосообщения ;(")
    elif content_type == types.ContentType.POLL:
        await message.answer("Извините, я пока не умею обрабатывать опросы ;(")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
