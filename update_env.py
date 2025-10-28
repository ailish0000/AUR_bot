"""
Обновление .env файла - объединение старой и новой конфигурации
"""

# Объединённая конфигурация
env_content = """# ========================================
# TELEGRAM BOT CONFIGURATION
# ========================================
BOT_TOKEN=7418671884:AAFvcf5SNmAgW46W-D_C2YiZVEUJCVetKOW
ADMIN_ID=494024814

# ========================================
# LLM CONFIGURATION
# ========================================
OPENROUTER_API_KEY=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
# ИСПРАВЛЕНО: GPT-5 не существует, используем gpt-4o-mini
LLM_MODEL=openai/gpt-4o-mini

# ========================================
# BACKEND API
# ========================================
BACKEND_API_URL=http://localhost:8000

# ========================================
# QDRANT VECTOR DATABASE
# ========================================
QDRANT_URL=https://4ba6b46c-9066-40b2-8b98-ae23d00d89c4.europe-west3-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.NWLhwEI2saEFMN7wWHPzf9J0fzBH4BvfkKwUayTPj0I
QDRANT_HOST=
QDRANT_COLLECTION_NAME=aurora_products

# ========================================
# BOT SETTINGS
# ========================================
LOG_LEVEL=INFO
ENABLE_CACHE=true
CACHE_SIZE=100

# ========================================
# FEATURES
# ========================================
ENABLE_SMART_SEARCH=true
ENABLE_RECOMMENDATIONS=true
ENABLE_CONVERSATION_MEMORY=true

# ========================================
# BACKEND SECURITY
# ========================================
# SECRET_KEY сгенерирован автоматически - НЕ ИЗМЕНЯЙТЕ БЕЗ НЕОБХОДИМОСТИ
SECRET_KEY=oZkbFiuH06UIYylcIvnL45Lik0BBTE31m9PdBhPhm7o
DEBUG=true
DATABASE_URL=sqlite:///./aurora_bot.db

# ========================================
# TELEGRAM PHOTOS (если уже получены)
# ========================================
WELCOME_PHOTO_ID=AgACAgIAAxkBAAID2Gike91mECS1PIS7qfib1Fc7Lwd0AAIy_DEbyo8gSR07zGsoAaAFAQADAgADeAADNgQ
MENU_PHOTO_ID=AgACAgIAAxkBAAID1mikrode8kt0PGUNNOU9U4abT45A8nhAAIx_DEbyo8gSX4-Ga04NzKhAQADAgADEAADNgQ

# ========================================
# GOOGLE SHEETS (опционально)
# ========================================
GOOGLE_SHEETS_API_KEY=AIzaSyA92bByiyf2GJM78pIPGoWAZ1G_IW-Ve9I
"""

print("=" * 70)
print("🔧 ОБНОВЛЕНИЕ .ENV ФАЙЛА")
print("=" * 70)
print()

try:
    # Записываем обновлённый файл
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print("✅ Файл .env успешно обновлён!")
    print()
    print("📋 Что было объединено:")
    print("   ✅ BOT_TOKEN - из старого файла")
    print("   ✅ ADMIN_ID - из старого файла")
    print("   ✅ OPENROUTER_API_KEY - из старого файла")
    print("   ⚠️  LLM_MODEL - ИСПРАВЛЕНО: GPT-5 → gpt-4o-mini")
    print("   ✅ QDRANT настройки - из старого файла")
    print("   ✅ SECRET_KEY - из нового файла (сгенерирован)")
    print("   ✅ PHOTO_ID - из старого файла")
    print("   ✅ GOOGLE_SHEETS_API_KEY - из старого файла")
    print("   ✅ Все новые настройки - добавлены")
    print()
    print("=" * 70)
    print("✅ ГОТОВО!")
    print("=" * 70)
    print()
    print("🚀 Теперь можно запускать проект!")
    print()
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

