#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from dotenv import load_dotenv

print("🔍 ПРОВЕРКА ЛОГОВ И ИНТЕГРАЦИИ")
print("=" * 50)

# Загружаем переменные окружения
load_dotenv()

print("📋 Проверка переменных окружения:")
print("-" * 30)

# Проверяем API ключ
api_key = os.getenv("GOOGLE_SHEETS_API_KEY")
print(f"GOOGLE_SHEETS_API_KEY: {'✅ Найден' if api_key else '❌ Не найден'}")
if api_key:
    print(f"   Ключ: {api_key[:20]}...")

# Проверяем другие переменные
bot_token = os.getenv("BOT_TOKEN")
print(f"BOT_TOKEN: {'✅ Найден' if bot_token else '❌ Не найден'}")

admin_id = os.getenv("ADMIN_ID")
print(f"ADMIN_ID: {'✅ Найден' if admin_id else '❌ Не найден'}")

print("\n🔧 Проверка модулей:")
print("-" * 30)

# Проверяем модуль google_sheets
try:
    from google_sheets import google_sheets_logger, log_user_question
    print("✅ Модуль google_sheets импортирован успешно")
    print(f"   ID таблицы: {google_sheets_logger.sheet_id}")
    print(f"   API ключ в модуле: {'✅ Найден' if google_sheets_logger.api_key else '❌ Не найден'}")
    print(f"   Модуль включен: {'✅ Да' if google_sheets_logger.enabled else '❌ Нет'}")
except ImportError as e:
    print(f"❌ Ошибка импорта google_sheets: {e}")

# Проверяем модуль бота
try:
    import bot
    print("✅ Модуль bot импортирован успешно")
    
    # Проверяем переменные в боте
    sheets_enabled = getattr(bot, 'GOOGLE_SHEETS_ENABLED', False)
    print(f"   GOOGLE_SHEETS_ENABLED: {'✅ Да' if sheets_enabled else '❌ Нет'}")
    
    ai_enabled = getattr(bot, 'AI_ENABLED', False)
    print(f"   AI_ENABLED: {'✅ Да' if ai_enabled else '❌ Нет'}")
    
except ImportError as e:
    print(f"❌ Ошибка импорта bot: {e}")

print("\n📊 Проверка интеграции:")
print("-" * 30)

# Проверяем, есть ли функция логирования в боте
try:
    from bot import log_user_question as bot_log_function
    print("✅ Функция log_user_question доступна в боте")
except ImportError:
    print("❌ Функция log_user_question недоступна в боте")

print("\n🎯 РЕКОМЕНДАЦИИ:")
print("-" * 30)

if not api_key:
    print("❌ Добавьте GOOGLE_SHEETS_API_KEY в .env файл")
else:
    print("✅ API ключ найден")

if not bot_token:
    print("❌ Добавьте BOT_TOKEN в .env файл")
else:
    print("✅ BOT_TOKEN найден")

try:
    if not google_sheets_logger.enabled:
        print("❌ Google Sheets Logger отключен - проверьте API ключ")
    else:
        print("✅ Google Sheets Logger включен")
except NameError:
    print("❌ Google Sheets Logger недоступен")

print("\n🚀 СЛЕДУЮЩИЕ ШАГИ:")
print("-" * 30)
print("1. Убедитесь, что .env файл содержит все необходимые переменные")
print("2. Запустите бота: python bot.py")
print("3. Отправьте боту несколько вопросов")
print("4. Проверьте логи на наличие сообщений:")
print("   - '✅ Google Sheets интеграция подключена'")
print("   - '✅ Вопрос сохранен в Google Sheets'")
print("5. Откройте Google Sheets и проверьте, появились ли записи")

print("\n🎉 ПРОВЕРКА ЗАВЕРШЕНА!")







