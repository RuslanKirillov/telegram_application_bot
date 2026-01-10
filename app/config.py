import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # Безопасный парсинг ADMIN_IDS
    ADMIN_IDS = []
    try:
        raw_ids = os.getenv("ADMIN_IDS", "").split(',')
        ADMIN_IDS = [int(x.strip()) for x in raw_ids if x.strip().isdigit()]
    except (ValueError, AttributeError):
        ADMIN_IDS = []  # Fallback пустой список
    
    MAIN_ADMIN_ID = int(os.getenv("MAIN_ADMIN_ID", "0") or 0)
    
    DB_NAME = os.getenv("DB_NAME", "veh_car")
    DB_USER = os.getenv("DB_USER", "admin")
    DB_PASS = os.getenv("DB_PASS")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    
    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

config = Config()

