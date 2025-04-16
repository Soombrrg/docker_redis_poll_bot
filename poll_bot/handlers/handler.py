import logging

from aiogram import Dispatcher, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    PhotoSize,
)

from states.states import FSMFillForm

logger = logging.getLogger(__name__)


# Создаем "базу данных" пользователей
user_dict: dict[int, dict[str, str | int | bool]] = {}


# /start вне состояний
# предлагает перейти к заполнению анкеты, отправив команду /fillform
async def process_start_command(message: Message):
    await message.answer(
        text="Этот бот демонстрирует работу FSM\n\n"
        "Чтобы перейти к заполнению анкеты - "
        "отправьте команду /fillform"
    )


# "/cancel" в состоянии
# срабатывает по умолчанию и сообщает, что эта команда работает внутри машины состояний
async def process_cancel_command(message: Message):
    await message.answer(
        text="Отменять нечего. Вы вне машины состояний\n\n"
        "Чтобы перейти к заполнению анкеты - "
        "отправьте команду /fillform"
    )


# Этот хэндлер будет срабатывать на команду "/cancel" в любых состояниях,
# кроме состояния по умолчанию, и отключать машину состояний
async def process_cancel_command_state(message: Message, state: FSMContext):
    await message.answer(
        text="Вы вышли из машины состояний\n\n"
        "Чтобы снова перейти к заполнению анкеты - "
        "отправьте команду /fillform"
    )
    # Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()


# Этот хэндлер будет срабатывать на команду /fillform
# и переводить бота в состояние ожидания ввода имени
async def process_fillform_command(message: Message, state: FSMContext):
    await message.answer(text="Пожалуйста, введите ваше имя")
    # Устанавливаем состояние ожидания ввода имени
    await state.set_state(FSMFillForm.fill_name)


# Этот хэндлер будет срабатывать, если введено корректное имя
# и переводить в состояние ожидания ввода возраста
async def process_name_sent(message: Message, state: FSMContext):
    # Cохраняем введенное имя в хранилище по ключу "name"
    await state.update_data(name=message.text)
    await message.answer(text="Спасибо!\n\nА теперь введите ваш возраст")
    # Устанавливаем состояние ожидания ввода возраста
    await state.set_state(FSMFillForm.fill_age)


# Этот хэндлер будет срабатывать, если во время ввода имени
# будет введено что-то некорректное
async def warning_not_name(message: Message):
    await message.answer(
        text="То, что вы отправили не похоже на имя\n\n"
        "Пожалуйста, введите ваше имя\n\n"
        "Если вы хотите прервать заполнение анкеты - "
        "отправьте команду /cancel"
    )


# Этот хэндлер будет срабатывать, если введен корректный возраст
# и переводить в состояние выбора пола
async def process_age_sent(message: Message, state: FSMContext):
    # Cохраняем возраст в хранилище по ключу "age"
    await state.update_data(age=message.text)
    # Создаем объекты инлайн-кнопок
    male_button = InlineKeyboardButton(text="Мужской ♂", callback_data="male")
    female_button = InlineKeyboardButton(text="Женский ♀", callback_data="female")
    undefined_button = InlineKeyboardButton(
        text="🤷 Пока не ясно", callback_data="undefined_gender"
    )
    # Добавляем кнопки в клавиатуру (две в одном ряду и одну в другом)
    keyboard: list[list[InlineKeyboardButton]] = [
        [male_button, female_button],
        [undefined_button],
    ]
    # Создаем объект инлайн-клавиатуры
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    # Отправляем пользователю сообщение с клавиатурой
    await message.answer(text="Спасибо!\n\nУкажите ваш пол", reply_markup=markup)
    # Устанавливаем состояние ожидания выбора пола
    await state.set_state(FSMFillForm.fill_gender)


# Этот хэндлер будет срабатывать, если во время ввода возраста
# будет введено что-то некорректное
async def warning_not_age(message: Message):
    await message.answer(
        text="Возраст должен быть целым числом от 4 до 120\n\n"
        "Попробуйте еще раз\n\nЕсли вы хотите прервать "
        "заполнение анкеты - отправьте команду /cancel"
    )


# Этот хэндлер будет срабатывать на нажатие кнопки при
# выборе пола и переводить в состояние отправки фото
async def process_gender_press(callback: CallbackQuery, state: FSMContext):
    # Cохраняем пол (callback.data нажатой кнопки) в хранилище,
    # по ключу "gender"
    await state.update_data(gender=callback.data)
    # Удаляем сообщение с кнопками, потому что следующий этап - загрузка фото
    # чтобы у пользователя не было желания тыкать кнопки
    await callback.message.delete()
    await callback.message.answer(
        text="Спасибо! А теперь загрузите, пожалуйста, ваше фото"
    )
    # Устанавливаем состояние ожидания загрузки фото
    await state.set_state(FSMFillForm.upload_photo)


# Этот хэндлер будет срабатывать, если во время выбора пола
# будет введено/отправлено что-то некорректное
async def warning_not_gender(message: Message):
    await message.answer(
        text="Пожалуйста, пользуйтесь кнопками "
        "при выборе пола\n\nЕсли вы хотите прервать "
        "заполнение анкеты - отправьте команду /cancel"
    )


# Этот хэндлер будет срабатывать, если отправлено фото
# и переводить в состояние выбора образования
async def process_photo_sent(
    message: Message, state: FSMContext, largest_photo: PhotoSize
):
    # Cохраняем данные фото (file_unique_id и file_id) в хранилище
    # по ключам "photo_unique_id" и "photo_id"
    await state.update_data(
        photo_unique_id=largest_photo.file_unique_id, photo_id=largest_photo.file_id
    )
    # Создаем объекты инлайн-кнопок
    secondary_button = InlineKeyboardButton(text="Среднее", callback_data="secondary")
    higher_button = InlineKeyboardButton(text="Высшее", callback_data="higher")
    no_edu_button = InlineKeyboardButton(text="🤷 Нету", callback_data="no_edu")
    # Добавляем кнопки в клавиатуру (две в одном ряду и одну в другом)
    keyboard: list[list[InlineKeyboardButton]] = [
        [secondary_button, higher_button],
        [no_edu_button],
    ]
    # Создаем объект инлайн-клавиатуры
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    # Отправляем пользователю сообщение с клавиатурой
    await message.answer(
        text="Спасибо!\n\nУкажите ваше образование", reply_markup=markup
    )
    # Устанавливаем состояние ожидания выбора образования
    await state.set_state(FSMFillForm.fill_education)


# Этот хэндлер будет срабатывать, если во время отправки фото
# будет введено/отправлено что-то некорректное
async def warning_not_photo(message: Message):
    await message.answer(
        text="Пожалуйста, на этом шаге отправьте "
        "ваше фото\n\nЕсли вы хотите прервать "
        "заполнение анкеты - отправьте команду /cancel"
    )


# Этот хэндлер будет срабатывать, если выбрано образование
# и переводить в состояние согласия получать новости
async def process_education_press(callback: CallbackQuery, state: FSMContext):
    # Cохраняем данные об образовании по ключу "education"
    await state.update_data(education=callback.data)
    # Создаем объекты инлайн-кнопок
    yes_news_button = InlineKeyboardButton(text="Да", callback_data="yes_news")
    no_news_button = InlineKeyboardButton(text="Нет, спасибо", callback_data="no_news")
    # Добавляем кнопки в клавиатуру в один ряд
    keyboard: list[list[InlineKeyboardButton]] = [[yes_news_button, no_news_button]]
    # Создаем объект инлайн-клавиатуры
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    # Редактируем предыдущее сообщение с кнопками, отправляя
    # новый текст и новую клавиатуру
    await callback.message.edit_text(
        text="Спасибо!\n\nОстался последний шаг.\n" "Хотели бы вы получать новости?",
        reply_markup=markup,
    )
    # Устанавливаем состояние ожидания выбора получать новости или нет
    await state.set_state(FSMFillForm.fill_wish_news)


# Этот хэндлер будет срабатывать, если во время выбора образования
# будет введено/отправлено что-то некорректное
async def warning_not_education(message: Message):
    await message.answer(
        text="Пожалуйста, пользуйтесь кнопками при выборе образования\n\n"
        "Если вы хотите прервать заполнение анкеты - отправьте "
        "команду /cancel"
    )


# Этот хэндлер будет срабатывать на выбор получать или
# не получать новости и выводить из машины состояний
async def process_wish_news_press(callback: CallbackQuery, state: FSMContext):
    # Cохраняем данные о получении новостей по ключу "wish_news"
    await state.update_data(wish_news=callback.data == "yes_news")
    # Добавляем в "базу данных" анкету пользователя
    # по ключу id пользователя
    user_dict[callback.from_user.id] = await state.get_data()
    # Завершаем машину состояний
    await state.clear()
    # Отправляем в чат сообщение о выходе из машины состояний
    await callback.message.edit_text(
        text="Спасибо! Ваши данные сохранены!\n\n" "Вы вышли из машины состояний"
    )
    # Отправляем в чат сообщение с предложением посмотреть свою анкету
    await callback.message.answer(
        text="Чтобы посмотреть данные вашей " "анкеты - отправьте команду /showdata"
    )


# Этот хэндлер будет срабатывать, если во время согласия на получение
# новостей будет введено/отправлено что-то некорректное
async def warning_not_wish_news(message: Message):
    await message.answer(
        text="Пожалуйста, воспользуйтесь кнопками!\n\n"
        "Если вы хотите прервать заполнение анкеты - "
        "отправьте команду /cancel"
    )


# Этот хэндлер будет срабатывать на отправку команды /showdata
# и отправлять в чат данные анкеты, либо сообщение об отсутствии данных
async def process_showdata_command(message: Message):
    # Отправляем пользователю анкету, если она есть в "базе данных"
    if message.from_user.id in user_dict:
        await message.answer_photo(
            photo=user_dict[message.from_user.id]["photo_id"],
            caption=f'Имя: {user_dict[message.from_user.id]["name"]}\n'
            f'Возраст: {user_dict[message.from_user.id]["age"]}\n'
            f'Пол: {user_dict[message.from_user.id]["gender"]}\n'
            f'Образование: {user_dict[message.from_user.id]["education"]}\n'
            f'Получать новости: {user_dict[message.from_user.id]["wish_news"]}',
        )
    else:
        # Если анкеты пользователя в базе нет - предлагаем заполнить
        await message.answer(
            text="Вы еще не заполняли анкету. Чтобы приступить - "
            "отправьте команду /fillform"
        )


# Этот хэндлер будет срабатывать на любые сообщения в состоянии "по умолчанию",
# кроме тех, для которых есть отдельные хэндлеры
async def send_echo(message: Message):
    await message.reply(text="Извините, моя твоя не понимать")


def register_handlers(dp: Dispatcher):
    dp.message.register(
        process_start_command, CommandStart(), StateFilter(default_state)
    )
    dp.message.register(
        process_cancel_command, Command(commands="cancel"), StateFilter(default_state)
    )
    dp.message.register(
        process_cancel_command_state,
        Command(commands="cancel"),
        ~StateFilter(default_state),
    )
    dp.message.register(
        process_fillform_command,
        Command(commands="fillform"),
        StateFilter(default_state),
    )
    dp.message.register(
        process_name_sent, StateFilter(FSMFillForm.fill_name), F.text.isalpha()
    )
    dp.message.register(warning_not_name, StateFilter(FSMFillForm.fill_name))
    dp.message.register(
        process_age_sent,
        StateFilter(FSMFillForm.fill_age),
        lambda x: x.text.isdigit() and 4 <= int(x.text) <= 120,
    )
    dp.message(warning_not_age, StateFilter(FSMFillForm.fill_age))
    dp.callback_query.register(
        process_gender_press,
        StateFilter(FSMFillForm.fill_gender),
        F.data.in_(["male", "female", "undefined_gender"]),
    )
    dp.message.register(warning_not_gender, StateFilter(FSMFillForm.fill_gender))
    dp.message.register(
        process_photo_sent,
        StateFilter(FSMFillForm.upload_photo),
        F.photo[-1].as_("largest_photo"),
    )
    dp.message.register(warning_not_photo, StateFilter(FSMFillForm.upload_photo))
    dp.callback_query.register(
        process_education_press,
        StateFilter(FSMFillForm.fill_education),
        F.data.in_(["secondary", "higher", "no_edu"]),
    )
    dp.message.register(warning_not_education, StateFilter(FSMFillForm.fill_education))
    dp.callback_query.register(
        process_wish_news_press,
        StateFilter(FSMFillForm.fill_wish_news),
        F.data.in_(["yes_news", "no_news"]),
    )
    dp.message.register(warning_not_wish_news, StateFilter(FSMFillForm.fill_wish_news))
    dp.message.register(
        process_showdata_command,
        Command(commands="showdata"),
        StateFilter(default_state),
    )
    dp.message.register(send_echo, StateFilter(default_state))
