"""
Репозиторий для работы с продуктами
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from models.product import ProductDB, ProductCreate, ProductUpdate
from core.database import get_db


class ProductRepository:
    """Репозиторий для работы с продуктами"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, product_data: ProductCreate) -> ProductDB:
        """Создание нового продукта"""
        db_product = ProductDB(**product_data.dict())
        self.db.add(db_product)
        self.db.commit()
        self.db.refresh(db_product)
        return db_product
    
    def get_by_id(self, product_id: str) -> Optional[ProductDB]:
        """Получение продукта по ID"""
        return self.db.query(ProductDB).filter(ProductDB.id == product_id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ProductDB]:
        """Получение всех продуктов с пагинацией"""
        return self.db.query(ProductDB).offset(skip).limit(limit).all()
    
    def get_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[ProductDB]:
        """Получение продуктов по категории"""
        return (
            self.db.query(ProductDB)
            .filter(ProductDB.category.ilike(f"%{category}%"))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[ProductDB]:
        """Поиск продуктов по тексту"""
        search_filter = or_(
            ProductDB.name.ilike(f"%{query}%"),
            ProductDB.description.ilike(f"%{query}%"),
            ProductDB.short_description.ilike(f"%{query}%"),
            ProductDB.category.ilike(f"%{query}%"),
            ProductDB.composition.ilike(f"%{query}%")
        )
        
        return (
            self.db.query(ProductDB)
            .filter(search_filter)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def search_advanced(
        self,
        query: str,
        category: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        is_available: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ProductDB]:
        """Расширенный поиск продуктов"""
        filters = []
        
        # Текстовый поиск
        if query:
            text_filter = or_(
                ProductDB.name.ilike(f"%{query}%"),
                ProductDB.description.ilike(f"%{query}%"),
                ProductDB.short_description.ilike(f"%{query}%"),
                ProductDB.category.ilike(f"%{query}%"),
                ProductDB.composition.ilike(f"%{query}%")
            )
            filters.append(text_filter)
        
        # Фильтр по категории
        if category:
            filters.append(ProductDB.category.ilike(f"%{category}%"))
        
        # Фильтр по цене
        if price_min is not None:
            filters.append(ProductDB.price >= price_min)
        if price_max is not None:
            filters.append(ProductDB.price <= price_max)
        
        # Фильтр по доступности
        if is_available is not None:
            filters.append(ProductDB.is_available == is_available)
        
        # Фильтр по тегам (если поддерживается JSON поиск)
        if tags:
            for tag in tags:
                filters.append(ProductDB.tags.contains([tag]))
        
        # Применяем все фильтры
        query_obj = self.db.query(ProductDB)
        if filters:
            query_obj = query_obj.filter(and_(*filters))
        
        return query_obj.offset(skip).limit(limit).all()
    
    def update(self, product_id: str, product_data: ProductUpdate) -> Optional[ProductDB]:
        """Обновление продукта"""
        db_product = self.get_by_id(product_id)
        if not db_product:
            return None
        
        update_data = product_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_product, field, value)
        
        self.db.commit()
        self.db.refresh(db_product)
        return db_product
    
    def delete(self, product_id: str) -> bool:
        """Удаление продукта"""
        db_product = self.get_by_id(product_id)
        if not db_product:
            return False
        
        self.db.delete(db_product)
        self.db.commit()
        return True
    
    def count(self) -> int:
        """Подсчет общего количества продуктов"""
        return self.db.query(ProductDB).count()
    
    def count_by_category(self, category: str) -> int:
        """Подсчет продуктов по категории"""
        return (
            self.db.query(ProductDB)
            .filter(ProductDB.category.ilike(f"%{category}%"))
            .count()
        )
    
    def get_categories(self) -> List[str]:
        """Получение списка всех категорий"""
        categories = (
            self.db.query(ProductDB.category)
            .filter(ProductDB.category.isnot(None))
            .distinct()
            .all()
        )
        return [cat[0] for cat in categories if cat[0]]
    
    def get_popular_products(self, limit: int = 10) -> List[ProductDB]:
        """Получение популярных продуктов"""
        return (
            self.db.query(ProductDB)
            .filter(ProductDB.is_available == True)
            .order_by(ProductDB.rating.desc(), ProductDB.review_count.desc())
            .limit(limit)
            .all()
        )


