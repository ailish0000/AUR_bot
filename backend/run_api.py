"""
Скрипт запуска Backend API
"""
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь для загрузки .env
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Загружаем .env из корня проекта
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

import uvicorn
from core.config import settings

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Backend API Starting...")
    print(f"📍 URL: http://127.0.0.1:8000")
    print(f"📍 Docs: http://127.0.0.1:8000/docs")
    print("=" * 60)
    
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",  # Изменено с 0.0.0.0 на 127.0.0.1
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


