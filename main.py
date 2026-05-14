"""
Точка входа в приложение
Запуск Telegram-бота для лидогенерации
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from handlers import lead
from database import init_database

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(bot: Bot):
    """Контекстный менеджер для жизненного цикла бота"""
    logger.info("Запуск бота...")
    
    # Инициализация базы данных
    try:
        init_database()
        logger.info("База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        # Не прерываем запуск, но логируем ошибку
    
    yield
    
    logger.info("Остановка бота...")


async def main() -> None:
    """Основная функция запуска бота"""
    try:
        # Валидация конфигурации
        Config.validate()
        
        # Создание экземпляра бота
        from aiogram import Bot
        
        bot = Bot(token=Config.BOT_TOKEN)
        
        # Создание диспетчера
        storage = MemoryStorage()
        dp = Dispatcher(
            storage=storage,
            lifespan=lifespan,
            default=ParseMode.MARKDOWN
        )
        
        # Регистрация роутеров
        dp.include_router(lead.router)
        
        logger.info("Бот успешно настроен, запуск polling...")
        
        # Запуск polling с обработкой сигналов
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал KeyboardInterrupt, завершение работы...")
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        raise
    finally:
        logger.info("Работа бота завершена")


def handle_shutdown(signum, frame):
    """Обработка сигналов graceful shutdown"""
    logger.info(f"Получен сигнал {signum}, начинаем graceful shutdown...")
    sys.exit(0)


if __name__ == "__main__":
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    try:
        # Запуск основного цикла
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}")
        sys.exit(1)