from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from database.db import db  # Ваш асинхронный объект сессии
from database.models import Application, User
from config import config
from sqlalchemy import select
from aiogram import Bot
from settings_manager import get_setting  # Менеджер настроек

client_router = Router()
bot = Bot(token=config.BOT_TOKEN)

class ApplicationForm(StatesGroup):
    waiting_for_phone = State()

@client_router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    async with db.async_session() as session:
        # Проверяем, есть ли пользователь в users
        result = await session.execute(select(User).where(User.user_id == message.from_user.id))
        user = result.scalars().first()

        if not user:
            new_user = User(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            session.add(new_user)
            await session.commit()

    if message.from_user.id in config.ADMIN_IDS:
        await message.answer("Вы вошли как администратор. Используйте /admin для панели управления.")
    else:
        greeting = get_setting(
            "greeting_message",
            "Добро пожаловать! Пожалуйста, поделитесь вашим номером телефона, нажав кнопку ниже:"
        )

        # Уведомляем админов о новом пользователе
        for admin_id in config.MAIN_ADMIN_ID:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"👤 Пользователь @{message.from_user.username or message.from_user.id} "
                         f"({message.from_user.first_name}) начал работу с ботом."
                )
            except Exception as e:
                print(f"Не удалось отправить уведомление админу {admin_id}: {e}")

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
        # Создаем заявку с номером телефона
        new_application = Application(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            phone_number=phone
        )
        session.add(new_application)
        await session.commit()
        application_id = new_application.id

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
        new_application = Application(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            phone_number=phone
        )
        session.add(new_application)
        await session.commit()
        application_id = new_application.id

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
