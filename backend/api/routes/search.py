"""
API маршруты для поиска
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import time
from core.database import get_db
from repositories.product_repo import ProductRepository
from models.product import ProductResponse, ProductSearchRequest, ProductSearchResponse

router = APIRouter()


@router.post("/query", response_model=ProductSearchResponse)
async def search_products(
    search_request: ProductSearchRequest,
    db: Session = Depends(get_db)
):
    """Поиск продуктов по запросу"""
    start_time = time.time()
    
    product_repo = ProductRepository(db)
    
    # Выполняем поиск
    products = product_repo.search_advanced(
        query=search_request.query,
        category=search_request.category,
        price_min=search_request.price_min,
        price_max=search_request.price_max,
        is_available=search_request.is_available,
        tags=search_request.tags,
        skip=search_request.offset,
        limit=search_request.limit
    )
    
    search_time = time.time() - start_time
    
    return ProductSearchResponse(
        products=[ProductResponse.from_orm(p) for p in products],
        total_found=len(products),
        search_time=search_time,
        search_type="database_search"
    )


@router.get("/suggestions", response_model=List[str])
async def get_search_suggestions(
    query: str = Query(..., min_length=2, description="Поисковый запрос"),
    limit: int = Query(10, ge=1, le=20, description="Количество подсказок"),
    db: Session = Depends(get_db)
):
    """Получение поисковых подсказок"""
    product_repo = ProductRepository(db)
    
    # Получаем продукты, которые начинаются с запроса
    products = product_repo.search(query, skip=0, limit=limit)
    
    # Извлекаем уникальные названия для подсказок
    suggestions = []
    seen = set()
    
    for product in products:
        name = product.name
        if name.lower().startswith(query.lower()) and name not in seen:
            suggestions.append(name)
            seen.add(name)
    
    return suggestions[:limit]


@router.get("/categories", response_model=List[str])
async def search_categories(
    query: str = Query(..., min_length=1, description="Поиск по категориям"),
    db: Session = Depends(get_db)
):
    """Поиск категорий по запросу"""
    product_repo = ProductRepository(db)
    all_categories = product_repo.get_categories()
    
    # Фильтруем категории по запросу
    matching_categories = [
        cat for cat in all_categories 
        if query.lower() in cat.lower()
    ]
    
    return matching_categories


@router.get("/quick", response_model=List[ProductResponse])
async def quick_search(
    q: str = Query(..., min_length=2, description="Быстрый поиск"),
    limit: int = Query(5, ge=1, le=10, description="Количество результатов"),
    db: Session = Depends(get_db)
):
    """Быстрый поиск для автодополнения"""
    product_repo = ProductRepository(db)
    products = product_repo.search(q, skip=0, limit=limit)
    
    return [ProductResponse.from_orm(p) for p in products]


