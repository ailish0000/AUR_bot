# Aurora Bot Backend API

## 🏗️ Архитектура

```
backend/
├── api/                    # API слой
│   ├── main.py            # Основное FastAPI приложение
│   └── routes/            # API маршруты
│       ├── products.py    # Продукты
│       ├── search.py      # Поиск
│       ├── users.py       # Пользователи
│       └── analytics.py   # Аналитика
├── core/                  # Ядро системы
│   ├── config.py         # Конфигурация
│   ├── database.py       # База данных
│   └── base.py           # Базовые классы
├── models/                # Модели данных
│   ├── product.py        # Модель продукта
│   └── user.py           # Модель пользователя
├── repositories/          # Репозитории
│   ├── product_repo.py   # Репозиторий продуктов
│   └── user_repo.py      # Репозиторий пользователей
├── services/              # Бизнес-логика
│   ├── product_service.py # Сервис продуктов
│   └── user_service.py    # Сервис пользователей
├── scripts/               # Скрипты
│   └── migrate_data.py   # Миграция данных
└── utils/                 # Утилиты
```

## 🚀 Запуск

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка окружения
```bash
cp env_example.txt .env
# Отредактируйте .env файл
```

### 3. Миграция данных
```bash
python scripts/migrate_data.py
```

### 4. Запуск API сервера
```bash
python run_api.py
```

### 5. Тестирование
```bash
python test_api.py
```

## 📡 API Endpoints

### Основные
- `GET /` - Информация об API
- `GET /health` - Проверка здоровья

### Продукты
- `GET /api/v1/products/` - Список продуктов
- `GET /api/v1/products/{id}` - Конкретный продукт
- `GET /api/v1/products/categories/list` - Категории

### Поиск
- `POST /api/v1/search/query` - Поиск продуктов

### Пользователи
- `GET /api/v1/users/` - Список пользователей
- `GET /api/v1/users/{id}` - Конкретный пользователь

### Аналитика
- `GET /api/v1/analytics/stats` - Общая статистика

## 🗄️ База данных

- **SQLite** для разработки
- **95 продуктов** в базе данных
- **9 категорий** продуктов
- **Автоматическое создание** таблиц при запуске

## 🔧 Конфигурация

Основные настройки в `core/config.py`:
- `DEBUG` - режим отладки
- `DATABASE_URL` - URL базы данных
- `SECRET_KEY` - секретный ключ
- `LOG_LEVEL` - уровень логирования


