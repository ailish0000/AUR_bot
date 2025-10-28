"""
Подключение к базе данных
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from core.config import settings
from core.base import Base

# Создаем движок базы данных
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(settings.database_url)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Получение сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Создание таблиц в базе данных"""
    # Импортируем все модели для регистрации
    from models.product import ProductDB
    from models.user import UserDB, UserStatsDB
    
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы успешно")


def drop_tables():
    """Удаление всех таблиц"""
    Base.metadata.drop_all(bind=engine)
