"""
Модуль работы с базой данных SQLite
Для перехода на Google Sheets API потребуется:
1. Установить gspread: pip install gspread
2. Создать service account в Google Cloud Console
3. Скачать JSON ключ и добавить в .env: GOOGLE_SERVICE_ACCOUNT_KEY=path/to/key.json
4. Заменить методы add_lead() и get_leads()
5. Создать Google Sheet и настроить доступ для service account
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с базой данных SQLite"""
    
    def __init__(self, db_path: str = "leads.db"):
        """
        Инициализация базы данных
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """Инициализация таблицы лидов, если она не существует"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS leads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        name TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        service TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        UNIQUE(user_id, created_at)
                    )
                """)
                conn.commit()
                logger.info("База данных успешно инициализирована")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")
            raise
    
    def add_lead(self, name: str, phone: str, service: str, user_id: int) -> bool:
        """
        Добавление нового лида в базу данных
        
        Args:
            name: Имя клиента
            phone: Телефон клиента
            service: Выбранная услуга
            user_id: ID пользователя в Telegram
            
        Returns:
            True если успех, False ошибка
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO leads (name, phone, service, user_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, phone, service, user_id)
                )
                conn.commit()
                logger.info(f"Лид успешно добавлен: {name}, {phone}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка при добавлении лида: {e}")
            return False
    
    def get_leads(self, limit: int = 50) -> List[Dict]:
        """
        Получение последних лидов
        
        Args:
            limit: Максимальное количество записей
            
        Returns:
            Список словарей с данными лидов
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM leads
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,)
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении лидов: {e}")
            return []
    
    def get_user_leads(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Получение лидов конкретного пользователя
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество записей
            
        Returns:
            Список словарей с данными лидов пользователя
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM leads
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (user_id, limit)
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении лидов пользователя: {e}")
            return []


# Функции-обертки для удобства использования
def get_db(db_path: str = "leads.db") -> Database:
    """Получение экземпляра базы данных"""
    return Database(db_path)


def init_database(db_path: str = "leads.db") -> None:
    """Инициализация базы данных"""
    db = Database(db_path)
    return db


def add_lead_to_db(name: str, phone: str, service: str, user_id: int, db_path: str = "leads.db") -> bool:
    """Добавление лида в базу данных (функция для обратной совместимости)"""
    db = Database(db_path)
    return db.add_lead(name, phone, service, user_id)


def get_leads_from_db(limit: int = 50, db_path: str = "leads.db") -> List[Dict]:
    """Получение лидов из базы данных (функция для обратной совместимости)"""
    db = Database(db_path)
    return db.get_leads(limit)