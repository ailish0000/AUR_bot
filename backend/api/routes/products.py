"""
API маршруты для работы с продуктами
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from repositories.product_repo import ProductRepository
from models.product import (
    ProductResponse, ProductCreate, ProductUpdate, 
    ProductListResponse, ProductSearchRequest, ProductSearchResponse
)

router = APIRouter()


@router.get("/", response_model=ProductListResponse)
async def get_products(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(10, ge=1, le=100, description="Размер страницы"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    db: Session = Depends(get_db)
):
    """Получение списка продуктов с пагинацией"""
    product_repo = ProductRepository(db)
    
    skip = (page - 1) * size
    
    if category:
        products = product_repo.get_by_category(category, skip=skip, limit=size)
        total = product_repo.count_by_category(category)
    else:
        products = product_repo.get_all(skip=skip, limit=size)
        total = product_repo.count()
    
    pages = (total + size - 1) // size
    
    return ProductListResponse(
        products=[ProductResponse.from_orm(p) for p in products],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db: Session = Depends(get_db)):
    """Получение конкретного продукта по ID"""
    product_repo = ProductRepository(db)
    product = product_repo.get_by_id(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    return ProductResponse.from_orm(product)


@router.post("/", response_model=ProductResponse)
async def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    """Создание нового продукта"""
    product_repo = ProductRepository(db)
    
    # Проверяем, не существует ли уже продукт с таким ID
    existing_product = product_repo.get_by_id(product_data.name.lower().replace(" ", "-"))
    if existing_product:
        raise HTTPException(status_code=400, detail="Продукт с таким названием уже существует")
    
    product = product_repo.create(product_data)
    return ProductResponse.from_orm(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str, 
    product_data: ProductUpdate, 
    db: Session = Depends(get_db)
):
    """Обновление продукта"""
    product_repo = ProductRepository(db)
    product = product_repo.update(product_id, product_data)
    
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    return ProductResponse.from_orm(product)


@router.delete("/{product_id}")
async def delete_product(product_id: str, db: Session = Depends(get_db)):
    """Удаление продукта"""
    product_repo = ProductRepository(db)
    success = product_repo.delete(product_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    return {"message": "Продукт успешно удален"}


@router.get("/categories/list", response_model=List[str])
async def get_categories(db: Session = Depends(get_db)):
    """Получение списка всех категорий"""
    product_repo = ProductRepository(db)
    categories = product_repo.get_categories()
    return categories


@router.get("/popular/list", response_model=List[ProductResponse])
async def get_popular_products(
    limit: int = Query(10, ge=1, le=50, description="Количество продуктов"),
    db: Session = Depends(get_db)
):
    """Получение популярных продуктов"""
    product_repo = ProductRepository(db)
    products = product_repo.get_popular_products(limit=limit)
    return [ProductResponse.from_orm(p) for p in products]


