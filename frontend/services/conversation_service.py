"""
Conversation Service - управление контекстом разговора
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """Сообщение в разговоре"""
    role: str  # user или assistant
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """Контекст разговора"""
    user_id: int
    messages: List[ConversationMessage] = field(default_factory=list)
    current_topic: Optional[str] = None
    last_products: List[Dict] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)


class ConversationService:
    """Сервис управления разговором"""
    
    def __init__(self, max_history: int = 10):
        """
        Инициализация сервиса разговора
        
        Args:
            max_history: максимальное количество сообщений в истории
        """
        self.max_history = max_history
        self.conversations: Dict[int, ConversationContext] = {}
        logger.info(f"Conversation Service initialized (max_history={max_history})")
    
    def get_or_create_context(self, user_id: int) -> ConversationContext:
        """
        Получить или создать контекст разговора
        
        Args:
            user_id: ID пользователя
        
        Returns:
            Контекст разговора
        """
        if user_id not in self.conversations:
            self.conversations[user_id] = ConversationContext(user_id=user_id)
            logger.info(f"Created new conversation context for user {user_id}")
        
        return self.conversations[user_id]
    
    def add_message(
        self,
        user_id: int,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """
        Добавить сообщение в историю
        
        Args:
            user_id: ID пользователя
            role: роль (user или assistant)
            content: содержимое сообщения
            metadata: дополнительные данные
        """
        context = self.get_or_create_context(user_id)
        
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        context.messages.append(message)
        
        # Ограничиваем историю
        if len(context.messages) > self.max_history:
            context.messages = context.messages[-self.max_history:]
        
        logger.debug(f"Added message from {role} for user {user_id}")
    
    def get_history(
        self,
        user_id: int,
        limit: Optional[int] = None
    ) -> List[ConversationMessage]:
        """
        Получить историю сообщений
        
        Args:
            user_id: ID пользователя
            limit: ограничение количества сообщений
        
        Returns:
            Список сообщений
        """
        context = self.get_or_create_context(user_id)
        
        if limit:
            return context.messages[-limit:]
        return context.messages
    
    def get_context_summary(self, user_id: int) -> str:
        """
        Получить краткое резюме контекста
        
        Args:
            user_id: ID пользователя
        
        Returns:
            Текстовое резюме
        """
        context = self.get_or_create_context(user_id)
        
        if not context.messages:
            return "Новый разговор"
        
        parts = []
        
        if context.current_topic:
            parts.append(f"Тема: {context.current_topic}")
        
        # Последние 3 сообщения
        recent = context.messages[-3:]
        for msg in recent:
            parts.append(f"{msg.role}: {msg.content[:50]}...")
        
        return "\n".join(parts)
    
    def set_topic(self, user_id: int, topic: str):
        """Установить текущую тему разговора"""
        context = self.get_or_create_context(user_id)
        context.current_topic = topic
        logger.info(f"Set topic for user {user_id}: {topic}")
    
    def set_last_products(self, user_id: int, products: List[Dict]):
        """Сохранить последние показанные продукты"""
        context = self.get_or_create_context(user_id)
        context.last_products = products
        logger.debug(f"Saved {len(products)} products for user {user_id}")
    
    def get_last_products(self, user_id: int) -> List[Dict]:
        """Получить последние показанные продукты"""
        context = self.get_or_create_context(user_id)
        return context.last_products
    
    def update_preferences(
        self,
        user_id: int,
        preferences: Dict[str, Any]
    ):
        """
        Обновить предпочтения пользователя
        
        Args:
            user_id: ID пользователя
            preferences: словарь с предпочтениями
        """
        context = self.get_or_create_context(user_id)
        context.preferences.update(preferences)
        logger.info(f"Updated preferences for user {user_id}")
    
    def get_preferences(self, user_id: int) -> Dict[str, Any]:
        """Получить предпочтения пользователя"""
        context = self.get_or_create_context(user_id)
        return context.preferences
    
    def clear_context(self, user_id: int):
        """Очистить контекст разговора"""
        if user_id in self.conversations:
            del self.conversations[user_id]
            logger.info(f"Cleared conversation context for user {user_id}")
    
    def export_conversation(self, user_id: int) -> str:
        """
        Экспортировать разговор в JSON
        
        Args:
            user_id: ID пользователя
        
        Returns:
            JSON строка с разговором
        """
        context = self.get_or_create_context(user_id)
        
        data = {
            "user_id": context.user_id,
            "current_topic": context.current_topic,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in context.messages
            ],
            "preferences": context.preferences
        }
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику сервиса"""
        return {
            "total_conversations": len(self.conversations),
            "total_messages": sum(
                len(ctx.messages) for ctx in self.conversations.values()
            ),
            "active_users": list(self.conversations.keys())
        }


# Создаем глобальный экземпляр сервиса
conversation_service = ConversationService()
