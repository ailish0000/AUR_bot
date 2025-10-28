"""
API маршруты для аналитики
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from core.database import get_db
from repositories.user_repo import UserRepository
from repositories.product_repo import ProductRepository

router = APIRouter()


@router.get("/stats")
async def get_general_stats(
    days: int = Query(7, ge=1, le=365, description="Количество дней для статистики"),
    db: Session = Depends(get_db)
):
    """Получение общей статистики"""
    user_repo = UserRepository(db)
    product_repo = ProductRepository(db)
    
    # Общее количество пользователей
    total_users = user_repo.count()
    
    # Активные пользователи за период
    active_users = len(user_repo.get_active_users(days * 24))
    
    # Общее количество продуктов
    total_products = product_repo.count()
    
    # Популярные категории
    categories = product_repo.get_categories()
    
    # Статистика по действиям пользователей
    cutoff_time = datetime.utcnow() - timedelta(days=days)
    
    return {
        "period_days": days,
        "total_users": total_users,
        "active_users": active_users,
        "total_products": total_products,
        "categories_count": len(categories),
        "popular_categories": categories[:5],
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/users/stats")
async def get_users_analytics(
    days: int = Query(7, ge=1, le=365, description="Количество дней для статистики"),
    db: Session = Depends(get_db)
):
    """Аналитика по пользователям"""
    user_repo = UserRepository(db)
    
    # Активные пользователи
    active_1d = len(user_repo.get_active_users(24))
    active_7d = len(user_repo.get_active_users(168))
    active_30d = len(user_repo.get_active_users(720))
    
    # Недавние пользователи
    recent_users = user_repo.get_recent_users(10)
    
    return {
        "period_days": days,
        "active_users": {
            "last_24h": active_1d,
            "last_7d": active_7d,
            "last_30d": active_30d
        },
        "recent_registrations": len(recent_users),
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/products/stats")
async def get_products_analytics(db: Session = Depends(get_db)):
    """Аналитика по продуктам"""
    product_repo = ProductRepository(db)
    
    # Общая статистика
    total_products = product_repo.count()
    categories = product_repo.get_categories()
    
    # Популярные продукты
    popular_products = product_repo.get_popular_products(10)
    
    # Статистика по категориям
    category_stats = {}
    for category in categories:
        count = product_repo.count_by_category(category)
        category_stats[category] = count
    
    return {
        "total_products": total_products,
        "categories_count": len(categories),
        "category_distribution": category_stats,
        "popular_products": [
            {
                "name": p.name,
                "rating": p.rating,
                "review_count": p.review_count
            } for p in popular_products
        ],
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/queries/stats")
async def get_queries_analytics(
    days: int = Query(7, ge=1, le=365, description="Количество дней для статистики"),
    db: Session = Depends(get_db)
):
    """Аналитика по запросам"""
    user_repo = UserRepository(db)
    
    # Получаем статистику запросов за период
    cutoff_time = datetime.utcnow() - timedelta(days=days)
    
    # Здесь можно добавить более детальную аналитику запросов
    # когда будет реализована система логирования запросов
    
    return {
        "period_days": days,
        "message": "Аналитика запросов будет доступна после реализации системы логирования",
        "generated_at": datetime.utcnow().isoformat()
    }


