"""
API маршруты для работы с пользователями
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from repositories.user_repo import UserRepository
from models.user import (
    UserResponse, UserCreate, UserUpdate, 
    UserListResponse, UserStatsResponse
)

router = APIRouter()


@router.get("/", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(10, ge=1, le=100, description="Размер страницы"),
    db: Session = Depends(get_db)
):
    """Получение списка пользователей с пагинацией"""
    user_repo = UserRepository(db)
    
    skip = (page - 1) * size
    users = user_repo.get_all(skip=skip, limit=size)
    total = user_repo.count()
    pages = (total + size - 1) // size
    
    return UserListResponse(
        users=[UserResponse.from_orm(u) for u in users],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Получение пользователя по Telegram user_id"""
    user_repo = UserRepository(db)
    user = user_repo.get_by_user_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return UserResponse.from_orm(user)


@router.post("/", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Создание нового пользователя"""
    user_repo = UserRepository(db)
    
    # Проверяем, не существует ли уже пользователь
    existing_user = user_repo.get_by_user_id(user_data.user_id)
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    
    user = user_repo.create(user_data)
    return UserResponse.from_orm(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, 
    user_data: UserUpdate, 
    db: Session = Depends(get_db)
):
    """Обновление пользователя"""
    user_repo = UserRepository(db)
    user = user_repo.update(user_id, user_data)
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return UserResponse.from_orm(user)


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Удаление пользователя"""
    user_repo = UserRepository(db)
    success = user_repo.delete(user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return {"message": "Пользователь успешно удален"}


@router.get("/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="Количество дней для статистики"),
    db: Session = Depends(get_db)
):
    """Получение статистики пользователя"""
    user_repo = UserRepository(db)
    
    # Проверяем, существует ли пользователь
    user = user_repo.get_by_user_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    stats = user_repo.get_user_stats(user_id, days)
    return UserStatsResponse(**stats)


@router.post("/{user_id}/action")
async def log_user_action(
    user_id: int,
    action: str,
    metadata: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """Логирование действия пользователя"""
    user_repo = UserRepository(db)
    
    # Проверяем, существует ли пользователь
    user = user_repo.get_by_user_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user_repo.log_user_action(user_id, action, metadata)
    return {"message": "Действие залогировано"}


@router.get("/active/list", response_model=List[UserResponse])
async def get_active_users(
    hours: int = Query(24, ge=1, le=168, description="Количество часов для активности"),
    db: Session = Depends(get_db)
):
    """Получение активных пользователей"""
    user_repo = UserRepository(db)
    users = user_repo.get_active_users(hours)
    return [UserResponse.from_orm(u) for u in users]


@router.get("/recent/list", response_model=List[UserResponse])
async def get_recent_users(
    limit: int = Query(10, ge=1, le=50, description="Количество пользователей"),
    db: Session = Depends(get_db)
):
    """Получение недавно зарегистрированных пользователей"""
    user_repo = UserRepository(db)
    users = user_repo.get_recent_users(limit)
    return [UserResponse.from_orm(u) for u in users]


