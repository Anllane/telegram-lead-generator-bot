# Инструкция по развертыванию Telegram-бота "Лидогенератор"

## 📁 Структура проекта

```
lead-generator/
├── main.py                 # Точка входа
├── config.py              # Конфигурация
├── states.py              # FSM-состояния
├── database.py            # Работа с БД
├── handlers/
│   └── lead.py            # Обработчики формы
├── utils/
│   └── validators.py      # Валидация
├── .env.example           # Пример конфигурации
├── requirements.txt       # Зависимости
├── bot.log               # Логи бота
└── leads.db              # База данных SQLite
```

## 🚀 Локальный запуск

### 1. Получение токена бота

1. Найдите в Telegram **@BotFather**
2. Отправьте команду `/newbot`
3. Придумайте имя бота (например, "Мой Лидогенератор")
4. Придумайте юзернейм бота (должен заканчиваться на `bot`, например, `my_lead_generator_bot`)
5. BotFather пришлет вам **API Token** - скопируйте его

### 2. Получение ID администратора

1. Найдите в Telegram **@userinfobot**
2. Отправьте любое сообщение боту
3. Он пришлет ваш ID в формате: `Your user ID is: 123456789`
4. Или используйте команду `/start` в вашем боте и посмотрите логи

### 3. Настройка окружения

1. Скопируйте `.env.example` в `.env`:
   ```bash
   cp .env.example .env
   ```

2. Заполните `.env` файл:
   ```env
   BOT_TOKEN=ваш_токен_бота
   ADMIN_ID=ваш_id_администратора
   DB_PATH=leads.db
   ```

### 4. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 5. Запуск бота

```bash
python main.py
```

Бот запущен! Для тестирования отправьте ему `/start`.

## 🌐 Развертывание на PythonAnywhere

### 1. Подготовка

1. Зарегистрируйтесь на [PythonAnywhere](https://www.pythonanywhere.com/)
2. Создайте новый аккаунт (бесплатный достаточно для тестирования)
3. Перейдите в раздел **Web** и создайте новое веб-приложение

### 2. Загрузка файлов

1. Используйте **Conda** для создания окружения:
   ```bash
   conda create -n leadbot python=3.10
   conda activate leadbot
   ```

2. Загрузите файлы проекта через **Files** интерфейс

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Настройка окружения

1. В разделе **Web** выберите ваш веб-приложение
2. В поле **Source code** укажите путь к вашей директории
3. В разделе **Virtualenv** выберите созданное окружение

### 4. Настройка WSGI

Создайте файл `leadbot_wsgi.py`:
```python
import sys
import os

# Добавляем путь к проекту
path = '/home/ваш_логин/leadbot'
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from main import app as application
```

### 5. Автозапуск

Создайте файл `leadbot_bot.py`:
```python
#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path

# Настройка пути
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / 'bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Запуск бота
if __name__ == "__main__":
    from main import main
    main()
```

### 6. Настройка cron для запуска

Добавьте задачу cron:
```bash
crontab -e
```
Добавьте строку:
```
@reboot cd /home/ваш_логин/leadbot && /home/ваш_логин/.conda/envs/leadbot/bin/python leadbot_bot.py >> /home/ваш_логин/leadbot/cron.log 2>&1
```

## 🚀 Развертывание на Render

### 1. Подготовка репозитория

1. Создайте репозиторий на GitHub
2. Загрузите туда все файлы проекта
3. Убедитесь, что `.env` файл добавлен в `.gitignore`

### 2. Создание приложения на Render

1. Зарегистрируйтесь на [Render](https://render.com/)
2. Нажмите **New +** → **Web Service**
3. Выберите GitHub репозиторий
4. Настройте параметры:
   - **Name**: ваш-бот
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Instance Type**: Free

### 3. Настройка переменных окружения

В разделе **Environment** добавьте:
```
BOT_TOKEN=ваш_токен
ADMIN_ID=ваш_id
DB_PATH=/app/leads.db
```

### 4. Важно!

Render требует веб-сервер, поэтому измените `main.py`:

```python
# В начале файла
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class BotHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

# В конце main() функции
async def main():
    # ... ваш код ...
    
    # Для Render запускаем веб-сервер
    def run_server():
        server = HTTPServer(('0.0.0.0', 10000), BotHandler)
        server.serve_forever()
    
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # ... ваш код ...

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔄 Обновление бота

### Локальное обновление:

```bash
git pull origin main
pip install -r requirements.txt
python main.py
```

### PythonAnywhere:

1. Обновите файлы через **Files**
2. Перезапустите веб-приложение в **Web** разделе
3. Перезапустите процесс бота

## 🔧 Устранение проблем

### Бот не может писать админу

1. Убедитесь, что админ хотя раз написал боту
2. Проверьте `ADMIN_ID` в `.env`
3. Проверьте логи на ошибки

### Валидация телефона не работает

1. Проверьте логи на ошибки
2. Убедитесь, что номер соответствует формату
3. Тестовые номера: `+79001234567`, `89001234567`

### Бот не запускается

1. Проверьте токен в `.env`
2. Убедитесь, что Python 3.10+ установлен
3. Проверьте зависимости

### База данных не создается

1. Убедитесь, что права на запись есть
2. Проверьте путь к `DB_PATH`
3. Посмотрите логи на ошибки

## 📞 Техническая поддержка

При возникновении проблем:
1. Проверьте файл `bot.log`
2. Проверьте консоль вывода
3. Убедитесь, что все переменные окружения заполнены корректно