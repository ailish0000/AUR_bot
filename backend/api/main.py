"""
Основное FastAPI приложение
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from core.config import settings
from core.database import create_tables
from api.routes import products, search, users, analytics

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan события приложения"""
    # Startup
    try:
        create_tables()
        logger.info("✅ Tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        raise
    
    yield  # Приложение работает
    
    # Shutdown
    logger.info("👋 Application shutting down...")


# Создаем приложение
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API для Telegram бота Aurora",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# CORS middleware - улучшенные настройки
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
] if settings.debug else [
    "https://aur-ora.com",
    "https://www.aur-ora.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Trusted host middleware отключен для разработки
# Для продакшена раскомментировать:
# if not settings.debug:
#     app.add_middleware(
#         TrustedHostMiddleware,
#         allowed_hosts=["aur-ora.com", "*.aur-ora.com"]
#     )

# Подключаем маршруты
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])




@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "Aurora Bot API",
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья API"""
    return {
        "status": "healthy",
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
