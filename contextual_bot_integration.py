"""
🧠 Интеграция контекстной системы с основным ботом Aurora
Объединяет все компоненты интеллектуального диалога
"""

from typing import Dict, List, Optional, Any, Tuple
from conversation_memory import conversation_memory, ConversationMessage
from context_analyzer import context_analyzer
from personalized_recommendations import recommendation_engine
from conversation_flow import conversation_flow_manager
import logging

logger = logging.getLogger(__name__)

class ContextualBotIntegration:
    """Интеграция контекстной системы с ботом"""
    
    def __init__(self):
        self.memory = conversation_memory
        self.analyzer = context_analyzer
        self.recommender = recommendation_engine
        self.flow_manager = conversation_flow_manager
        
        logger.info("🧠 Контекстная система инициализирована")
    
    def process_user_message(self, user_id: str, message: str, intent: Optional[str] = None) -> Dict[str, Any]:
        """Обрабатывает сообщение пользователя с полным контекстом"""
        
        try:
            # Сохраняем сообщение пользователя в память
            self.memory.add_message(
                user_id=user_id,
                message_type='user_question',
                content=message,
                intent=intent
            )
            
            # Анализируем поток диалога
            conversation_guidance = self.flow_manager.orchestrate_conversation_flow(user_id, message)
            
            # Получаем инсайты пользователя
            user_insights = self.memory.get_user_insights(user_id)
            
            # Формируем контекстно-зависимый промпт
            contextual_prompt = self.analyzer.generate_contextual_prompt(user_id, message)
            
            return {
                'contextual_prompt': contextual_prompt,
                'conversation_guidance': conversation_guidance,
                'user_insights': user_insights,
                'should_ask_clarifying_question': self._should_ask_clarifying_question(conversation_guidance),
                'personalization_level': self._calculate_personalization_level(user_id)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки контекста: {e}")
            return self._fallback_response()
    
    def enhance_bot_response(self, user_id: str, base_response: str, 
                           found_products: List[str]) -> Dict[str, Any]:
        """Улучшает ответ бота с учетом контекста"""
        
        try:
            # Генерируем персонализированные рекомендации
            personalized_recs = self.recommender.generate_personalized_recommendations(
                user_id, "", found_products
            )
            
            # Создаем персонализированный ответ
            enhanced_response = self.recommender.generate_personalized_response(
                user_id, base_response, personalized_recs
            )
            
            # Получаем рекомендации по разговору
            conversation_context = self.analyzer.analyze_conversation_context(user_id)
            
            # Формируем дополнительные предложения
            follow_up_suggestions = self._generate_follow_up_suggestions(
                user_id, conversation_context
            )
            
            # Сохраняем ответ бота в память
            self.memory.add_message(
                user_id=user_id,
                message_type='bot_response',
                content=enhanced_response,
                products_mentioned=found_products
            )
            
            return {
                'enhanced_response': enhanced_response,
                'personalized_recommendations': personalized_recs,
                'follow_up_suggestions': follow_up_suggestions,
                'conversation_momentum': conversation_context.get('conversation_momentum', 'medium'),
                'next_best_action': conversation_context.get('next_best_action', 'continue_consultation')
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка улучшения ответа: {e}")
            return {
                'enhanced_response': base_response,
                'personalized_recommendations': [],
                'follow_up_suggestions': [],
                'conversation_momentum': 'medium',
                'next_best_action': 'continue_consultation'
            }
    
    def handle_product_selection(self, user_id: str, selected_product: str) -> Dict[str, Any]:
        """Обрабатывает выбор продукта пользователем"""
        
        try:
            # Сохраняем выбор в память
            self.memory.add_message(
                user_id=user_id,
                message_type='product_selection',
                content=f"Выбран продукт: {selected_product}",
                products_mentioned=[selected_product]
            )
            
            # Анализируем что это значит для диалога
            context = self.analyzer.analyze_conversation_context(user_id)
            
            # Генерируем соответствующие действия
            next_actions = self._generate_post_selection_actions(user_id, selected_product, context)
            
            return {
                'selected_product': selected_product,
                'next_actions': next_actions,
                'should_offer_synergy': self._should_offer_synergy_products(user_id, selected_product),
                'purchase_readiness': self._assess_purchase_readiness(user_id)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки выбора продукта: {e}")
            return {'selected_product': selected_product, 'next_actions': []}
    
    def handle_link_request(self, user_id: str, requested_product: str) -> Dict[str, Any]:
        """Обрабатывает запрос ссылки на продукт"""
        
        try:
            # Сохраняем запрос ссылки
            self.memory.add_message(
                user_id=user_id,
                message_type='product_link',
                content=f"Запрос ссылки на: {requested_product}",
                products_mentioned=[requested_product]
            )
            
            # Это сильный сигнал намерения покупки
            profile = self.memory.user_profiles.get(user_id)
            if profile:
                # Увеличиваем уровень намерения покупки
                profile.purchase_intent_level = min(1.0, profile.purchase_intent_level + 0.25)
                profile.conversation_stage = 'decision'
            
            # Генерируем последующие действия
            follow_up_actions = self._generate_post_link_actions(user_id, requested_product)
            
            return {
                'requested_product': requested_product,
                'high_purchase_intent': True,
                'follow_up_actions': follow_up_actions,
                'should_suggest_complementary': True
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки запроса ссылки: {e}")
            return {'requested_product': requested_product}
    
    def get_conversation_summary(self, user_id: str) -> Dict[str, Any]:
        """Получает резюме разговора для понимания контекста"""
        
        try:
            context = self.memory.get_conversation_context(user_id)
            insights = self.analyzer.analyze_conversation_context(user_id)
            user_insights = self.memory.get_user_insights(user_id)
            
            return {
                'conversation_context': context,
                'behavioral_insights': insights,
                'user_profile_insights': user_insights,
                'recommendation_summary': self._summarize_recommendations(user_id)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения резюме: {e}")
            return {}
    
    def _should_ask_clarifying_question(self, guidance: Dict[str, Any]) -> bool:
        """Определяет, стоит ли задать уточняющий вопрос"""
        
        dialogue_state = guidance.get('dialogue_state', {})
        confidence = dialogue_state.get('confidence', 0.5)
        gaps = dialogue_state.get('information_gaps', [])
        
        return confidence < 0.6 and len(gaps) > 0
    
    def _calculate_personalization_level(self, user_id: str) -> str:
        """Вычисляет уровень персонализации для пользователя"""
        
        profile = self.memory.user_profiles.get(user_id)
        
        if not profile:
            return 'basic'
        
        if profile.total_interactions > 10:
            return 'high'
        elif profile.total_interactions > 3:
            return 'medium'
        else:
            return 'basic'
    
    def _generate_follow_up_suggestions(self, user_id: str, context: Dict[str, Any]) -> List[str]:
        """Генерирует предложения для продолжения диалога"""
        
        suggestions = []
        
        next_action = context.get('next_best_action', '')
        
        if 'facilitate_purchase' in next_action:
            suggestions.append("Хотите получить ссылку на продукт?")
            suggestions.append("Есть вопросы по способу применения?")
        
        elif 'explain_synergy' in next_action:
            suggestions.append("Расскажу о сочетании с другими продуктами")
            suggestions.append("Интересует комплексный подход?")
        
        elif 'provide_comparison' in next_action:
            suggestions.append("Сравнить с альтернативными продуктами?")
            suggestions.append("Узнать преимущества каждого варианта?")
        
        else:
            suggestions.append("Есть дополнительные вопросы?")
            suggestions.append("Нужна консультация по применению?")
        
        return suggestions
    
    def _generate_post_selection_actions(self, user_id: str, product: str, context: Dict) -> List[str]:
        """Генерирует действия после выбора продукта"""
        
        actions = []
        
        # Предлагаем детальную информацию
        actions.append(f"Подробная информация о {product}")
        
        # Проверяем синергию
        if self._should_offer_synergy_products(user_id, product):
            actions.append("Рекомендации по сочетанию с другими продуктами")
        
        # Проверяем готовность к покупке
        if self._assess_purchase_readiness(user_id) > 0.6:
            actions.append("Помощь с оформлением заказа")
        
        return actions
    
    def _should_offer_synergy_products(self, user_id: str, product: str) -> bool:
        """Определяет, стоит ли предложить синергические продукты"""
        
        product_info = self.recommender.product_database.get(product, {})
        synergy_partners = product_info.get('synergy_partners', [])
        
        profile = self.memory.user_profiles.get(user_id)
        
        # Если у продукта есть партнеры и пользователь проявляет интерес к комплексам
        if synergy_partners and profile:
            synergy_mentions = profile.preferred_categories.get('комплекс', 0)
            return synergy_mentions > 0 or len(profile.discussed_products) > 1
        
        return len(synergy_partners) > 0
    
    def _assess_purchase_readiness(self, user_id: str) -> float:
        """Оценивает готовность к покупке"""
        
        profile = self.memory.user_profiles.get(user_id)
        
        if profile:
            return profile.purchase_intent_level
        
        return 0.1
    
    def _generate_post_link_actions(self, user_id: str, product: str) -> List[str]:
        """Генерирует действия после запроса ссылки"""
        
        actions = []
        
        # Предлагаем дополнительные продукты
        if self._should_offer_synergy_products(user_id, product):
            actions.append("Рекомендовать дополнительные продукты")
        
        # Предлагаем консультацию
        actions.append("Консультация по применению")
        
        # Информация о доставке/заказе
        actions.append("Информация о заказе и доставке")
        
        return actions
    
    def _summarize_recommendations(self, user_id: str) -> Dict[str, Any]:
        """Создает резюме рекомендаций для пользователя"""
        
        profile = self.memory.user_profiles.get(user_id)
        
        if not profile:
            return {}
        
        return {
            'total_products_discussed': len(profile.discussed_products),
            'top_interests': list(profile.preferred_categories.keys())[:3],
            'conversation_stage': profile.conversation_stage,
            'purchase_readiness': profile.purchase_intent_level,
            'most_discussed_products': sorted(profile.discussed_products.items(), 
                                            key=lambda x: x[1], reverse=True)[:3]
        }
    
    def _fallback_response(self) -> Dict[str, Any]:
        """Возвращает базовый ответ при ошибках"""
        
        return {
            'contextual_prompt': '',
            'conversation_guidance': {},
            'user_insights': {},
            'should_ask_clarifying_question': False,
            'personalization_level': 'basic'
        }
    
    def cleanup_old_data(self):
        """Очищает старые данные"""
        
        try:
            self.memory.cleanup_old_conversations()
            logger.info("🧹 Очистка старых данных завершена")
        except Exception as e:
            logger.error(f"❌ Ошибка очистки данных: {e}")

# Создаем глобальный экземпляр
contextual_integration = ContextualBotIntegration()

