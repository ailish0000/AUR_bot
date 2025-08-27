"""
🧠 Система памяти диалога для Aurora Bot
Обеспечивает контекстное понимание и персонализированные рекомендации
"""

import json
import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConversationMessage:
    """Сообщение в диалоге"""
    timestamp: float
    user_id: str
    message_type: str  # 'user_question', 'bot_response', 'product_selection', 'product_link'
    content: str
    intent: Optional[str] = None
    products_mentioned: List[str] = None
    user_interests: List[str] = None
    
    def __post_init__(self):
        if self.products_mentioned is None:
            self.products_mentioned = []
        if self.user_interests is None:
            self.user_interests = []

@dataclass
class UserProfile:
    """Профиль пользователя на основе истории диалогов"""
    user_id: str
    first_interaction: float
    last_interaction: float
    total_interactions: int
    preferred_categories: Dict[str, int]  # категория -> количество упоминаний
    discussed_products: Dict[str, int]   # продукт -> количество упоминаний
    health_concerns: List[str]           # проблемы здоровья, которые обсуждались
    purchase_intent_level: float        # уровень намерения покупки (0.0-1.0)
    conversation_stage: str              # 'exploration', 'narrowing', 'decision', 'post_purchase'
    
    def __post_init__(self):
        if not self.preferred_categories:
            self.preferred_categories = {}
        if not self.discussed_products:
            self.discussed_products = {}
        if not self.health_concerns:
            self.health_concerns = []

class ConversationMemory:
    """Система памяти диалогов"""
    
    def __init__(self, memory_file: str = "conversation_memory.json"):
        self.memory_file = memory_file
        self.conversations: Dict[str, List[ConversationMessage]] = {}
        self.user_profiles: Dict[str, UserProfile] = {}
        self.max_memory_hours = 1  # Храним историю 1 час
        self.max_messages_per_user = 100  # Максимум сообщений на пользователя
        self.cleanup_interval = 600  # Очищаем каждые 10 минут
        
        self._load_memory()
        self._start_cleanup_timer()
    
    def _load_memory(self):
        """Загружает память из файла"""
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Восстанавливаем разговоры
            for user_id, messages_data in data.get('conversations', {}).items():
                self.conversations[user_id] = [
                    ConversationMessage(**msg) for msg in messages_data
                ]
            
            # Восстанавливаем профили
            for user_id, profile_data in data.get('user_profiles', {}).items():
                self.user_profiles[user_id] = UserProfile(**profile_data)
                
            logger.info(f"✅ Загружена память: {len(self.conversations)} пользователей")
            
        except FileNotFoundError:
            logger.info("📝 Создаем новую базу памяти диалогов")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки памяти: {e}")
    
    def _save_memory(self):
        """Сохраняет память в файл"""
        try:
            data = {
                'conversations': {},
                'user_profiles': {}
            }
            
            # Сохраняем разговоры
            for user_id, messages in self.conversations.items():
                data['conversations'][user_id] = [
                    asdict(msg) for msg in messages
                ]
            
            # Сохраняем профили
            for user_id, profile in self.user_profiles.items():
                data['user_profiles'][user_id] = asdict(profile)
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения памяти: {e}")
    
    def add_message(self, user_id: str, message_type: str, content: str, 
                   intent: Optional[str] = None, products_mentioned: List[str] = None,
                   user_interests: List[str] = None):
        """Добавляет сообщение в память диалога"""
        
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        message = ConversationMessage(
            timestamp=time.time(),
            user_id=user_id,
            message_type=message_type,
            content=content,
            intent=intent,
            products_mentioned=products_mentioned or [],
            user_interests=user_interests or []
        )
        
        self.conversations[user_id].append(message)
        
        # Ограничиваем количество сообщений
        if len(self.conversations[user_id]) > self.max_messages_per_user:
            self.conversations[user_id] = self.conversations[user_id][-self.max_messages_per_user:]
        
        # Обновляем профиль пользователя
        self._update_user_profile(user_id, message)
        
        # Периодически сохраняем
        if len(self.conversations[user_id]) % 5 == 0:
            self._save_memory()
    
    def _update_user_profile(self, user_id: str, message: ConversationMessage):
        """Обновляет профиль пользователя на основе нового сообщения"""
        
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id,
                first_interaction=message.timestamp,
                last_interaction=message.timestamp,
                total_interactions=1,
                preferred_categories={},
                discussed_products={},
                health_concerns=[],
                purchase_intent_level=0.1,
                conversation_stage='exploration'
            )
        
        profile = self.user_profiles[user_id]
        profile.last_interaction = message.timestamp
        profile.total_interactions += 1
        
        # Обновляем упоминания продуктов
        for product in message.products_mentioned:
            profile.discussed_products[product] = profile.discussed_products.get(product, 0) + 1
        
        # Обновляем интересы (как категории)
        for interest in message.user_interests:
            profile.preferred_categories[interest] = profile.preferred_categories.get(interest, 0) + 1
        
        # Анализируем стадию разговора
        self._analyze_conversation_stage(profile, message)
        
        # Обновляем уровень намерения покупки
        self._update_purchase_intent(profile, message)
    
    def _analyze_conversation_stage(self, profile: UserProfile, message: ConversationMessage):
        """Анализирует на какой стадии находится разговор"""
        
        recent_messages = self.get_recent_messages(profile.user_id, limit=5)
        
        # Подсчитываем типы сообщений
        question_count = sum(1 for msg in recent_messages if msg.message_type == 'user_question')
        product_selections = sum(1 for msg in recent_messages if msg.message_type == 'product_selection')
        link_requests = sum(1 for msg in recent_messages if msg.message_type == 'product_link')
        
        # Определяем стадию
        if link_requests > 0:
            profile.conversation_stage = 'decision'
        elif product_selections > 0 or len(profile.discussed_products) > 3:
            profile.conversation_stage = 'narrowing'
        elif question_count > 2:
            profile.conversation_stage = 'exploration'
        else:
            profile.conversation_stage = 'exploration'
    
    def _update_purchase_intent(self, profile: UserProfile, message: ConversationMessage):
        """Обновляет уровень намерения покупки"""
        
        intent_signals = {
            'product_link': 0.3,      # Запрос ссылки = высокий интерес
            'product_selection': 0.2,  # Выбор продукта = средний интерес
            'user_question': 0.05      # Вопрос = небольшой интерес
        }
        
        # Ключевые слова, указывающие на намерение покупки
        purchase_keywords = [
            'купить', 'заказать', 'цена', 'стоимость', 'ссылка', 
            'где купить', 'как заказать', 'доставка', 'оплата'
        ]
        
        intent_boost = intent_signals.get(message.message_type, 0)
        
        # Проверяем ключевые слова в сообщении
        if any(keyword in message.content.lower() for keyword in purchase_keywords):
            intent_boost += 0.15
        
        # Обновляем с затуханием
        current_intent = profile.purchase_intent_level
        profile.purchase_intent_level = min(1.0, current_intent * 0.9 + intent_boost)
    
    def get_conversation_context(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """Получает контекст разговора для пользователя"""
        
        recent_messages = self.get_recent_messages(user_id, limit)
        profile = self.user_profiles.get(user_id)
        
        context = {
            'recent_messages': [asdict(msg) for msg in recent_messages],
            'message_count': len(recent_messages),
            'user_profile': asdict(profile) if profile else None,
            'conversation_summary': self._generate_conversation_summary(user_id),
            'recommended_next_actions': self._get_recommended_actions(user_id)
        }
        
        return context
    
    def get_recent_messages(self, user_id: str, limit: int = 10) -> List[ConversationMessage]:
        """Получает последние сообщения пользователя"""
        
        if user_id not in self.conversations:
            return []
        
        return self.conversations[user_id][-limit:]
    
    def _generate_conversation_summary(self, user_id: str) -> Dict[str, Any]:
        """Генерирует краткое резюме разговора"""
        
        profile = self.user_profiles.get(user_id)
        recent_messages = self.get_recent_messages(user_id, limit=20)
        
        if not profile or not recent_messages:
            return {}
        
        # Самые обсуждаемые продукты
        top_products = sorted(profile.discussed_products.items(), 
                            key=lambda x: x[1], reverse=True)[:3]
        
        # Самые интересные категории
        top_categories = sorted(profile.preferred_categories.items(), 
                              key=lambda x: x[1], reverse=True)[:3]
        
        # Последние вопросы пользователя
        user_questions = [msg.content for msg in recent_messages 
                         if msg.message_type == 'user_question'][-3:]
        
        return {
            'stage': profile.conversation_stage,
            'purchase_intent': profile.purchase_intent_level,
            'top_products': [product for product, count in top_products],
            'top_categories': [category for category, count in top_categories],
            'recent_questions': user_questions,
            'interaction_count': profile.total_interactions
        }
    
    def _get_recommended_actions(self, user_id: str) -> List[str]:
        """Рекомендует следующие действия на основе контекста"""
        
        profile = self.user_profiles.get(user_id)
        if not profile:
            return ['start_conversation']
        
        actions = []
        
        # На основе стадии разговора
        if profile.conversation_stage == 'exploration':
            actions.append('ask_clarifying_questions')
            actions.append('suggest_popular_products')
        elif profile.conversation_stage == 'narrowing':
            actions.append('compare_products')
            actions.append('explain_synergies')
        elif profile.conversation_stage == 'decision':
            actions.append('provide_purchase_info')
            actions.append('suggest_complementary_products')
        
        # На основе уровня намерения покупки
        if profile.purchase_intent_level > 0.7:
            actions.append('facilitate_purchase')
        elif profile.purchase_intent_level > 0.4:
            actions.append('provide_detailed_info')
        
        return actions
    
    def cleanup_old_conversations(self):
        """Очищает старые разговоры"""
        
        cutoff_time = time.time() - (self.max_memory_hours * 3600)  # 1 час в секундах
        
        for user_id in list(self.conversations.keys()):
            # Фильтруем старые сообщения
            self.conversations[user_id] = [
                msg for msg in self.conversations[user_id] 
                if msg.timestamp > cutoff_time
            ]
            
            # Удаляем пустые разговоры
            if not self.conversations[user_id]:
                del self.conversations[user_id]
                if user_id in self.user_profiles:
                    del self.user_profiles[user_id]
        
        self._save_memory()
        logger.info(f"🧹 Очистка памяти завершена")
    
    def _start_cleanup_timer(self):
        """Запускает периодическую очистку памяти"""
        
        def cleanup_worker():
            while True:
                time.sleep(self.cleanup_interval)
                try:
                    self.cleanup_old_conversations()
                except Exception as e:
                    logger.error(f"❌ Ошибка автоочистки: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info(f"🕒 Автоочистка памяти запущена (каждые {self.cleanup_interval/60:.0f} минут)")
    
    def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Получает инсайты о пользователе для персонализации"""
        
        profile = self.user_profiles.get(user_id)
        if not profile:
            return {}
        
        recent_messages = self.get_recent_messages(user_id, limit=15)
        
        insights = {
            'is_returning_user': profile.total_interactions > 5,
            'high_purchase_intent': profile.purchase_intent_level > 0.6,
            'preferred_product_types': list(profile.preferred_categories.keys()),
            'previously_discussed': list(profile.discussed_products.keys()),
            'conversation_pattern': self._analyze_conversation_pattern(recent_messages),
            'recommended_approach': self._recommend_communication_approach(profile)
        }
        
        return insights
    
    def _analyze_conversation_pattern(self, messages: List[ConversationMessage]) -> str:
        """Анализирует паттерн общения пользователя"""
        
        if len(messages) < 3:
            return 'new_user'
        
        question_types = [msg.intent for msg in messages if msg.intent]
        
        if 'PRODUCT_SELECTION' in question_types and 'PRODUCT_LINK' in question_types:
            return 'decisive_buyer'
        elif question_types.count('GENERAL_QUESTION') > len(question_types) * 0.6:
            return 'information_seeker'
        elif 'HEALTH_ADVICE' in question_types:
            return 'health_focused'
        else:
            return 'casual_browser'
    
    def _recommend_communication_approach(self, profile: UserProfile) -> str:
        """Рекомендует подход к общению с пользователем"""
        
        if profile.purchase_intent_level > 0.7:
            return 'sales_focused'
        elif profile.conversation_stage == 'exploration':
            return 'educational'
        elif len(profile.discussed_products) > 5:
            return 'comparison_focused'
        else:
            return 'consultative'

# Создаем глобальный экземпляр
conversation_memory = ConversationMemory()
