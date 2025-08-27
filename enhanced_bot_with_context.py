"""
🚀 Улучшенный Aurora Bot с контекстной системой
Демонстрация интеграции всех компонентов интеллектуального диалога
"""

import asyncio
from typing import Dict, List, Optional, Any
from contextual_bot_integration import contextual_integration
from enhanced_llm import EnhancedLLM
from nlp_processor import NLPProcessor, Intent
import logging

logger = logging.getLogger(__name__)

class EnhancedAuroraBot:
    """Улучшенный Aurora Bot с контекстной системой"""
    
    def __init__(self):
        self.llm = EnhancedLLM()
        self.nlp = NLPProcessor()
        self.context_system = contextual_integration
        
        logger.info("🚀 Улучшенный Aurora Bot с контекстом инициализирован")
    
    async def handle_user_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """Обрабатывает сообщение пользователя с полным контекстом"""
        
        try:
            # Анализируем намерение пользователя
            intent = self.nlp.analyze_intent(message)
            
            # Обрабатываем сообщение через контекстную систему
            context_result = self.context_system.process_user_message(user_id, message, intent.name)
            
            # Получаем контекстный промпт
            contextual_prompt = context_result.get('contextual_prompt', message)
            
            # Проверяем, нужно ли задать уточняющий вопрос
            if context_result.get('should_ask_clarifying_question', False):
                clarifying_response = await self._generate_clarifying_question(user_id, context_result)
                return {
                    'response': clarifying_response,
                    'type': 'clarification',
                    'context_info': context_result
                }
            
            # Генерируем ответ с учетом контекста
            base_response = await self.llm.process_query(contextual_prompt, intent)
            
            # Извлекаем упомянутые продукты
            found_products = self.llm._extract_products_from_response(base_response)
            
            # Улучшаем ответ через контекстную систему
            enhancement_result = self.context_system.enhance_bot_response(
                user_id, base_response, found_products
            )
            
            # Формируем финальный ответ
            final_response = self._format_contextual_response(
                enhancement_result, context_result
            )
            
            return {
                'response': final_response,
                'type': 'contextual_recommendation',
                'products': found_products,
                'personalized_recommendations': enhancement_result.get('personalized_recommendations', []),
                'follow_up_suggestions': enhancement_result.get('follow_up_suggestions', []),
                'conversation_momentum': enhancement_result.get('conversation_momentum', 'medium'),
                'context_info': context_result
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения: {e}")
            return await self._fallback_response(message)
    
    async def handle_product_selection(self, user_id: str, selection: str) -> Dict[str, Any]:
        """Обрабатывает выбор продукта пользователем"""
        
        try:
            # Обрабатываем через контекстную систему
            selection_result = self.context_system.handle_product_selection(user_id, selection)
            
            # Генерируем ответ о выбранном продукте
            product_info_response = await self._generate_product_info_response(
                selection, selection_result
            )
            
            return {
                'response': product_info_response,
                'type': 'product_selection',
                'selected_product': selection,
                'next_actions': selection_result.get('next_actions', []),
                'should_offer_synergy': selection_result.get('should_offer_synergy', False)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки выбора продукта: {e}")
            return {
                'response': f"Информация о продукте {selection}",
                'type': 'product_selection',
                'selected_product': selection
            }
    
    async def handle_link_request(self, user_id: str, product_name: str) -> Dict[str, Any]:
        """Обрабатывает запрос ссылки на продукт"""
        
        try:
            # Обрабатываем через контекстную систему
            link_result = self.context_system.handle_link_request(user_id, product_name)
            
            # Генерируем ответ с дополнительными предложениями
            link_response = await self._generate_link_response(product_name, link_result)
            
            return {
                'response': link_response,
                'type': 'product_link',
                'product': product_name,
                'high_purchase_intent': link_result.get('high_purchase_intent', False),
                'follow_up_actions': link_result.get('follow_up_actions', [])
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки запроса ссылки: {e}")
            return {
                'response': f"Ссылка на {product_name}",
                'type': 'product_link',
                'product': product_name
            }
    
    async def get_conversation_insights(self, user_id: str) -> Dict[str, Any]:
        """Получает инсайты о разговоре для админа"""
        
        return self.context_system.get_conversation_summary(user_id)
    
    async def _generate_clarifying_question(self, user_id: str, context_result: Dict) -> str:
        """Генерирует уточняющий вопрос"""
        
        guidance = context_result.get('conversation_guidance', {})
        recommended_action = guidance.get('recommended_action', {})
        
        question = recommended_action.get('content', 
                                        "Расскажите подробнее о ваших потребностях, чтобы я мог дать лучшие рекомендации")
        
        # Добавляем персонализированное введение
        user_insights = context_result.get('user_insights', {})
        if user_insights.get('is_returning_user', False):
            question = f"Рад снова вас видеть! {question}"
        
        return question
    
    async def _generate_product_info_response(self, product: str, selection_result: Dict) -> str:
        """Генерирует ответ с информацией о выбранном продукте"""
        
        base_response = f"🌿 {product}\n\n"
        
        # Добавляем основную информацию
        base_response += "Отличный выбор! Этот продукт поможет вам достичь ваших целей в области здоровья.\n\n"
        
        # Предлагаем дополнительные действия
        next_actions = selection_result.get('next_actions', [])
        if next_actions:
            base_response += "Что вас интересует:\n"
            for i, action in enumerate(next_actions, 1):
                base_response += f"{i}. {action}\n"
        
        # Предлагаем синергию
        if selection_result.get('should_offer_synergy', False):
            base_response += "\n💡 Могу рассказать о продуктах, которые хорошо сочетаются с этим выбором."
        
        return base_response
    
    async def _generate_link_response(self, product: str, link_result: Dict) -> str:
        """Генерирует ответ с ссылкой и дополнительными предложениями"""
        
        response = f"🔗 Ссылка на {product}:\n[Здесь будет ссылка]\n\n"
        
        if link_result.get('high_purchase_intent', False):
            response += "🎯 Вижу, что вы готовы к покупке!\n\n"
        
        # Добавляем последующие действия
        follow_up = link_result.get('follow_up_actions', [])
        if follow_up:
            response += "Также рекомендую:\n"
            for action in follow_up:
                response += f"• {action}\n"
        
        return response
    
    def _format_contextual_response(self, enhancement_result: Dict, context_result: Dict) -> str:
        """Форматирует контекстно-зависимый ответ"""
        
        base_response = enhancement_result.get('enhanced_response', '')
        
        # Добавляем предложения для продолжения диалога
        suggestions = enhancement_result.get('follow_up_suggestions', [])
        if suggestions:
            base_response += "\n\n" + suggestions[0]
        
        # Добавляем индикатор персонализации
        personalization_level = context_result.get('personalization_level', 'basic')
        if personalization_level == 'high':
            base_response += "\n\n🎯 *Рекомендация создана специально для вас на основе нашего диалога*"
        
        return base_response
    
    async def _fallback_response(self, message: str) -> Dict[str, Any]:
        """Базовый ответ при ошибках"""
        
        try:
            # Используем стандартный LLM без контекста
            basic_response = await self.llm.process_query(message, Intent.GENERAL_QUESTION)
            
            return {
                'response': basic_response,
                'type': 'basic_response',
                'products': [],
                'context_info': {}
            }
        except Exception as e:
            logger.error(f"❌ Ошибка базового ответа: {e}")
            return {
                'response': "Извините, произошла техническая ошибка. Попробуйте задать вопрос еще раз.",
                'type': 'error',
                'products': [],
                'context_info': {}
            }

# Пример использования
async def demo_contextual_bot():
    """Демонстрация работы контекстного бота"""
    
    bot = EnhancedAuroraBot()
    user_id = "demo_user_123"
    
    print("🚀 Демонстрация работы контекстного Aurora Bot")
    print("=" * 60)
    
    # Первый вопрос
    print("👤 Пользователь: Мне нужно что-то для печени")
    result1 = await bot.handle_user_message(user_id, "Мне нужно что-то для печени")
    print(f"🤖 Бот: {result1['response']}")
    print(f"📊 Тип ответа: {result1['type']}")
    print()
    
    # Второй вопрос (продолжение диалога)
    print("👤 Пользователь: А что лучше сочетается с этим?")
    result2 = await bot.handle_user_message(user_id, "А что лучше сочетается с этим?")
    print(f"🤖 Бот: {result2['response']}")
    print(f"📊 Тип ответа: {result2['type']}")
    print()
    
    # Выбор продукта
    print("👤 Пользователь: 1")
    result3 = await bot.handle_product_selection(user_id, "Силицитин")
    print(f"🤖 Бот: {result3['response']}")
    print()
    
    # Запрос ссылки
    print("👤 Пользователь: Пришли ссылку")
    result4 = await bot.handle_link_request(user_id, "Силицитин")
    print(f"🤖 Бот: {result4['response']}")
    print()
    
    # Инсайты о разговоре
    insights = await bot.get_conversation_insights(user_id)
    print("📈 Инсайты о разговоре:")
    print(f"   Обсуждено продуктов: {insights.get('recommendation_summary', {}).get('total_products_discussed', 0)}")
    print(f"   Стадия разговора: {insights.get('recommendation_summary', {}).get('conversation_stage', 'неизвестно')}")
    print(f"   Готовность к покупке: {insights.get('recommendation_summary', {}).get('purchase_readiness', 0):.2f}")

if __name__ == "__main__":
    # Запуск демонстрации
    asyncio.run(demo_contextual_bot())

