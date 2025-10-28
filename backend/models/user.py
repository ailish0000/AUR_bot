"""
Модели для пользователей
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from core.base import Base


class UserDB(Base):
    """Модель пользователя в базе данных"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True, nullable=False)  # Telegram user ID
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    started_at = Column(DateTime, default=func.now())
    last_active = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    preferences = Column(JSON)  # Dict[str, Any]
    user_metadata = Column(JSON)  # Dict[str, Any]


class UserStatsDB(Base):
    """Модель статистики пользователя"""
    __tablename__ = "user_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    user_metadata = Column(JSON)  # Dict[str, Any]


# Pydantic модели для API
class UserBase(BaseModel):
    """Базовая модель пользователя"""
    user_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserCreate(UserBase):
    """Модель для создания пользователя"""
    pass


class UserUpdate(BaseModel):
    """Модель для обновления пользователя"""
    username: Optional[str] = None
    full_name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    """Модель ответа с пользователем"""
    id: int
    started_at: datetime
    last_active: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """Модель ответа со статистикой пользователя"""
    user_id: int
    total_queries: int
    last_activity: datetime
    favorite_categories: List[str]
    total_products_viewed: int


class UserListResponse(BaseModel):
    """Модель ответа со списком пользователей"""
    users: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int
