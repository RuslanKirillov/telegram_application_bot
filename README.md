<div align="center">

# 🚀 **Telegram Application Bot** 🚀



**Telegram бот для принятия заявок** — авторизация, админ-панель, принятие заявок, добавление менеджеров-администраторов, полный контроль над работой менеджеров.


## 📦 Зависимости (requirements.txt)

| **Пакет** | **Версия** | **Назначение** |
|-----------|------------|----------------|
| **aiogram** | `3.20.0` | 🎭 Telegram Bot Framework |
| **asyncpg** | `0.30.0` | 🐘 PostgreSQL драйвер |
| **SQLAlchemy** | `2.0.41` | 🔗 ORM / Database |
| **aiohttp** | `3.11.18` | 🌐 Async HTTP клиент |
| **pydantic** | `2.11.7` | ✅ Валидация данных |
| **python-dotenv** | `1.1.0` | ⚙️ Загрузка .env |

**Полный список**: `pip install -r requirements.txt`

### Минимальные версии Python
Python >= 3.9
PostgreSQL >= 13
Docker >= 20 (optional)

## 🚀 Быстрый старт

```bash
git clone https://github.com/RuslanKirillov/telegram_application_bot
cd telegram_application_bot

cp .env.example .env
vim .env  # Поменяйте настройки

python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
python main.py

