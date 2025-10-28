"""
Cache Service - кэширование ответов для быстрого доступа
"""
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Запись в кэше"""
    key: str
    value: str
    created_at: datetime = field(default_factory=datetime.now)
    hits: int = 0
    
    def is_expired(self, ttl_minutes: int) -> bool:
        """Проверка истечения срока жизни"""
        expiry_time = self.created_at + timedelta(minutes=ttl_minutes)
        return datetime.now() > expiry_time


class CacheService:
    """Сервис кэширования ответов"""
    
    def __init__(
        self,
        max_size: int = 100,
        ttl_minutes: int = 60
    ):
        """
        Инициализация сервиса кэширования
        
        Args:
            max_size: Максимальный размер кэша
            ttl_minutes: Время жизни записи в минутах
        """
        self.max_size = max_size
        self.ttl_minutes = ttl_minutes
        self.cache: Dict[str, CacheEntry] = {}
        logger.info(f"Cache Service initialized (size={max_size}, ttl={ttl_minutes}min)")
    
    def _normalize_key(self, key: str) -> str:
        """Нормализация ключа для кэша"""
        return key.lower().strip()
    
    def get(self, key: str) -> Optional[str]:
        """
        Получить значение из кэша
        
        Args:
            key: Ключ запроса
        
        Returns:
            Закэшированное значение или None
        """
        normalized_key = self._normalize_key(key)
        
        if normalized_key not in self.cache:
            logger.debug(f"Cache miss for key: {key[:50]}...")
            return None
        
        entry = self.cache[normalized_key]
        
        # Проверяем срок жизни
        if entry.is_expired(self.ttl_minutes):
            logger.debug(f"Cache entry expired for key: {key[:50]}...")
            del self.cache[normalized_key]
            return None
        
        # Увеличиваем счетчик попаданий
        entry.hits += 1
        logger.debug(f"Cache hit for key: {key[:50]}... (hits={entry.hits})")
        
        return entry.value
    
    def set(self, key: str, value: str):
        """
        Сохранить значение в кэш
        
        Args:
            key: Ключ запроса
            value: Значение для кэширования
        """
        # Не кэшируем слишком короткие запросы
        if len(key.strip()) < 10:
            return
        
        normalized_key = self._normalize_key(key)
        
        # Проверяем размер кэша
        if len(self.cache) >= self.max_size:
            self._evict_least_used()
        
        # Сохраняем в кэш
        self.cache[normalized_key] = CacheEntry(
            key=normalized_key,
            value=value
        )
        
        logger.debug(f"Cached response for key: {key[:50]}...")
    
    def _evict_least_used(self):
        """Удаляет наименее используемую запись"""
        if not self.cache:
            return
        
        # Находим запись с наименьшим количеством попаданий
        least_used_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].hits
        )
        
        logger.debug(f"Evicting least used entry: {least_used_key[:50]}...")
        del self.cache[least_used_key]
    
    def clear(self):
        """Очистить весь кэш"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def clear_expired(self):
        """Удалить устаревшие записи"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired(self.ttl_minutes)
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict:
        """Получить статистику кэша"""
        total_hits = sum(entry.hits for entry in self.cache.values())
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "total_hits": total_hits,
            "avg_hits": total_hits / len(self.cache) if self.cache else 0,
            "ttl_minutes": self.ttl_minutes
        }
    
    def get_top_cached(self, limit: int = 10) -> list:
        """
        Получить наиболее часто используемые записи
        
        Args:
            limit: Количество записей
        
        Returns:
            Список (ключ, hits)
        """
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1].hits,
            reverse=True
        )
        
        return [
            (key, entry.hits)
            for key, entry in sorted_entries[:limit]
        ]


# Создаем глобальный экземпляр сервиса
cache_service = CacheService()
