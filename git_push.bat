@echo off
chcp 65001 > nul
echo ============================================================
echo 🚀 ОТПРАВКА ИЗМЕНЕНИЙ В GIT
echo ============================================================
echo.

echo 📋 Добавляем все изменения...
git add .

echo.
echo 💬 Создаём коммит...
git commit -m "🎉 Complete refactoring: Backend API + Frontend Bot

✨ New features:
- Separated monolithic bot into Backend (FastAPI) and Frontend (Aiogram)
- Restored critical LLM functionality with PromptManager
- Enhanced search service with local fallback
- Integrated conversation, cache, and recommendation services
- Added comprehensive error handling and logging

🔧 Improvements:
- Fixed settings.py to use LLM_MODEL instead of OPENROUTER_MODEL
- Updated backend/run_api.py to load .env from project root
- Changed backend host from 0.0.0.0 to 127.0.0.1 for better compatibility
- Improved bot authentication flow with detailed error messages

🧹 Cleanup:
- Removed 280+ temporary test files and debug scripts
- Cleaned up old reports and documentation
- Streamlined project structure

📁 Structure:
backend/    - FastAPI API server
frontend/   - Aiogram bot with services
run_bot.py  - Bot launcher
"

echo.
echo 🌐 Отправляем на GitHub...
git push origin main

echo.
echo ============================================================
echo ✅ ГОТОВО!
echo ============================================================
pause

