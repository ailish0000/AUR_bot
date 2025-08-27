"""
🎯 Система персонализированных рекомендаций для Aurora Bot
Генерирует индивидуальные рекомендации на основе истории диалога и контекста
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from conversation_memory import conversation_memory, UserProfile
from context_analyzer import context_analyzer
import logging

logger = logging.getLogger(__name__)

@dataclass
class PersonalizedRecommendation:
    """Персонализированная рекомендация"""
    product_name: str
    relevance_score: float  # 0.0 - 1.0
    recommendation_type: str  # 'primary', 'complementary', 'alternative'
    reasoning: str
    confidence: float
    personalization_factors: List[str]

@dataclass
class RecommendationContext:
    """Контекст для генерации рекомендаций"""
    user_query: str
    user_profile: Optional[UserProfile]
    conversation_context: Dict[str, Any]
    health_focus: List[str]
    previous_interests: List[str]
    purchase_intent_level: float

class PersonalizedRecommendationEngine:
    """Движок персонализированных рекомендаций"""
    
    def __init__(self):
        # Карта продуктов и их характеристик
        self.product_database = {
            'Магний Плюс (Mg Plus)': {
                'categories': ['минералы', 'нервная система', 'сердце'],
                'health_benefits': ['стресс', 'сон', 'мышцы', 'нервы'],
                'target_audience': ['стресс', 'бессонница', 'спорт'],
                'synergy_partners': ['Кальций', 'Витамин D', 'Витамин B6'],
                'price_category': 'medium'
            },
            'Магний-Вечер (Mg-Evening)': {
                'categories': ['минералы', 'сон', 'релаксация'],
                'health_benefits': ['сон', 'расслабление', 'стресс'],
                'target_audience': ['бессонница', 'стресс', 'тревожность'],
                'synergy_partners': ['Магний Плюс', 'Витамин B комплекс'],
                'price_category': 'medium'
            },
            'Силицитин (Silicitin)': {
                'categories': ['гепатопротекторы', 'печень', 'детокс'],
                'health_benefits': ['печень', 'детоксикация', 'метаболизм'],
                'target_audience': ['проблемы печени', 'детокс', 'метаболизм'],
                'synergy_partners': ['Битерон-H', 'Витамин E'],
                'price_category': 'high'
            },
            'Аргент-Макс': {
                'categories': ['иммунитет', 'антибактериальный', 'серебро'],
                'health_benefits': ['иммунитет', 'антибактериальный', 'противовирусный'],
                'target_audience': ['частые болезни', 'низкий иммунитет', 'профилактика'],
                'synergy_partners': ['Витамин C', 'БАРС-2', 'Солберри'],
                'price_category': 'high'
            },
            'Витамин С': {
                'categories': ['витамины', 'иммунитет', 'антиоксиданты'],
                'health_benefits': ['иммунитет', 'антиоксидант', 'коллаген'],
                'target_audience': ['иммунитет', 'антиоксидант', 'красота'],
                'synergy_partners': ['Аргент-Макс', 'Цинк', 'Железо'],
                'price_category': 'low'
            },
            'БАРС-2 (BARS-2)': {
                'categories': ['иммунитет', 'комплекс', 'адаптогены'],
                'health_benefits': ['иммунитет', 'адаптация', 'энергия'],
                'target_audience': ['слабый иммунитет', 'усталость', 'стресс'],
                'synergy_partners': ['Аргент-Макс', 'Витамин C', 'Магний'],
                'price_category': 'medium'
            },
            'Солберри': {
                'categories': ['антиоксиданты', 'ягоды', 'иммунитет'],
                'health_benefits': ['антиоксидант', 'зрение', 'иммунитет'],
                'target_audience': ['антиоксидант', 'зрение', 'профилактика'],
                'synergy_partners': ['Витамин C', 'Витамин E', 'Аргент-Макс'],
                'price_category': 'medium'
            },
            'Битерон-H': {
                'categories': ['антиоксиданты', 'свекла', 'метаболизм'],
                'health_benefits': ['антиоксидант', 'метаболизм', 'энергия'],
                'target_audience': ['антиоксидант', 'энергия', 'метаболизм'],
                'synergy_partners': ['Силицитин', 'Витамин C', 'Солберри'],
                'price_category': 'medium'
            }
        }
        
        # Весовые коэффициенты для различных факторов персонализации
        self.personalization_weights = {
            'previous_discussion': 0.3,      # Ранее обсуждаемые продукты
            'health_focus_match': 0.4,       # Соответствие проблемам здоровья
            'synergy_bonus': 0.2,            # Синергия с ранее интересными продуктами
            'conversation_stage': 0.1        # Стадия разговора
        }
    
    def generate_personalized_recommendations(self, user_id: str, query: str, 
                                            base_recommendations: List[str]) -> List[PersonalizedRecommendation]:
        """Генерирует персонализированные рекомендации"""
        
        # Получаем контекст пользователя
        context = self._build_recommendation_context(user_id, query)
        
        # Анализируем базовые рекомендации
        personalized_recs = []
        
        for product_name in base_recommendations:
            if product_name in self.product_database:
                rec = self._create_personalized_recommendation(product_name, context)
                if rec:
                    personalized_recs.append(rec)
        
        # Добавляем дополнительные рекомендации на основе персонализации
        additional_recs = self._generate_additional_recommendations(context, personalized_recs)
        personalized_recs.extend(additional_recs)
        
        # Сортируем по релевантности
        personalized_recs.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Ограничиваем количество
        return personalized_recs[:6]
    
    def _build_recommendation_context(self, user_id: str, query: str) -> RecommendationContext:
        """Строит контекст для генерации рекомендаций"""
        
        profile = conversation_memory.user_profiles.get(user_id)
        conversation_context = context_analyzer.analyze_conversation_context(user_id)
        
        # Извлекаем фокус на здоровье из контекста
        health_focus = []
        for insight in conversation_context.get('insights', []):
            if insight['type'] == 'health_concern':
                health_focus.append(insight['details']['health_area'])
        
        # Извлекаем предыдущие интересы
        previous_interests = []
        if profile:
            previous_interests = list(profile.preferred_categories.keys())
        
        return RecommendationContext(
            user_query=query,
            user_profile=profile,
            conversation_context=conversation_context,
            health_focus=health_focus,
            previous_interests=previous_interests,
            purchase_intent_level=profile.purchase_intent_level if profile else 0.1
        )
    
    def _create_personalized_recommendation(self, product_name: str, 
                                          context: RecommendationContext) -> Optional[PersonalizedRecommendation]:
        """Создает персонализированную рекомендацию для продукта"""
        
        product_info = self.product_database.get(product_name)
        if not product_info:
            return None
        
        # Вычисляем персонализированную релевантность
        relevance_score = self._calculate_personalized_relevance(product_name, product_info, context)
        
        # Определяем тип рекомендации
        recommendation_type = self._determine_recommendation_type(product_name, context)
        
        # Генерируем персонализированное обоснование
        reasoning = self._generate_personalized_reasoning(product_name, product_info, context)
        
        # Определяем факторы персонализации
        personalization_factors = self._identify_personalization_factors(product_name, product_info, context)
        
        # Вычисляем уверенность
        confidence = self._calculate_recommendation_confidence(product_info, context)
        
        return PersonalizedRecommendation(
            product_name=product_name,
            relevance_score=relevance_score,
            recommendation_type=recommendation_type,
            reasoning=reasoning,
            confidence=confidence,
            personalization_factors=personalization_factors
        )
    
    def _calculate_personalized_relevance(self, product_name: str, product_info: Dict, 
                                        context: RecommendationContext) -> float:
        """Вычисляет персонализированную релевантность продукта"""
        
        base_score = 0.5  # Базовая релевантность
        
        # Бонус за предыдущие обсуждения
        if context.user_profile and product_name in context.user_profile.discussed_products:
            discussion_count = context.user_profile.discussed_products[product_name]
            previous_bonus = min(0.3, discussion_count * 0.1) * self.personalization_weights['previous_discussion']
            base_score += previous_bonus
        
        # Бонус за соответствие проблемам здоровья
        health_matches = len(set(product_info['health_benefits']) & set(context.health_focus))
        if health_matches > 0:
            health_bonus = min(0.4, health_matches * 0.2) * self.personalization_weights['health_focus_match']
            base_score += health_bonus
        
        # Бонус за синергию с ранее обсуждаемыми продуктами
        if context.user_profile:
            synergy_score = 0
            for discussed_product in context.user_profile.discussed_products.keys():
                if discussed_product in product_info['synergy_partners']:
                    synergy_score += 0.15
            
            synergy_bonus = min(0.2, synergy_score) * self.personalization_weights['synergy_bonus']
            base_score += synergy_bonus
        
        # Бонус за стадию разговора
        stage_bonus = 0
        if context.user_profile:
            if context.user_profile.conversation_stage == 'decision' and context.purchase_intent_level > 0.7:
                stage_bonus = 0.1
            elif context.user_profile.conversation_stage == 'narrowing':
                stage_bonus = 0.05
        
        base_score += stage_bonus * self.personalization_weights['conversation_stage']
        
        return min(1.0, base_score)
    
    def _determine_recommendation_type(self, product_name: str, context: RecommendationContext) -> str:
        """Определяет тип рекомендации"""
        
        if context.user_profile and product_name in context.user_profile.discussed_products:
            discussion_count = context.user_profile.discussed_products[product_name]
            if discussion_count >= 2:
                return 'primary'
        
        # Проверяем, является ли продукт синергическим к уже обсуждаемым
        if context.user_profile:
            product_info = self.product_database.get(product_name, {})
            for discussed_product in context.user_profile.discussed_products.keys():
                if discussed_product in product_info.get('synergy_partners', []):
                    return 'complementary'
        
        return 'alternative'
    
    def _generate_personalized_reasoning(self, product_name: str, product_info: Dict, 
                                       context: RecommendationContext) -> str:
        """Генерирует персонализированное обоснование рекомендации"""
        
        reasons = []
        
        # Обоснование на основе предыдущих обсуждений
        if context.user_profile and product_name in context.user_profile.discussed_products:
            reasons.append("вы уже проявляли интерес к этому продукту")
        
        # Обоснование на основе проблем здоровья
        health_matches = set(product_info['health_benefits']) & set(context.health_focus)
        if health_matches:
            health_areas = ', '.join(health_matches)
            reasons.append(f"подходит для ваших потребностей в области: {health_areas}")
        
        # Обоснование синергии
        if context.user_profile:
            synergy_products = []
            for discussed_product in context.user_profile.discussed_products.keys():
                if discussed_product in product_info['synergy_partners']:
                    synergy_products.append(discussed_product)
            
            if synergy_products:
                synergy_list = ', '.join(synergy_products)
                reasons.append(f"хорошо сочетается с {synergy_list}")
        
        # Обоснование на основе стадии разговора
        if context.user_profile:
            if context.user_profile.conversation_stage == 'decision':
                reasons.append("подходит для принятия решения о покупке")
            elif context.purchase_intent_level > 0.6:
                reasons.append("соответствует вашему высокому интересу к покупке")
        
        if not reasons:
            reasons.append("подходит под ваш запрос")
        
        return "Рекомендуется, так как " + " и ".join(reasons)
    
    def _identify_personalization_factors(self, product_name: str, product_info: Dict, 
                                        context: RecommendationContext) -> List[str]:
        """Идентифицирует факторы персонализации"""
        
        factors = []
        
        if context.user_profile and product_name in context.user_profile.discussed_products:
            factors.append('previous_interest')
        
        health_matches = set(product_info['health_benefits']) & set(context.health_focus)
        if health_matches:
            factors.append('health_focus_match')
        
        if context.user_profile:
            for discussed_product in context.user_profile.discussed_products.keys():
                if discussed_product in product_info['synergy_partners']:
                    factors.append('synergy_match')
                    break
        
        if context.purchase_intent_level > 0.6:
            factors.append('high_purchase_intent')
        
        return factors
    
    def _calculate_recommendation_confidence(self, product_info: Dict, 
                                           context: RecommendationContext) -> float:
        """Вычисляет уверенность в рекомендации"""
        
        confidence = 0.5  # Базовая уверенность
        
        # Увеличиваем уверенность за соответствие здоровью
        health_matches = len(set(product_info['health_benefits']) & set(context.health_focus))
        confidence += health_matches * 0.15
        
        # Увеличиваем уверенность за предыдущие обсуждения
        if context.user_profile:
            total_interactions = context.user_profile.total_interactions
            if total_interactions > 5:
                confidence += 0.1
            if total_interactions > 10:
                confidence += 0.1
        
        # Увеличиваем уверенность за высокий интерес к покупке
        if context.purchase_intent_level > 0.7:
            confidence += 0.15
        
        return min(1.0, confidence)
    
    def _generate_additional_recommendations(self, context: RecommendationContext, 
                                           existing_recs: List[PersonalizedRecommendation]) -> List[PersonalizedRecommendation]:
        """Генерирует дополнительные рекомендации на основе персонализации"""
        
        additional_recs = []
        existing_products = {rec.product_name for rec in existing_recs}
        
        # Рекомендуем синергические продукты
        for rec in existing_recs:
            if rec.relevance_score > 0.7:  # Только для высокорелевантных
                product_info = self.product_database.get(rec.product_name, {})
                for synergy_partner in product_info.get('synergy_partners', []):
                    if (synergy_partner in self.product_database and 
                        synergy_partner not in existing_products):
                        
                        synergy_rec = self._create_synergy_recommendation(
                            synergy_partner, rec.product_name, context)
                        if synergy_rec:
                            additional_recs.append(synergy_rec)
                            existing_products.add(synergy_partner)
        
        # Рекомендуем на основе предыдущих интересов
        if context.user_profile:
            for category in context.user_profile.preferred_categories.keys():
                candidate_products = self._find_products_by_category(category)
                for product in candidate_products:
                    if product not in existing_products:
                        category_rec = self._create_category_recommendation(
                            product, category, context)
                        if category_rec and category_rec.relevance_score > 0.5:
                            additional_recs.append(category_rec)
                            existing_products.add(product)
                            break  # Только один продукт на категорию
        
        return additional_recs
    
    def _create_synergy_recommendation(self, product_name: str, partner_product: str, 
                                     context: RecommendationContext) -> Optional[PersonalizedRecommendation]:
        """Создает рекомендацию на основе синергии"""
        
        product_info = self.product_database.get(product_name)
        if not product_info:
            return None
        
        return PersonalizedRecommendation(
            product_name=product_name,
            relevance_score=0.6,  # Средняя релевантность для синергических
            recommendation_type='complementary',
            reasoning=f"Отлично сочетается с {partner_product} для усиления эффекта",
            confidence=0.7,
            personalization_factors=['synergy_match']
        )
    
    def _create_category_recommendation(self, product_name: str, category: str, 
                                      context: RecommendationContext) -> Optional[PersonalizedRecommendation]:
        """Создает рекомендацию на основе категориальных предпочтений"""
        
        product_info = self.product_database.get(product_name)
        if not product_info:
            return None
        
        return PersonalizedRecommendation(
            product_name=product_name,
            relevance_score=0.5,  # Базовая релевантность для категориальных
            recommendation_type='alternative',
            reasoning=f"Соответствует вашему интересу к категории '{category}'",
            confidence=0.6,
            personalization_factors=['category_preference']
        )
    
    def _find_products_by_category(self, category: str) -> List[str]:
        """Находит продукты по категории"""
        
        matching_products = []
        for product_name, product_info in self.product_database.items():
            if category in product_info.get('categories', []):
                matching_products.append(product_name)
        
        return matching_products
    
    def generate_personalized_response(self, user_id: str, base_response: str, 
                                     recommendations: List[PersonalizedRecommendation]) -> str:
        """Генерирует персонализированный ответ с рекомендациями"""
        
        if not recommendations:
            return base_response
        
        context = conversation_memory.get_conversation_context(user_id)
        profile = context.get('user_profile')
        
        # Формируем персонализированное введение
        intro_parts = []
        
        if profile:
            stage = profile.get('conversation_stage', 'exploration')
            total_interactions = profile.get('total_interactions', 0)
            
            if total_interactions > 1:
                intro_parts.append("Учитывая нашу беседу")
            
            if stage == 'decision':
                intro_parts.append("и ваш интерес к покупке")
            elif stage == 'narrowing':
                intro_parts.append("и ваш процесс выбора")
        
        # Формируем персонализированный ответ
        response_parts = [base_response]
        
        if intro_parts:
            intro = ", ".join(intro_parts)
            response_parts.append(f"\n{intro.capitalize()}, рекомендую:")
        else:
            response_parts.append("\nПерсонально для вас рекомендую:")
        
        # Добавляем топ-3 рекомендации с обоснованиями
        top_recommendations = recommendations[:3]
        
        for i, rec in enumerate(top_recommendations, 1):
            response_parts.append(f"\n{i}. {rec.product_name}")
            response_parts.append(f"   {rec.reasoning}")
            
            if rec.recommendation_type == 'complementary':
                response_parts.append("   💫 Дополнительный продукт для усиления эффекта")
            elif rec.recommendation_type == 'primary':
                response_parts.append("   ⭐ Основная рекомендация на основе ваших интересов")
        
        # Добавляем призыв к действию на основе уровня намерения покупки
        if profile and profile.get('purchase_intent_level', 0) > 0.6:
            response_parts.append("\n💡 Готовы узнать больше или получить ссылку на продукт?")
        else:
            response_parts.append("\n❓ Есть вопросы по этим продуктам?")
        
        return "".join(response_parts)

# Создаем глобальный экземпляр
recommendation_engine = PersonalizedRecommendationEngine()

