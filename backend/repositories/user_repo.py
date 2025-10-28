"""
Репозиторий для работы с пользователями
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
from models.user import UserDB, UserStatsDB, UserCreate, UserUpdate


class UserRepository:
    """Репозиторий для работы с пользователями"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user_data: UserCreate) -> UserDB:
        """Создание нового пользователя"""
        db_user = UserDB(**user_data.dict())
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def get_by_user_id(self, user_id: int) -> Optional[UserDB]:
        """Получение пользователя по Telegram user_id"""
        return self.db.query(UserDB).filter(UserDB.user_id == user_id).first()
    
    def get_by_id(self, id: int) -> Optional[UserDB]:
        """Получение пользователя по внутреннему ID"""
        return self.db.query(UserDB).filter(UserDB.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[UserDB]:
        """Получение всех пользователей с пагинацией"""
        return self.db.query(UserDB).offset(skip).limit(limit).all()
    
    def update(self, user_id: int, user_data: UserUpdate) -> Optional[UserDB]:
        """Обновление пользователя"""
        db_user = self.get_by_user_id(user_id)
        if not db_user:
            return None
        
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        # Обновляем время последней активности
        db_user.last_active = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def delete(self, user_id: int) -> bool:
        """Удаление пользователя"""
        db_user = self.get_by_user_id(user_id)
        if not db_user:
            return False
        
        self.db.delete(db_user)
        self.db.commit()
        return True
    
    def count(self) -> int:
        """Подсчет общего количества пользователей"""
        return self.db.query(UserDB).count()
    
    def get_active_users(self, hours: int = 24) -> List[UserDB]:
        """Получение активных пользователей за последние N часов"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return (
            self.db.query(UserDB)
            .filter(UserDB.last_active >= cutoff_time)
            .filter(UserDB.is_active == True)
            .all()
        )
    
    def get_recent_users(self, limit: int = 10) -> List[UserDB]:
        """Получение недавно зарегистрированных пользователей"""
        return (
            self.db.query(UserDB)
            .order_by(desc(UserDB.started_at))
            .limit(limit)
            .all()
        )
    
    def log_user_action(self, user_id: int, action: str, metadata: Optional[Dict[str, Any]] = None):
        """Логирование действия пользователя"""
        user_stats = UserStatsDB(
            user_id=user_id,
            action=action,
            metadata=metadata or {}
        )
        self.db.add(user_stats)
        self.db.commit()
    
    def get_user_stats(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Получение статистики пользователя"""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # Общее количество запросов
        total_queries = (
            self.db.query(UserStatsDB)
            .filter(UserStatsDB.user_id == user_id)
            .filter(UserStatsDB.timestamp >= cutoff_time)
            .count()
        )
        
        # Последняя активность
        last_activity = (
            self.db.query(UserStatsDB.timestamp)
            .filter(UserStatsDB.user_id == user_id)
            .order_by(desc(UserStatsDB.timestamp))
            .first()
        )
        
        # Популярные действия
        popular_actions = (
            self.db.query(UserStatsDB.action, func.count(UserStatsDB.action))
            .filter(UserStatsDB.user_id == user_id)
            .filter(UserStatsDB.timestamp >= cutoff_time)
            .group_by(UserStatsDB.action)
            .order_by(desc(func.count(UserStatsDB.action)))
            .limit(5)
            .all()
        )
        
        return {
            "user_id": user_id,
            "total_queries": total_queries,
            "last_activity": last_activity[0] if last_activity else None,
            "popular_actions": [{"action": action, "count": count} for action, count in popular_actions]
        }
    
    def get_all_user_ids(self) -> List[int]:
        """Получение всех user_id для рассылок"""
        return [user.user_id for user in self.db.query(UserDB).filter(UserDB.is_active == True).all()]


