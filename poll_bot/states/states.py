from aiogram.fsm.state import StatesGroup, State


class FSMFillForm(StatesGroup):
    fill_name = State()  # Состояние ожидания ввода имени
    fill_age = State()  # Состояние ожидания ввода возраста
    fill_gender = State()  # Состояние ожидания выбора пола
    upload_photo = State()  # Состояние ожидания загрузки фото
    fill_education = State()  # Состояние ожидания выбора образования
    fill_wish_news = State()  # Состояние ожидания выбора получать ли новости
