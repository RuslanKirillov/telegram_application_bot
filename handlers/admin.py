from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

from database.db import db
from database.models import Application
from sqlalchemy import select, update
from services.logger import log_admin_action
from config import config

# Создаем роутер
admin_router = Router()

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

# Остальные обработчики остаются без изменений
@admin_router.message(F.text == "Активные заявки")
async def show_active_applications(message: types.Message):
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
            f"📞 Телефон: {app.phone_number}\n🕒 Создана: {app.created_at}\n"
            f"🔹 Статус: {status}", reply_markup=keyboard)

@admin_router.message(F.text == "Статистика")
async def show_closed_applications(message: types.Message):
    pass

@admin_router.message(F.text == "Настройки")
async def settings(message: types.Message):
    pass

@admin_router.message(F.text == "Закрытые заявки")
async def show_closed_applications(message: types.Message):
    async with db.async_session() as session:
        result = await session.execute(
            select(Application).where(Application.is_active == False))
        applications = result.scalars().all()
    
    if not applications:
        await message.answer("Нет закрытых заявок.")
        return
    
    for app in applications:
        await message.answer(
            f"📄 Заявка №{app.id} (ЗАКРЫТА)\n👤 Имя: {app.first_name}\n"
            f"📞 Телефон: {app.phone_number}\n🕒 Создана: {app.created_at}\n"
            f"🕒 Закрыта: {app.closed_at}\n👨‍💻 Админ ID: {app.admin_id}")

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