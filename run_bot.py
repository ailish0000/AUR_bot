"""
Bot launcher - Run the Telegram bot
"""
import sys
import os
import asyncio
import signal

# Добавляем корневую директорию в path
sys.path.insert(0, '.')


def validate_env():
    """Проверка обязательных переменных окружения"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required = {
        "BOT_TOKEN": "Telegram Bot Token",
    }
    
    recommended = {
        "OPENROUTER_API_KEY": "OpenRouter API Key (или OPENAI_API_KEY)",
        "BACKEND_API_URL": "URL Backend API",
    }
    
    missing_required = []
    missing_recommended = []
    
    # Проверяем обязательные
    for var, description in required.items():
        if not os.getenv(var):
            missing_required.append(f"  ❌ {var}: {description}")
    
    # Проверяем рекомендованные
    for var, description in recommended.items():
        if var == "OPENROUTER_API_KEY":
            if not os.getenv(var) and not os.getenv("OPENAI_API_KEY"):
                missing_recommended.append(f"  ⚠️  {var}: {description}")
        elif not os.getenv(var):
            missing_recommended.append(f"  ⚠️  {var}: {description}")
    
    if missing_required:
        print("❌ ОШИБКА: Отсутствуют обязательные переменные окружения:")
        print("\n".join(missing_required))
        print("\n💡 Создайте файл .env на основе env_example.txt")
        sys.exit(1)
    
    if missing_recommended:
        print("⚠️  Предупреждение: Отсутствуют рекомендованные переменные:")
        print("\n".join(missing_recommended))
        print("   Бот будет работать с ограниченным функционалом\n")
    else:
        print("✅ Все переменные окружения установлены")


def print_versions():
    """Вывод версий используемых библиотек"""
    try:
        import aiogram
        import sqlalchemy
        
        print(f"📦 Python: {sys.version.split()[0]}")
        print(f"📦 Aiogram: {aiogram.__version__}")
        print(f"📦 SQLAlchemy: {sqlalchemy.__version__}")
    except ImportError as e:
        print(f"⚠️  Не удалось определить версии: {e}")
    print("-" * 50)


def signal_handler(sig, frame):
    """Обработчик сигнала остановки"""
    print('\n\n👋 Получен сигнал остановки...')
    print('🔄 Завершение работы бота...')
    sys.exit(0)


if __name__ == "__main__":
    # Регистрируем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        print("=" * 50)
        print("🔍 Проверка конфигурации...")
        print("-" * 50)
        validate_env()
        print_versions()
        print("=" * 50)
        print("🚀 Запуск Aurora Bot...")
        print("=" * 50)
        
        from frontend.bot.main import main
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
