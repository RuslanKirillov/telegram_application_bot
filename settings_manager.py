import json
import os

SETTINGS_FILE = "settings.json"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        # Если файла нет — создаём с дефолтными значениями
        default_settings = {
            "greeting_message": "Добро пожаловать! Пожалуйста, поделитесь вашим номером телефона, нажав кнопку ниже:"
        }
        save_settings(default_settings)
        return default_settings
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(settings: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def get_setting(key: str, default=None):
    settings = load_settings()
    return settings.get(key, default)

def set_setting(key: str, value):
    settings = load_settings()
    settings[key] = value
    save_settings(settings)
