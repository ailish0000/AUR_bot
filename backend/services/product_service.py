"""
Сервис для работы с продуктами
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from repositories.product_repo import ProductRepository
from models.product import (
    ProductResponse, ProductCreate, ProductUpdate,
    ProductSearchRequest, ProductSearchResponse
)
import time


class ProductService:
    """Сервис для работы с продуктами"""
    
    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)
    
    def get_products(self, page: int = 1, size: int = 10, category: Optional[str] = None) -> Dict[str, Any]:
        """Получение списка продуктов с пагинацией"""
        skip = (page - 1) * size
        
        if category:
            products = self.product_repo.get_by_category(category, skip=skip, limit=size)
            total = self.product_repo.count_by_category(category)
        else:
            products = self.product_repo.get_all(skip=skip, limit=size)
            total = self.product_repo.count()
        
        pages = (total + size - 1) // size
        
        return {
            "products": [ProductResponse.from_orm(p) for p in products],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }
    
    def get_product(self, product_id: str) -> Optional[ProductResponse]:
        """Получение продукта по ID"""
        product = self.product_repo.get_by_id(product_id)
        if not product:
            return None
        return ProductResponse.from_orm(product)
    
    def create_product(self, product_data: ProductCreate) -> ProductResponse:
        """Создание нового продукта"""
        product = self.product_repo.create(product_data)
        return ProductResponse.from_orm(product)
    
    def update_product(self, product_id: str, product_data: ProductUpdate) -> Optional[ProductResponse]:
        """Обновление продукта"""
        product = self.product_repo.update(product_id, product_data)
        if not product:
            return None
        return ProductResponse.from_orm(product)
    
    def delete_product(self, product_id: str) -> bool:
        """Удаление продукта"""
        return self.product_repo.delete(product_id)
    
    def search_products(self, search_request: ProductSearchRequest) -> ProductSearchResponse:
        """Поиск продуктов"""
        start_time = time.time()
        
        products = self.product_repo.search_advanced(
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
    
    def get_categories(self) -> List[str]:
        """Получение списка категорий"""
        return self.product_repo.get_categories()
    
    def get_popular_products(self, limit: int = 10) -> List[ProductResponse]:
        """Получение популярных продуктов"""
        products = self.product_repo.get_popular_products(limit)
        return [ProductResponse.from_orm(p) for p in products]
    
    def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Получение поисковых подсказок"""
        products = self.product_repo.search(query, skip=0, limit=limit)
        
        suggestions = []
        seen = set()
        
        for product in products:
            name = product.name
            if name.lower().startswith(query.lower()) and name not in seen:
                suggestions.append(name)
                seen.add(name)
        
        return suggestions[:limit]


