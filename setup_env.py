"""
Автоматическая настройка .env файла
"""
import os
import secrets
from pathlib import Path

def setup_env():
    """Создание .env файла с необходимыми настройками"""
    
    print("=" * 70)
    print("🔧 НАСТРОЙКА .ENV ФАЙЛА")
    print("=" * 70)
    print()
    
    # Проверяем существует ли .env
    env_path = Path(".env")
    
    if env_path.exists():
        print("⚠️  Файл .env уже существует!")
        response = input("   Хотите перезаписать его? (yes/no): ").lower()
        if response not in ['yes', 'y', 'да', 'д']:
            print("   Операция отменена.")
            return
        print()
    
    # Генерируем SECRET_KEY
    print("🔐 Генерация SECRET_KEY...")
    secret_key = secrets.token_urlsafe(32)
    print(f"   ✅ Сгенерирован: {secret_key[:20]}...{secret_key[-10:]}")
    print()
    
    # Спрашиваем о BOT_TOKEN
    print("📱 Telegram Bot Token")
    bot_token = input("   Введите ваш BOT_TOKEN (или нажмите Enter для примера): ").strip()
    if not bot_token:
        bot_token = "your_telegram_bot_token_here"
        print(f"   ⚠️  Используется заглушка. Замените позже!")
    else:
        print(f"   ✅ Установлен")
    print()
    
    # Спрашиваем о OpenRouter API Key
    print("🤖 OpenRouter API Key")
    openrouter_key = input("   Введите OPENROUTER_API_KEY (или нажмите Enter для пропуска): ").strip()
    if not openrouter_key:
        openrouter_key = "your_openrouter_api_key_here"
        print(f"   ⚠️  Не установлен. Бот будет работать без LLM")
    else:
        print(f"   ✅ Установлен")
    print()
    
    # Создаем содержимое .env
    env_content = f"""# Telegram Bot Configuration
BOT_TOKEN={bot_token}
ADMIN_ID=your_admin_telegram_id_here

# LLM Configuration
OPENROUTER_API_KEY={openrouter_key}
LLM_MODEL=openai/gpt-4o-mini

# Backend API
BACKEND_API_URL=http://localhost:8000

# Qdrant Vector Database (опционально)
QDRANT_HOST=
QDRANT_API_KEY=
QDRANT_COLLECTION_NAME=aurora_products

# Bot Settings
LOG_LEVEL=INFO
ENABLE_CACHE=true
CACHE_SIZE=100

# Features
ENABLE_SMART_SEARCH=true
ENABLE_RECOMMENDATIONS=true
ENABLE_CONVERSATION_MEMORY=true

# Backend Security (для backend/api)
SECRET_KEY={secret_key}
DEBUG=true
DATABASE_URL=sqlite:///./aurora_bot.db
"""
    
    # Записываем файл
    print("💾 Создание .env файла...")
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print("   ✅ Файл .env создан успешно!")
    print()
    
    # Итоговая информация
    print("=" * 70)
    print("✅ НАСТРОЙКА ЗАВЕРШЕНА")
    print("=" * 70)
    print()
    print("📋 Что было настроено:")
    print(f"   • SECRET_KEY: {secret_key[:20]}...{secret_key[-10:]}")
    print(f"   • BOT_TOKEN: {'✅ установлен' if bot_token != 'your_telegram_bot_token_here' else '⚠️  требует замены'}")
    print(f"   • OPENROUTER_API_KEY: {'✅ установлен' if openrouter_key != 'your_openrouter_api_key_here' else '⚠️  не установлен'}")
    print()
    
    if bot_token == "your_telegram_bot_token_here":
        print("⚠️  ВАЖНО: Обновите BOT_TOKEN в файле .env!")
        print("   Получите токен у @BotFather в Telegram")
        print()
    
    if openrouter_key == "your_openrouter_api_key_here":
        print("⚠️  ВНИМАНИЕ: OPENROUTER_API_KEY не установлен")
        print("   Бот будет работать с ограниченным функционалом")
        print("   Получите ключ на https://openrouter.ai/")
        print()
    
    print("🚀 Теперь можно запускать проект!")
    print("   Backend: cd backend && python run_api.py")
    print("   Frontend: python run_bot.py")
    print()


if __name__ == "__main__":
    try:
        setup_env()
    except KeyboardInterrupt:
        print("\n\n⛔ Настройка отменена пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

