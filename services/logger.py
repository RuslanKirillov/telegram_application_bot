from aiogram import Bot
from config import config
from database.db import db
from database.models import AdminActionLog
from sqlalchemy import insert

async def log_admin_action(admin_id: int, admin_username: str, action: str, application_id: int = None):
    async with db.async_session() as session:
        stmt = insert(AdminActionLog).values(
            admin_id=admin_id,
            admin_username=admin_username,
            action=action,
            application_id=application_id)
        await session.execute(stmt)
        await session.commit()
    
    bot = Bot(token=config.BOT_TOKEN)
    message = f"👨‍💻 Админ @{admin_username} (ID: {admin_id})\n"
    message += f"🔹 Действие: {action}\n"
    if application_id:
        message += f"📄 Заявка ID: {application_id}"
    await bot.send_message(chat_id=config.MAIN_ADMIN_ID, text=message)
