"""
🔍 Анализатор контекста диалога для Aurora Bot
Понимает связи между вопросами и выявляет скрытые намерения пользователя
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from conversation_memory import ConversationMessage, UserProfile, conversation_memory
import logging

logger = logging.getLogger(__name__)

@dataclass
class ContextInsight:
    """Инсайт о контексте диалога"""
    insight_type: str  # 'product_focus', 'health_concern', 'synergy_interest', 'comparison_intent'
    confidence: float  # 0.0 - 1.0
    details: Dict[str, Any]
    suggested_action: str

class ContextAnalyzer:
    """Анализатор контекста диалога"""
    
    def __init__(self):
        # Паттерны для выявления различных типов намерений
        self.health_patterns = {
            'печень': ['гепатопротектор', 'детокс', 'очищение', 'токсины'],
            'иммунитет': ['простуда', 'вирус', 'защита', 'антибактериальный'],
            'сердце': ['давление', 'сосуды', 'кардио', 'холестерин'],
            'кости': ['остеопороз', 'суставы', 'кальций', 'витамин д'],
            'нервы': ['стресс', 'сон', 'магний', 'расслабление'],
            'пищеварение': ['желудок', 'кишечник', 'микрофлора', 'переваривание']
        }
        
        self.synergy_patterns = [
            ['магний', 'кальций'],
            ['витамин с', 'цинк'],
            ['омега-3', 'витамин е'],
            ['витамин д', 'кальций'],
            ['железо', 'витамин с'],
            ['пробиотики', 'пребиотики']
        ]
        
        self.comparison_keywords = [
            'лучше', 'отличается', 'разница', 'сравнить', 'выбрать между',
            'что лучше', 'какой из', 'преимущества', 'эффективнее'
        ]
        
        self.purchase_intent_keywords = [
            'купить', 'заказать', 'цена', 'стоимость', 'ссылка', 'где купить',
            'как заказать', 'доставка', 'оплата', 'в наличии', 'скидка'
        ]
        
        self.urgency_keywords = [
            'срочно', 'быстро', 'немедленно', 'сегодня', 'сейчас', 'скорее'
        ]
    
    def analyze_conversation_context(self, user_id: str) -> Dict[str, Any]:
        """Анализирует полный контекст разговора пользователя"""
        
        context = conversation_memory.get_conversation_context(user_id, limit=15)
        profile = context.get('user_profile')
        recent_messages = context.get('recent_messages', [])
        
        if not recent_messages:
            return self._default_context()
        
        insights = []
        
        # Анализируем различные аспекты
        insights.extend(self._analyze_health_focus(recent_messages))
        insights.extend(self._analyze_product_focus(recent_messages, profile))
        insights.extend(self._analyze_synergy_interest(recent_messages))
        insights.extend(self._analyze_comparison_intent(recent_messages))
        insights.extend(self._analyze_purchase_readiness(recent_messages, profile))
        insights.extend(self._analyze_conversation_flow(recent_messages))
        
        # Генерируем итоговые рекомендации
        recommendations = self._generate_context_recommendations(insights, profile)
        
        return {
            'insights': [self._insight_to_dict(insight) for insight in insights],
            'primary_focus': self._identify_primary_focus(insights),
            'conversation_momentum': self._assess_momentum(recent_messages),
            'recommendations': recommendations,
            'next_best_action': self._determine_next_action(insights, profile)
        }
    
    def _analyze_health_focus(self, messages: List[Dict]) -> List[ContextInsight]:
        """Анализирует фокус на здоровье в разговоре"""
        
        insights = []
        combined_text = ' '.join([msg['content'].lower() for msg in messages 
                                if msg['message_type'] == 'user_question'])
        
        for health_area, keywords in self.health_patterns.items():
            matches = sum(1 for keyword in keywords if keyword in combined_text)
            if matches > 0:
                confidence = min(1.0, matches * 0.3 + 0.2)
                
                insight = ContextInsight(
                    insight_type='health_concern',
                    confidence=confidence,
                    details={
                        'health_area': health_area,
                        'matched_keywords': [kw for kw in keywords if kw in combined_text],
                        'mention_count': matches
                    },
                    suggested_action=f'focus_on_{health_area}_products'
                )
                insights.append(insight)
        
        return insights
    
    def _analyze_product_focus(self, messages: List[Dict], profile: Optional[Dict]) -> List[ContextInsight]:
        """Анализирует фокус на конкретных продуктах"""
        
        insights = []
        
        if not profile:
            return insights
        
        discussed_products = profile.get('discussed_products', {})
        
        # Ищем продукты, которые упоминались многократно
        for product, count in discussed_products.items():
            if count >= 2:
                confidence = min(1.0, count * 0.25)
                
                insight = ContextInsight(
                    insight_type='product_focus',
                    confidence=confidence,
                    details={
                        'product_name': product,
                        'mention_count': count,
                        'focus_level': 'high' if count >= 3 else 'medium'
                    },
                    suggested_action='provide_detailed_product_info'
                )
                insights.append(insight)
        
        return insights
    
    def _analyze_synergy_interest(self, messages: List[Dict]) -> List[ContextInsight]:
        """Анализирует интерес к синергии продуктов"""
        
        insights = []
        combined_text = ' '.join([msg['content'].lower() for msg in messages 
                                if msg['message_type'] == 'user_question'])
        
        # Проверяем паттерны синергии
        for synergy_pair in self.synergy_patterns:
            if all(component in combined_text for component in synergy_pair):
                confidence = 0.8
                
                insight = ContextInsight(
                    insight_type='synergy_interest',
                    confidence=confidence,
                    details={
                        'synergy_components': synergy_pair,
                        'combination_type': 'complementary'
                    },
                    suggested_action='explain_product_synergy'
                )
                insights.append(insight)
        
        # Проверяем ключевые слова синергии
        synergy_keywords = ['вместе', 'сочетание', 'комплекс', 'совместно', 'одновременно']
        synergy_mentions = sum(1 for keyword in synergy_keywords if keyword in combined_text)
        
        if synergy_mentions > 0:
            confidence = min(1.0, synergy_mentions * 0.4)
            
            insight = ContextInsight(
                insight_type='synergy_interest',
                confidence=confidence,
                details={
                    'synergy_keywords_found': synergy_mentions,
                    'interest_type': 'general_combination'
                },
                suggested_action='suggest_product_combinations'
            )
            insights.append(insight)
        
        return insights
    
    def _analyze_comparison_intent(self, messages: List[Dict]) -> List[ContextInsight]:
        """Анализирует намерение сравнить продукты"""
        
        insights = []
        combined_text = ' '.join([msg['content'].lower() for msg in messages 
                                if msg['message_type'] == 'user_question'])
        
        comparison_mentions = sum(1 for keyword in self.comparison_keywords 
                                if keyword in combined_text)
        
        if comparison_mentions > 0:
            confidence = min(1.0, comparison_mentions * 0.5)
            
            insight = ContextInsight(
                insight_type='comparison_intent',
                confidence=confidence,
                details={
                    'comparison_signals': comparison_mentions,
                    'comparison_type': 'product_evaluation'
                },
                suggested_action='provide_product_comparison'
            )
            insights.append(insight)
        
        return insights
    
    def _analyze_purchase_readiness(self, messages: List[Dict], profile: Optional[Dict]) -> List[ContextInsight]:
        """Анализирует готовность к покупке"""
        
        insights = []
        combined_text = ' '.join([msg['content'].lower() for msg in messages])
        
        # Проверяем ключевые слова покупки
        purchase_mentions = sum(1 for keyword in self.purchase_intent_keywords 
                              if keyword in combined_text)
        
        # Проверяем срочность
        urgency_mentions = sum(1 for keyword in self.urgency_keywords 
                             if keyword in combined_text)
        
        # Проверяем запросы ссылок
        link_requests = sum(1 for msg in messages 
                          if msg['message_type'] == 'product_link')
        
        # Вычисляем общую готовность
        purchase_signals = purchase_mentions + link_requests * 2 + urgency_mentions
        
        if purchase_signals > 0:
            confidence = min(1.0, purchase_signals * 0.3)
            readiness_level = 'high' if purchase_signals >= 3 else 'medium'
            
            insight = ContextInsight(
                insight_type='purchase_readiness',
                confidence=confidence,
                details={
                    'purchase_signals': purchase_signals,
                    'link_requests': link_requests,
                    'urgency_level': urgency_mentions,
                    'readiness_level': readiness_level
                },
                suggested_action='facilitate_purchase_process'
            )
            insights.append(insight)
        
        return insights
    
    def _analyze_conversation_flow(self, messages: List[Dict]) -> List[ContextInsight]:
        """Анализирует поток разговора"""
        
        insights = []
        
        if len(messages) < 3:
            return insights
        
        # Анализируем последние 5 сообщений для определения тренда
        recent_msgs = messages[-5:]
        user_questions = [msg for msg in recent_msgs if msg['message_type'] == 'user_question']
        
        if len(user_questions) >= 3:
            # Проверяем, углубляется ли разговор или расширяется
            question_lengths = [len(msg['content'].split()) for msg in user_questions]
            
            if len(question_lengths) >= 2:
                trend = 'deepening' if question_lengths[-1] > question_lengths[0] else 'broadening'
                
                insight = ContextInsight(
                    insight_type='conversation_flow',
                    confidence=0.6,
                    details={
                        'flow_trend': trend,
                        'question_complexity': 'increasing' if question_lengths[-1] > 10 else 'standard',
                        'engagement_level': len(user_questions)
                    },
                    suggested_action='adapt_detail_level'
                )
                insights.append(insight)
        
        return insights
    
    def _generate_context_recommendations(self, insights: List[ContextInsight], 
                                        profile: Optional[Dict]) -> List[str]:
        """Генерирует рекомендации на основе анализа контекста"""
        
        recommendations = []
        
        # Группируем инсайты по типам
        insight_groups = {}
        for insight in insights:
            if insight.insight_type not in insight_groups:
                insight_groups[insight.insight_type] = []
            insight_groups[insight.insight_type].append(insight)
        
        # Генерируем рекомендации на основе инсайтов
        if 'health_concern' in insight_groups:
            health_insights = insight_groups['health_concern']
            top_health = max(health_insights, key=lambda x: x.confidence)
            recommendations.append(f"Фокус на продуктах для {top_health.details['health_area']}")
        
        if 'synergy_interest' in insight_groups:
            recommendations.append("Предложить комбинации продуктов")
        
        if 'comparison_intent' in insight_groups:
            recommendations.append("Предоставить сравнительную таблицу")
        
        if 'purchase_readiness' in insight_groups:
            purchase_insight = insight_groups['purchase_readiness'][0]
            if purchase_insight.details['readiness_level'] == 'high':
                recommendations.append("Содействовать процессу покупки")
            else:
                recommendations.append("Предоставить дополнительную информацию")
        
        return recommendations
    
    def _identify_primary_focus(self, insights: List[ContextInsight]) -> Optional[str]:
        """Определяет основной фокус разговора"""
        
        if not insights:
            return None
        
        # Находим инсайт с наивысшей уверенностью
        primary_insight = max(insights, key=lambda x: x.confidence)
        
        if primary_insight.confidence > 0.5:
            return primary_insight.insight_type
        
        return None
    
    def _assess_momentum(self, messages: List[Dict]) -> str:
        """Оценивает моментум разговора"""
        
        if len(messages) < 2:
            return 'starting'
        
        recent_user_msgs = [msg for msg in messages[-5:] 
                           if msg['message_type'] == 'user_question']
        
        if len(recent_user_msgs) >= 3:
            return 'high'
        elif len(recent_user_msgs) >= 1:
            return 'medium'
        else:
            return 'low'
    
    def _determine_next_action(self, insights: List[ContextInsight], 
                             profile: Optional[Dict]) -> str:
        """Определяет следующее наилучшее действие"""
        
        if not insights:
            return 'engage_conversation'
        
        # Приоритизируем действия
        action_priorities = {
            'facilitate_purchase_process': 1,
            'provide_product_comparison': 2,
            'explain_product_synergy': 3,
            'focus_on_health_products': 4,
            'provide_detailed_product_info': 5
        }
        
        # Собираем все рекомендуемые действия
        suggested_actions = [insight.suggested_action for insight in insights]
        
        # Выбираем действие с наивысшим приоритетом
        for action in sorted(action_priorities.keys(), key=lambda x: action_priorities[x]):
            if any(action in sa for sa in suggested_actions):
                return action
        
        return 'continue_consultation'
    
    def _default_context(self) -> Dict[str, Any]:
        """Возвращает контекст по умолчанию для новых пользователей"""
        
        return {
            'insights': [],
            'primary_focus': None,
            'conversation_momentum': 'starting',
            'recommendations': ['start_with_general_questions'],
            'next_best_action': 'engage_conversation'
        }
    
    def _insight_to_dict(self, insight: ContextInsight) -> Dict[str, Any]:
        """Преобразует инсайт в словарь"""
        
        return {
            'type': insight.insight_type,
            'confidence': insight.confidence,
            'details': insight.details,
            'suggested_action': insight.suggested_action
        }
    
    def generate_contextual_prompt(self, user_id: str, current_query: str) -> str:
        """Генерирует контекстно-зависимый промпт для LLM"""
        
        context_analysis = self.analyze_conversation_context(user_id)
        profile = conversation_memory.user_profiles.get(user_id)
        
        prompt_parts = []
        
        # Базовая информация о пользователе
        if profile:
            prompt_parts.append(f"КОНТЕКСТ ПОЛЬЗОВАТЕЛЯ:")
            prompt_parts.append(f"- Стадия разговора: {profile.conversation_stage}")
            prompt_parts.append(f"- Уровень намерения покупки: {profile.purchase_intent_level:.1f}/1.0")
            prompt_parts.append(f"- Количество взаимодействий: {profile.total_interactions}")
        
        # Основной фокус разговора
        primary_focus = context_analysis.get('primary_focus')
        if primary_focus:
            prompt_parts.append(f"- Основной фокус: {primary_focus}")
        
        # Ранее обсуждаемые продукты
        if profile and profile.discussed_products:
            top_products = sorted(profile.discussed_products.items(), 
                                key=lambda x: x[1], reverse=True)[:3]
            products_list = [product for product, count in top_products]
            prompt_parts.append(f"- Обсуждаемые продукты: {', '.join(products_list)}")
        
        # Рекомендации по подходу
        recommendations = context_analysis.get('recommendations', [])
        if recommendations:
            prompt_parts.append(f"- Рекомендуемый подход: {', '.join(recommendations)}")
        
        # Следующее действие
        next_action = context_analysis.get('next_best_action')
        if next_action:
            prompt_parts.append(f"- Следующее действие: {next_action}")
        
        if prompt_parts:
            context_prompt = '\n'.join(prompt_parts)
            return f"{context_prompt}\n\nУчитывая этот контекст, ответь на вопрос: {current_query}"
        
        return current_query

# Создаем глобальный экземпляр
context_analyzer = ContextAnalyzer()

