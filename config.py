"""
Конфигурация приложения
Загрузка переменных окружения из .env файла
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()

class Config:
    """Класс конфигурации бота"""
    
    # Обязательные переменные окружения
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    DB_PATH: str = os.getenv("DB_PATH", "leads.db")
    
    @classmethod
    def validate(cls) -> bool:
        """Валидация конфигурации"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в .env файле")
        
        if cls.ADMIN_ID == 0:
            raise ValueError("ADMIN_ID не установлен или равен 0")
        
        return True