"""
Модели для продуктов
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from core.base import Base


class ProductDB(Base):
    """Модель продукта в базе данных"""
    __tablename__ = "products"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    short_description = Column(Text)
    category = Column(String, index=True)
    price = Column(Float)
    benefits = Column(JSON)  # List[str]
    short_benefits = Column(JSON)  # List[str]
    composition = Column(Text)
    dosage = Column(Text)
    contraindications = Column(Text)
    indications = Column(JSON)  # List[str]
    properties = Column(JSON)  # List[str]
    components = Column(JSON)  # List[str]
    image_id = Column(String)
    url = Column(String)
    form = Column(String)
    weight = Column(String)
    volume = Column(String)
    is_available = Column(Boolean, default=True)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    tags = Column(JSON)  # List[str]
    product_metadata = Column(JSON)  # Dict[str, Any]
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# Pydantic модели для API
class ProductBase(BaseModel):
    """Базовая модель продукта"""
    name: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    benefits: List[str] = Field(default_factory=list)
    short_benefits: List[str] = Field(default_factory=list)
    composition: Optional[str] = None
    dosage: Optional[str] = None
    contraindications: Optional[str] = None
    indications: List[str] = Field(default_factory=list)
    properties: List[str] = Field(default_factory=list)
    components: List[str] = Field(default_factory=list)
    image_id: Optional[str] = None
    url: Optional[str] = None
    form: Optional[str] = None
    weight: Optional[str] = None
    volume: Optional[str] = None
    is_available: bool = True
    rating: float = 0.0
    review_count: int = 0
    tags: List[str] = Field(default_factory=list)
    product_metadata: Dict[str, Any] = Field(default_factory=dict)


class ProductCreate(ProductBase):
    """Модель для создания продукта"""
    id: Optional[str] = None


class ProductUpdate(BaseModel):
    """Модель для обновления продукта"""
    name: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    benefits: Optional[List[str]] = None
    short_benefits: Optional[List[str]] = None
    composition: Optional[str] = None
    dosage: Optional[str] = None
    contraindications: Optional[str] = None
    indications: Optional[List[str]] = None
    properties: Optional[List[str]] = None
    components: Optional[List[str]] = None
    image_id: Optional[str] = None
    url: Optional[str] = None
    form: Optional[str] = None
    weight: Optional[str] = None
    volume: Optional[str] = None
    is_available: Optional[bool] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    tags: Optional[List[str]] = None
    product_metadata: Optional[Dict[str, Any]] = None


class ProductResponse(ProductBase):
    """Модель ответа с продуктом"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Модель ответа со списком продуктов"""
    products: List[ProductResponse]
    total: int
    page: int
    size: int
    pages: int


class ProductSearchRequest(BaseModel):
    """Модель запроса поиска"""
    query: str
    category: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    is_available: Optional[bool] = None
    tags: Optional[List[str]] = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ProductSearchResponse(BaseModel):
    """Модель ответа поиска"""
    products: List[ProductResponse]
    total_found: int
    search_time: float
    search_type: str
