# Aurora Bot Frontend

## 🏗️ Архитектура Frontend

```
frontend/
├── bot/                    # Telegram bot
│   ├── main.py            # Entry point
│   ├── handlers/          # Message/command handlers
│   │   ├── commands.py    # /start, /help, etc.
│   │   └── messages.py    # User messages
│   ├── middlewares/       # Bot middlewares
│   └── filters/           # Custom filters
│
├── services/              # Business logic
│   ├── llm_service.py    # LLM processing
│   ├── search_service.py # Product search
│   └── recommendation_service.py
│
├── utils/                 # Utilities
│   ├── text_processor.py
│   └── nlp_processor.py
│
└── config/                # Configuration
    └── settings.py        # App settings
```

## 🚀 Запуск Frontend

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка окружения
```bash
# Создайте .env файл с необходимыми переменными
cp env_example.txt .env
```

### 3. Запуск бота
```bash
# Из корневой директории проекта
python -m frontend.bot.main

# Или создайте run_bot.py в корне
```

## ⚙️ Конфигурация

Основные настройки в `config/settings.py`:

- `BOT_TOKEN` - токен Telegram бота
- `BACKEND_API_URL` - URL Backend API
- `OPENROUTER_API_KEY` - ключ для LLM
- `ENABLE_SMART_SEARCH` - включить умный поиск
- `ENABLE_RECOMMENDATIONS` - включить рекомендации

## 📡 Handlers

### Commands (`bot/handlers/commands.py`)
- `/start` - Приветствие и начало работы
- `/help` - Справка по использованию
- `/products` - Список всех продуктов
- `/categories` - Категории продуктов

### Messages (`bot/handlers/messages.py`)
- Обработка пользовательских сообщений
- Интеграция с LLM для генерации ответов
- Поиск и рекомендации продуктов

## 🔧 Services

### LLM Service
- Обработка запросов через LLM
- Генерация ответов
- Контекстное понимание

### Search Service
- Поиск продуктов
- Фильтрация по категориям
- Ранжирование результатов

### Recommendation Service
- Персональные рекомендации
- Анализ истории запросов
- Умные подсказки

## 📝 Разработка

### Добавление нового handler
```python
# В bot/handlers/your_handler.py
from aiogram import Router

router = Router()

@router.message(...)
async def your_handler(message: Message):
    pass

# В bot/handlers/__init__.py
from . import your_handler

def register_handlers(dp: Dispatcher):
    dp.include_router(your_handler.router)
```

### Добавление нового service
```python
# В services/your_service.py
class YourService:
    def __init__(self):
        pass
    
    async def your_method(self):
        pass
```

## 🧪 Тестирование

```bash
# Запуск тестов
pytest tests/frontend/

# Запуск с coverage
pytest --cov=frontend tests/frontend/
```

## 📚 Документация

- [Handlers Guide](../docs/handlers.md)
- [Services Guide](../docs/services.md)
- [Configuration Guide](../docs/configuration.md)
