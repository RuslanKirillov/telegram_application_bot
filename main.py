import asyncio
import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import config
from database.db import db
from handlers import admin_router, client_router

# Создаем папку для логов, если её нет
os.makedirs('log', exist_ok=True)

# Формируем имя файла с датой, например: bot_2025-06-16.log
log_filename = datetime.now().strftime('log/bot_%Y-%m-%d_%H-%M-%S.log')

# Настройка логгера
logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Файл с динамическим именем
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Консольный вывод
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

async def main():
    bot = Bot(token=config.BOT_TOKEN)
    try:
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        dp.include_router(admin_router)
        dp.include_router(client_router)
        
        await db.create_tables()
        
        logging.info("Бот запущен")
        await dp.start_polling(bot)
        
    except Exception as e:
        logging.error(f"Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
