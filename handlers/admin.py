from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from database.db import db
from database.models import Application, User
from sqlalchemy import select, update
from services.logger import log_admin_action
from config import config

from settings_manager import get_setting, set_setting  # Импорт менеджера настроек

# Создаем роутер
admin_router = Router()


# FSM состояния для настроек
class SettingsStates(StatesGroup):
    waiting_for_greeting = State()

@admin_router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("У вас нет доступа к этой команде.")
        return
    
    # Создаем кнопки
    button1 = KeyboardButton(text="Активные заявки")
    button2 = KeyboardButton(text="Закрытые заявки")
    button3 = KeyboardButton(text="Статистика")
    button4 = KeyboardButton(text="Настройки")
    
    # Создаем клавиатуру с правильной структурой
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [button1, button2],  # Первый ряд с двумя кнопками
            [button3],
            [button4]            # Второй ряд с одной кнопкой
        ],
        resize_keyboard=True
    )
    
    await message.answer("Панель администратора:", reply_markup=keyboard)

@admin_router.message(F.text == "Активные заявки")
async def show_active_applications(message: types.Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("У вас нет доступа к этой команде.")
        return
    
    async with db.async_session() as session:
        result = await session.execute(
            select(Application).where(Application.is_active == True))
        applications = result.scalars().all()
    
    if not applications:
        await message.answer("Нет активных заявок.")
        return
    
    for app in applications:
        status = "❌ Не взята" if not app.admin_id else f"👨‍💻 В работе (админ ID: {app.admin_id})"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Взять заявку", callback_data=f"take_{app.id}")] if not app.admin_id else [],
            [InlineKeyboardButton(text="Закрыть заявку", callback_data=f"close_{app.id}")]
        ])
        
        await message.answer(
            f"📄 Заявка №{app.id}\n👤 Имя: {app.first_name}\n"
            f"📞 Телефон: {app.phone_number}\n🕒 Создана: {app.created_at} (МСК)\n"
            f"🔹 Статус: {status}", reply_markup=keyboard)

@admin_router.message(F.text == "Закрытые заявки")
async def show_closed_applications(message: types.Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("У вас нет доступа к этой команде.")
        return
    
    async with db.async_session() as session:
        # Получаем заявки, отсортированные по дате закрытия (сначала новые)
        result = await session.execute(
            select(Application)
            .where(Application.is_active == False)
            .order_by(Application.closed_at.desc())  # Сортировка от новых к старым
        )
        applications = result.scalars().all()
    
    if not applications:
        await message.answer("Нет закрытых заявок.")
        return
    
    # Форматируем заявки в строки
    app_lines = []
    for app in applications:
        app_lines.append(
            f"📄 Заявка №{app.id} (ЗАКРЫТА)\n"
            f"👤 Имя: {app.first_name}\n"
            f"📞 Телефон: {app.phone_number}\n"
            f"🕒 Создана: {app.created_at} (МСК)\n"
            f"🕒 Закрыта: {app.closed_at} (МСК)\n"
            f"👨‍💻 Админ ID: {app.admin_id}\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
    
    # Ограничиваем количество заявок (30 последних)
    if len(app_lines) > 30:
        app_lines = app_lines[:30]
        header = "Последние 30 закрытых заявок:\n\n"
    else:
        header = "Все закрытые заявки:\n\n"
    
    full_text = header + "\n\n".join(app_lines)
    
    # Разбиваем текст на части по 4000 символов
    chunk_size = 4000
    for i in range(0, len(full_text), chunk_size):
        chunk = full_text[i:i+chunk_size]
        # Находим последний перенос строки для аккуратного обрыва
        last_newline = chunk.rfind('\n')
        if last_newline != -1 and i + chunk_size < len(full_text):
            chunk = chunk[:last_newline]
        await message.answer(chunk)

@admin_router.message(F.text == "Статистика")
async def statistics_menu(message: types.Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("У вас нет доступа к этой команде.")
        return
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1. Получить список пользователей")],
            [KeyboardButton(text="2. Назад в меню")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Меню статистики:", reply_markup=keyboard)

@admin_router.message(F.text == "2. Назад в меню")
async def back_to_admin_panel_from_stats(message: types.Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("У вас нет доступа к этой команде.")
        return
    await admin_panel(message)

@admin_router.message(F.text == "1. Получить список пользователей")
async def send_user_list(message: types.Message):
    if message.from_user.id != config.MAIN_ADMIN_ID:
        await message.answer("У вас нет доступа к этой команде.")
        return
    
    async with db.async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

    if not users:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="1. Получить список пользователей")],
                [KeyboardButton(text="2. Назад в меню")]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        await message.answer("Пользователи не найдены.", reply_markup=keyboard)
        return

    lines = []
    for idx, user in enumerate(users, start=1):
        username = f"@{user.username}" if user.username else str(user.user_id)
        lines.append(f"{idx}. {username}")

    text = "\n".join(lines)

    # Разбиваем на части по 4000 символов
    chunk_size = 4000
    for i in range(0, len(text), chunk_size):
        await message.answer(text[i:i+chunk_size])

    # Отправляем клавиатуру ПОСЛЕ списка пользователей
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1. Получить список пользователей")],
            #[KeyboardButton(text="2. Получить полный log консоли (last_time.log)")],
            [KeyboardButton(text="Назад в панель администратора")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False  # Ключевое изменение
    )
    await message.answer("Выберите действие:", reply_markup=keyboard)


@admin_router.message(F.text == "Настройки")
async def settings_menu(message: types.Message):
    if message.from_user.id != config.MAIN_ADMIN_ID:
        await message.answer("У вас нет доступа к этой команде.")
        return
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Изменить приветственное сообщение")],
            [KeyboardButton(text="Добавить администратора")],
            [KeyboardButton(text="Назад в панель администратора")]
        ],
        resize_keyboard=True
    )
    await message.answer("Меню настроек:", reply_markup=keyboard)

@admin_router.message(F.text == "Добавить администратора")
async def add_admin(message: types.Message):
    if message.from_user.id != config.MAIN_ADMIN_ID:
        await message.answer("У вас нет доступа к этой команде.")
        return
    
    await message.answer("В разработке...")

@admin_router.message(F.text == "Изменить приветственное сообщение")
async def change_greeting_start(message: types.Message, state: FSMContext):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("У вас нет доступа к этой команде.")
        return
    
    current_greeting = get_setting("greeting_message")
    await message.answer(f"Текущее приветственное сообщение:\n\n{current_greeting}\n\nВведите новое:")
    await state.set_state(SettingsStates.waiting_for_greeting)

@admin_router.message(SettingsStates.waiting_for_greeting)
async def process_new_greeting(message: types.Message, state: FSMContext):
    new_greeting = message.text.strip()
    if not new_greeting:
        await message.answer("Сообщение не может быть пустым. Попробуйте снова.")
        return

    set_setting("greeting_message", new_greeting)
    await message.answer(f"Приветственное сообщение обновлено на:\n\n{new_greeting}")
    await state.clear()
    # Возвращаемся в меню настроек
    await settings_menu(message)

@admin_router.message(F.text == "Назад в панель администратора")
async def back_to_admin_panel(message: types.Message):
    await admin_panel(message)

@admin_router.callback_query(F.data.startswith(('take_', 'close_')))
async def process_callback(callback: types.CallbackQuery):
    action, app_id = callback.data.split('_')
    app_id = int(app_id)
    admin_id = callback.from_user.id
    admin_username = callback.from_user.username
    
    async with db.async_session() as session:
        if action == "take":
            await session.execute(
                update(Application)
                .where(Application.id == app_id)
                .values(admin_id=admin_id))
            await session.commit()
            await callback.message.edit_text(
                text=callback.message.text + f"\n✅ Заявка взята админом @{admin_username}",
                reply_markup=None)
            await log_admin_action(
                admin_id, admin_username, f"Взял заявку №{app_id}", app_id)
            
        elif action == "close":
            await session.execute(
                update(Application)
                .where(Application.id == app_id)
                .values(is_active=False, closed_at=datetime.utcnow(), admin_id=admin_id))
            await session.commit()
            await callback.message.edit_text(
                text=callback.message.text.replace("🔹 Статус:", "🔹 Статус: ✅ ЗАКРЫТО"),
                reply_markup=None)
            await log_admin_action(
                admin_id, admin_username, f"Закрыл заявку №{app_id}", app_id)
    
    await callback.answer()
