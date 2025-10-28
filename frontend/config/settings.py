"""
Configuration settings for Frontend bot
"""
import os
from dotenv import load_dotenv
from typing import Optional

# Загружаем переменные окружения
load_dotenv()


class Settings:
    """Application settings"""
    
    # Bot settings
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_NAME: str = "AI-помощник AURORA"
    
    # API settings
    BACKEND_API_URL: str = os.getenv("BACKEND_API_URL", "http://localhost:8000")
    
    # LLM settings
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    
    # Database settings
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "bot_database.db")
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", ":memory:")
    
    # Google Sheets settings
    GOOGLE_SHEET_ID: Optional[str] = os.getenv("GOOGLE_SHEET_ID")
    SERVICE_ACCOUNT_FILE: Optional[str] = os.getenv("SERVICE_ACCOUNT_FILE")
    
    # Cache settings
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    CACHE_SIZE: int = int(os.getenv("CACHE_SIZE", "100"))
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    
    # Features flags
    ENABLE_SMART_SEARCH: bool = os.getenv("ENABLE_SMART_SEARCH", "true").lower() == "true"
    ENABLE_RECOMMENDATIONS: bool = os.getenv("ENABLE_RECOMMENDATIONS", "true").lower() == "true"
    ENABLE_CONVERSATION_MEMORY: bool = os.getenv("ENABLE_CONVERSATION_MEMORY", "true").lower() == "true"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required settings"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        return True


# Создаем глобальный экземпляр настроек
settings = Settings()

# Валидируем настройки при импорте
settings.validate()
