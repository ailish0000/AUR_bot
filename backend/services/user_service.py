"""
Сервис для работы с пользователями
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from repositories.user_repo import UserRepository
from models.user import UserResponse, UserCreate, UserUpdate, UserStatsResponse


class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def get_users(self, page: int = 1, size: int = 10) -> Dict[str, Any]:
        """Получение списка пользователей с пагинацией"""
        skip = (page - 1) * size
        users = self.user_repo.get_all(skip=skip, limit=size)
        total = self.user_repo.count()
        pages = (total + size - 1) // size
        
        return {
            "users": [UserResponse.from_orm(u) for u in users],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }
    
    def get_user(self, user_id: int) -> Optional[UserResponse]:
        """Получение пользователя по Telegram user_id"""
        user = self.user_repo.get_by_user_id(user_id)
        if not user:
            return None
        return UserResponse.from_orm(user)
    
    def create_user(self, user_data: UserCreate) -> UserResponse:
        """Создание нового пользователя"""
        user = self.user_repo.create(user_data)
        return UserResponse.from_orm(user)
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[UserResponse]:
        """Обновление пользователя"""
        user = self.user_repo.update(user_id, user_data)
        if not user:
            return None
        return UserResponse.from_orm(user)
    
    def delete_user(self, user_id: int) -> bool:
        """Удаление пользователя"""
        return self.user_repo.delete(user_id)
    
    def get_user_stats(self, user_id: int, days: int = 30) -> UserStatsResponse:
        """Получение статистики пользователя"""
        stats = self.user_repo.get_user_stats(user_id, days)
        return UserStatsResponse(**stats)
    
    def log_user_action(self, user_id: int, action: str, metadata: Optional[Dict[str, Any]] = None):
        """Логирование действия пользователя"""
        self.user_repo.log_user_action(user_id, action, metadata)
    
    def get_active_users(self, hours: int = 24) -> List[UserResponse]:
        """Получение активных пользователей"""
        users = self.user_repo.get_active_users(hours)
        return [UserResponse.from_orm(u) for u in users]
    
    def get_recent_users(self, limit: int = 10) -> List[UserResponse]:
        """Получение недавно зарегистрированных пользователей"""
        users = self.user_repo.get_recent_users(limit)
        return [UserResponse.from_orm(u) for u in users]
    
    def get_all_user_ids(self) -> List[int]:
        """Получение всех user_id для рассылок"""
        return self.user_repo.get_all_user_ids()


