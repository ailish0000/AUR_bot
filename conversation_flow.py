"""
🔄 Система управления потоком диалога для Aurora Bot
Управляет логикой ведения беседы, задает уточняющие вопросы, направляет к цели
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from conversation_memory import conversation_memory, ConversationMessage
from context_analyzer import context_analyzer
from personalized_recommendations import recommendation_engine
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConversationAction:
    """Действие в рамках диалога"""
    action_type: str  # 'ask_question', 'provide_recommendation', 'clarify_need', 'summarize'
    content: str
    priority: int  # 1-5, где 1 - наивысший приоритет
    reasoning: str
    expected_outcome: str

@dataclass
class DialogueState:
    """Состояние диалога"""
    current_goal: str  # 'product_discovery', 'comparison', 'purchase_decision', 'information_gathering'
    information_gaps: List[str]  # Что нужно уточнить
    confidence_level: float  # Уверенность в понимании потребностей
    next_logical_step: str
    conversation_momentum: str  # 'building', 'maintained', 'declining'

class ConversationFlowManager:
    """Менеджер потока диалога"""
    
    def __init__(self):
        # Паттерны для определения целей разговора
        self.goal_patterns = {
            'product_discovery': [
                'что лучше', 'посоветуй', 'рекомендуй', 'подходит', 'нужно что-то'
            ],
            'comparison': [
                'сравни', 'разница', 'отличается', 'лучше из', 'какой выбрать'
            ],
            'purchase_decision': [
                'купить', 'заказать', 'ссылка', 'цена', 'где купить', 'как заказать'
            ],
            'information_gathering': [
                'как принимать', 'состав', 'противопоказания', 'эффект', 'действие'
            ]
        }
        
        # Шаблоны уточняющих вопросов для разных ситуаций
        self.clarification_templates = {
            'health_focus': [
                "Не могли бы вы уточнить, какая область здоровья вас больше всего беспокоит?",
                "Есть ли у вас конкретные проблемы или цели в отношении здоровья?",
                "Что именно вы хотели бы улучшить или поддержать в своем организме?"
            ],
            'usage_context': [
                "Планируете ли вы принимать это для профилактики или есть конкретная проблема?",
                "Это для вас лично или для кого-то из близких?",
                "Есть ли у вас опыт приема подобных продуктов?"
            ],
            'product_preference': [
                "Предпочитаете ли вы натуральные компоненты или синтетические добавки?",
                "Важна ли для вас форма выпуска (капсулы, таблетки, порошок)?",
                "Есть ли ограничения по бюджету?"
            ],
            'synergy_interest': [
                "Принимаете ли вы уже какие-то добавки или лекарства?",
                "Интересует ли вас комплексный подход или отдельные продукты?",
                "Хотели бы узнать о сочетании нескольких продуктов?"
            ]
        }
    
    def analyze_conversation_flow(self, user_id: str, new_message: str) -> DialogueState:
        """Анализирует текущее состояние потока диалога"""
        
        # Получаем контекст разговора
        context = context_analyzer.analyze_conversation_context(user_id)
        recent_messages = conversation_memory.get_recent_messages(user_id, limit=5)
        
        # Определяем текущую цель
        current_goal = self._identify_conversation_goal(new_message, recent_messages)
        
        # Выявляем информационные пробелы
        information_gaps = self._identify_information_gaps(user_id, current_goal, context)
        
        # Оцениваем уверенность в понимании потребностей
        confidence_level = self._calculate_understanding_confidence(context, information_gaps)
        
        # Определяем следующий логический шаг
        next_step = self._determine_next_step(current_goal, information_gaps, confidence_level)
        
        # Оцениваем моментум разговора
        momentum = self._assess_conversation_momentum(recent_messages)
        
        return DialogueState(
            current_goal=current_goal,
            information_gaps=information_gaps,
            confidence_level=confidence_level,
            next_logical_step=next_step,
            conversation_momentum=momentum
        )
    
    def generate_conversation_actions(self, user_id: str, dialogue_state: DialogueState) -> List[ConversationAction]:
        """Генерирует возможные действия для продолжения диалога"""
        
        actions = []
        
        # Действия на основе информационных пробелов
        if dialogue_state.information_gaps and dialogue_state.confidence_level < 0.7:
            actions.extend(self._generate_clarification_actions(dialogue_state.information_gaps))
        
        # Действия на основе цели разговора
        if dialogue_state.current_goal == 'product_discovery':
            actions.extend(self._generate_discovery_actions(user_id, dialogue_state))
        elif dialogue_state.current_goal == 'comparison':
            actions.extend(self._generate_comparison_actions(user_id, dialogue_state))
        elif dialogue_state.current_goal == 'purchase_decision':
            actions.extend(self._generate_purchase_actions(user_id, dialogue_state))
        elif dialogue_state.current_goal == 'information_gathering':
            actions.extend(self._generate_information_actions(user_id, dialogue_state))
        
        # Действия для поддержания моментума
        if dialogue_state.conversation_momentum == 'declining':
            actions.extend(self._generate_engagement_actions(user_id))
        
        # Сортируем по приоритету
        actions.sort(key=lambda x: x.priority)
        
        return actions[:3]  # Возвращаем топ-3 действия
    
    def _identify_conversation_goal(self, message: str, recent_messages: List[ConversationMessage]) -> str:
        """Определяет основную цель разговора"""
        
        message_lower = message.lower()
        
        # Проверяем паттерны в текущем сообщении
        for goal, patterns in self.goal_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return goal
        
        # Анализируем контекст последних сообщений
        if recent_messages:
            recent_text = ' '.join([msg.content.lower() for msg in recent_messages[-3:] 
                                  if msg.message_type == 'user_question'])
            
            for goal, patterns in self.goal_patterns.items():
                pattern_matches = sum(1 for pattern in patterns if pattern in recent_text)
                if pattern_matches >= 2:
                    return goal
        
        return 'product_discovery'  # По умолчанию
    
    def _identify_information_gaps(self, user_id: str, goal: str, context: Dict) -> List[str]:
        """Выявляет информационные пробелы для достижения цели"""
        
        gaps = []
        profile = conversation_memory.user_profiles.get(user_id)
        
        # Основные информационные потребности по целям
        goal_requirements = {
            'product_discovery': ['health_focus', 'usage_context', 'product_preference'],
            'comparison': ['comparison_criteria', 'specific_products', 'decision_factors'],
            'purchase_decision': ['product_choice', 'purchase_readiness', 'additional_info'],
            'information_gathering': ['specific_questions', 'detail_level', 'application_context']
        }
        
        required_info = goal_requirements.get(goal, [])
        
        # Проверяем, какой информации не хватает
        for info_type in required_info:
            if not self._has_sufficient_info(info_type, profile, context):
                gaps.append(info_type)
        
        # Дополнительные проверки на основе контекста
        insights = context.get('insights', [])
        
        # Если нет ясности по здоровью, но есть намеки
        health_insights = [i for i in insights if i['type'] == 'health_concern']
        if not health_insights and goal in ['product_discovery', 'comparison']:
            gaps.append('health_focus')
        
        # Если высокий интерес к покупке, но нет ясности по продукту
        purchase_insights = [i for i in insights if i['type'] == 'purchase_readiness']
        if purchase_insights and not profile:
            gaps.append('product_choice')
        
        return gaps
    
    def _has_sufficient_info(self, info_type: str, profile: Optional[Any], context: Dict) -> bool:
        """Проверяет, достаточно ли информации определенного типа"""
        
        if info_type == 'health_focus':
            insights = context.get('insights', [])
            health_insights = [i for i in insights if i['type'] == 'health_concern']
            return len(health_insights) > 0
        
        elif info_type == 'usage_context':
            return profile and len(profile.preferred_categories) > 0
        
        elif info_type == 'product_preference':
            return profile and len(profile.discussed_products) > 1
        
        elif info_type == 'comparison_criteria':
            insights = context.get('insights', [])
            comparison_insights = [i for i in insights if i['type'] == 'comparison_intent']
            return len(comparison_insights) > 0
        
        elif info_type == 'product_choice':
            return profile and len(profile.discussed_products) > 0
        
        return False
    
    def _calculate_understanding_confidence(self, context: Dict, gaps: List[str]) -> float:
        """Вычисляет уверенность в понимании потребностей пользователя"""
        
        base_confidence = 0.3
        
        # Бонус за инсайты
        insights = context.get('insights', [])
        confidence_by_insight = {
            'health_concern': 0.2,
            'product_focus': 0.15,
            'synergy_interest': 0.1,
            'purchase_readiness': 0.2
        }
        
        for insight in insights:
            insight_type = insight.get('type')
            if insight_type in confidence_by_insight:
                base_confidence += confidence_by_insight[insight_type] * insight.get('confidence', 0.5)
        
        # Штраф за информационные пробелы
        gap_penalty = len(gaps) * 0.1
        base_confidence -= gap_penalty
        
        # Бонус за длительность разговора
        momentum = context.get('conversation_momentum', 'starting')
        if momentum == 'high':
            base_confidence += 0.1
        elif momentum == 'medium':
            base_confidence += 0.05
        
        return max(0.0, min(1.0, base_confidence))
    
    def _determine_next_step(self, goal: str, gaps: List[str], confidence: float) -> str:
        """Определяет следующий логический шаг в диалоге"""
        
        # Если низкая уверенность, нужно собрать больше информации
        if confidence < 0.5 and gaps:
            return 'gather_information'
        
        # Действия на основе цели
        if goal == 'product_discovery':
            if confidence > 0.7:
                return 'provide_recommendations'
            else:
                return 'clarify_needs'
        
        elif goal == 'comparison':
            if 'comparison_criteria' in gaps:
                return 'clarify_comparison_criteria'
            else:
                return 'provide_comparison'
        
        elif goal == 'purchase_decision':
            if 'product_choice' in gaps:
                return 'help_choose_product'
            else:
                return 'facilitate_purchase'
        
        elif goal == 'information_gathering':
            return 'provide_detailed_information'
        
        return 'continue_conversation'
    
    def _assess_conversation_momentum(self, recent_messages: List[ConversationMessage]) -> str:
        """Оценивает моментум разговора"""
        
        if len(recent_messages) < 2:
            return 'building'
        
        # Анализируем частоту сообщений
        user_messages = [msg for msg in recent_messages if msg.message_type == 'user_question']
        
        if len(user_messages) >= 3:
            return 'high'
        elif len(user_messages) >= 1:
            return 'maintained'
        else:
            return 'declining'
    
    def _generate_clarification_actions(self, gaps: List[str]) -> List[ConversationAction]:
        """Генерирует действия для уточнения информации"""
        
        actions = []
        
        for gap in gaps:
            if gap in self.clarification_templates:
                templates = self.clarification_templates[gap]
                
                action = ConversationAction(
                    action_type='ask_question',
                    content=templates[0],  # Берем первый шаблон
                    priority=1,  # Высокий приоритет для уточнений
                    reasoning=f"Необходимо уточнить {gap} для лучшего понимания потребностей",
                    expected_outcome=f"Получить информацию о {gap}"
                )
                actions.append(action)
        
        return actions
    
    def _generate_discovery_actions(self, user_id: str, state: DialogueState) -> List[ConversationAction]:
        """Генерирует действия для поиска продуктов"""
        
        actions = []
        
        if state.confidence_level > 0.6:
            action = ConversationAction(
                action_type='provide_recommendation',
                content="На основе ваших потребностей рекомендую следующие продукты:",
                priority=2,
                reasoning="Достаточно информации для рекомендаций",
                expected_outcome="Предоставить персонализированные рекомендации"
            )
            actions.append(action)
        else:
            action = ConversationAction(
                action_type='clarify_need',
                content="Чтобы подобрать наиболее подходящие продукты, расскажите подробнее о ваших потребностях",
                priority=1,
                reasoning="Недостаточно информации для точных рекомендаций",
                expected_outcome="Получить более детальную информацию"
            )
            actions.append(action)
        
        return actions
    
    def _generate_comparison_actions(self, user_id: str, state: DialogueState) -> List[ConversationAction]:
        """Генерирует действия для сравнения продуктов"""
        
        actions = []
        
        action = ConversationAction(
            action_type='provide_recommendation',
            content="Давайте сравним интересующие вас продукты:",
            priority=2,
            reasoning="Пользователь хочет сравнить продукты",
            expected_outcome="Предоставить сравнительную информацию"
        )
        actions.append(action)
        
        return actions
    
    def _generate_purchase_actions(self, user_id: str, state: DialogueState) -> List[ConversationAction]:
        """Генерирует действия для помощи с покупкой"""
        
        actions = []
        
        action = ConversationAction(
            action_type='provide_recommendation',
            content="Помогу вам с выбором и покупкой:",
            priority=1,  # Высокий приоритет для покупки
            reasoning="Пользователь готов к покупке",
            expected_outcome="Содействовать процессу покупки"
        )
        actions.append(action)
        
        return actions
    
    def _generate_information_actions(self, user_id: str, state: DialogueState) -> List[ConversationAction]:
        """Генерирует действия для предоставления информации"""
        
        actions = []
        
        action = ConversationAction(
            action_type='provide_recommendation',
            content="Предоставлю детальную информацию:",
            priority=3,
            reasoning="Пользователь запрашивает информацию",
            expected_outcome="Предоставить подробную информацию"
        )
        actions.append(action)
        
        return actions
    
    def _generate_engagement_actions(self, user_id: str) -> List[ConversationAction]:
        """Генерирует действия для повышения вовлеченности"""
        
        actions = []
        
        engagement_questions = [
            "Есть ли у вас дополнительные вопросы о продуктах Aurora?",
            "Может быть, вас интересует что-то конкретное?",
            "Хотели бы узнать о новинках или популярных продуктах?"
        ]
        
        action = ConversationAction(
            action_type='ask_question',
            content=engagement_questions[0],
            priority=4,
            reasoning="Поддержание активности диалога",
            expected_outcome="Возобновить активное участие пользователя"
        )
        actions.append(action)
        
        return actions
    
    def orchestrate_conversation_flow(self, user_id: str, user_message: str) -> Dict[str, Any]:
        """Оркестрирует поток диалога и возвращает рекомендации для ответа"""
        
        # Анализируем текущее состояние диалога
        dialogue_state = self.analyze_conversation_flow(user_id, user_message)
        
        # Генерируем возможные действия
        actions = self.generate_conversation_actions(user_id, dialogue_state)
        
        # Выбираем лучшее действие
        best_action = actions[0] if actions else None
        
        # Формируем контекстно-зависимый ответ
        conversation_guidance = {
            'dialogue_state': {
                'goal': dialogue_state.current_goal,
                'confidence': dialogue_state.confidence_level,
                'next_step': dialogue_state.next_logical_step,
                'momentum': dialogue_state.conversation_momentum,
                'information_gaps': dialogue_state.information_gaps
            },
            'recommended_action': {
                'type': best_action.action_type if best_action else 'continue_conversation',
                'content': best_action.content if best_action else '',
                'priority': best_action.priority if best_action else 5,
                'reasoning': best_action.reasoning if best_action else ''
            },
            'conversation_suggestions': [action.content for action in actions],
            'personalization_prompt': context_analyzer.generate_contextual_prompt(user_id, user_message)
        }
        
        return conversation_guidance

# Создаем глобальный экземпляр
conversation_flow_manager = ConversationFlowManager()

