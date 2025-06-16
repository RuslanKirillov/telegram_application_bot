from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from database.db import db
from database.models import Application
from config import config
from sqlalchemy import insert
from aiogram import Bot
from settings_manager import get_setting  # Импорт менеджера настроек

client_router = Router()

# Создаем глобальный бот один раз (лучше в основном файле, но для примера здесь)
bot = Bot(token=config.BOT_TOKEN)

class ApplicationForm(StatesGroup):
    waiting_for_phone = State()

@client_router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    if message.from_user.id in config.ADMIN_IDS:
        await message.answer("Вы вошли как администратор. Используйте /admin для панели управления.")
    else:
        # Получаем приветственное сообщение из settings.json
        greeting = get_setting(
            "greeting_message",
            "Добро пожаловать! Пожалуйста, поделитесь вашим номером телефона, нажав кнопку ниже:"
        )

        # Отправляем уведомление админам, что пользователь авторизовался
        for admin_id in config.ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"👤 Пользователь @{message.from_user.username or message.from_user.id} "
                         f"({message.from_user.first_name}) авторизовался в боте."
                )
            except Exception as e:
                print(f"Не удалось отправить уведомление админу {admin_id}: {e}")

        # Создаем клавиатуру с кнопкой запроса контакта
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Отправить номер телефона", request_contact=True)]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(greeting, reply_markup=keyboard)
        await state.set_state(ApplicationForm.waiting_for_phone)

@client_router.message(ApplicationForm.waiting_for_phone, F.contact)
async def process_phone_contact(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    async with db.async_session() as session:
        stmt = insert(Application).values(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            phone_number=phone)
        result = await session.execute(stmt)
        await session.commit()
        application_id = result.inserted_primary_key[0]

    await message.answer(f"Спасибо! Ваша заявка №{application_id} принята.", reply_markup=ReplyKeyboardRemove())
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=f"📄 Новая заявка №{application_id}\n"
                     f"👤 Имя: {message.from_user.first_name}\n"
                     f"📞 Телефон: {phone}\n"
                     f"🆔 ID пользователя: {message.from_user.id}\n\n"
                     f"Для обработки используйте /admin"
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение админу {admin_id}: {e}")
    await state.clear()

@client_router.message(ApplicationForm.waiting_for_phone)
async def process_phone_text(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    if not phone:
        await message.answer("Пожалуйста, отправьте корректный номер телефона.")
        return

    async with db.async_session() as session:
        stmt = insert(Application).values(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            phone_number=phone)
        result = await session.execute(stmt)
        await session.commit()
        application_id = result.inserted_primary_key[0]

    await message.answer(f"Спасибо! Ваша заявка №{application_id} принята.", reply_markup=ReplyKeyboardRemove())
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=f"📄 Новая заявка №{application_id}\n"
                     f"👤 Имя: {message.from_user.first_name}\n"
                     f"📞 Телефон: {phone}\n"
                     f"🆔 ID пользователя: {message.from_user.id}\n\n"
                     f"Для обработки используйте /admin"
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение админу {admin_id}: {e}")
    await state.clear()
