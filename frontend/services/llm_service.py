"""
LLM Service - обработка запросов через LLM с интеграцией всех модулей
"""
import os
import requests
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Импортируем восстановленные модули
from frontend.services.prompts import get_prompt_manager, IntentType
from frontend.services.cache_service import cache_service
from frontend.utils.synonyms import expand_query_with_synonyms
from frontend.utils.special_handlers import (
    is_small_talk,
    is_immunity_query,
    enhance_context_with_special_instructions
)

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Ответ от LLM"""
    text: str
    products: List[Dict[str, Any]]
    intent: str
    confidence: float
    cached: bool = False


class LLMService:
    """Сервис для работы с LLM с полным функционалом"""
    
    def __init__(self):
        """Инициализация LLM сервиса"""
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        # Определяем API URL
        if os.getenv("OPENROUTER_API_KEY"):
            self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        else:
            self.api_url = "https://api.openai.com/v1/chat/completions"
        
        # Модель
        model_name = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        # Исправляем неправильные названия моделей
        if "GPT-5" in model_name or "gpt-5" in model_name:
            model_name = "openai/gpt-4o-mini"
        elif "Chat" in model_name:
            model_name = "openai/gpt-3.5-turbo"
        self.model = model_name
        
        # Менеджер промптов
        self.prompt_manager = get_prompt_manager()
        
        logger.info(f"LLM Service initialized with model: {self.model}")
        logger.info("Integrated: PromptManager, CacheService, Synonyms, SpecialHandlers")
    
    async def process_query(
        self,
        user_query: str,
        context: Optional[str] = None,
        products: Optional[List[Dict]] = None,
        intent: Optional[IntentType] = None
    ) -> LLMResponse:
        """
        Обработка запроса пользователя через LLM
        
        Args:
            user_query: запрос пользователя
            context: дополнительный контекст
            products: найденные продукты
            intent: тип намерения (опционально)
        
        Returns:
            LLMResponse с ответом
        """
        logger.info(f"Processing query: {user_query[:50]}...")
        
        try:
            # ======================================
            # 1. SMALL-TALK ОБРАБОТКА
            # ======================================
            smalltalk_response = is_small_talk(user_query)
            if smalltalk_response:
                logger.info("Detected small-talk, returning quick response")
                return LLMResponse(
                    text=smalltalk_response,
                    products=[],
                    intent="small_talk",
                    confidence=1.0
                )
            
            # ======================================
            # 2. ПРОВЕРКА КЭША
            # ======================================
            cached_response = cache_service.get(user_query)
            if cached_response:
                logger.info("Cache hit! Returning cached response")
                return LLMResponse(
                    text=f"{cached_response}\n\n💡 _Информация из кэша для быстрого ответа_",
                    products=products or [],
                    intent="cached",
                    confidence=0.9,
                    cached=True
                )
            
            # ======================================
            # 3. РАСШИРЕНИЕ ЗАПРОСА СИНОНИМАМИ
            # ======================================
            expanded_query = expand_query_with_synonyms(user_query)
            if expanded_query != user_query:
                logger.debug(f"Query expanded with synonyms: {len(expanded_query)} chars")
            
            # ======================================
            # 4. ФОРМИРОВАНИЕ КОНТЕКСТА
            # ======================================
            full_context = self._build_context(context, products)
            
            # Дополняем контекст специальными инструкциями
            enhanced_context = enhance_context_with_special_instructions(
                full_context,
                user_query
            )
            
            # ======================================
            # 5. ВЫБОР СИСТЕМНОГО ПРОМПТА
            # ======================================
            if intent:
                system_prompt = self.prompt_manager.get_prompt(intent)
                logger.debug(f"Using prompt for intent: {intent}")
            else:
                system_prompt = self.prompt_manager.get_prompt_by_keywords(user_query)
                logger.debug("Auto-detected prompt from keywords")
            
            # ======================================
            # 6. ФОРМИРОВАНИЕ СООБЩЕНИЙ
            # ======================================
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Контекст из базы знаний:\n{enhanced_context}\n\nВопрос пользователя: {user_query}"
                }
            ]
            
            # ======================================
            # 7. ВЫЗОВ LLM
            # ======================================
            response_text = await self._call_llm(messages)
            
            # Добавляем подпись
            response_text += "\n\n*📚 Рекомендация на основе данных с сайта Aurora*"
            
            # ======================================
            # 8. КЭШИРОВАНИЕ ОТВЕТА
            # ======================================
            # Кэшируем только развернутые вопросы
            if len(user_query.strip()) > 20:
                cache_service.set(user_query, response_text)
                logger.debug("Response cached")
            
            # ======================================
            # 9. ВОЗВРАТ РЕЗУЛЬТАТА
            # ======================================
            return LLMResponse(
                text=response_text,
                products=products or [],
                intent=intent.value if intent else "auto_detected",
                confidence=0.85
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return LLMResponse(
                text="Извините, произошла ошибка при обработке запроса. Попробуйте переформулировать вопрос.",
                products=[],
                intent="error",
                confidence=0.0
            )
    
    def _build_context(
        self,
        context: Optional[str],
        products: Optional[List[Dict]]
    ) -> str:
        """Формирование контекста для LLM"""
        if not context and not products:
            return "NO_INFORMATION_FOUND"
        
        parts = []
        
        if context:
            parts.append(context)
        
        if products:
            parts.append("\n\nНайденные продукты:\n")
            for i, product in enumerate(products[:8], 1):  # Увеличили до 8
                name = product.get('product', product.get('name', 'Неизвестный продукт'))
                price = product.get('price', 'Цена не указана')
                category = product.get('category', '')
                description = product.get('description', product.get('short_description', ''))[:200]
                
                parts.append(f"\n{i}. Продукт: {name}")
                if category:
                    parts.append(f"   Категория: {category}")
                if price:
                    parts.append(f"   Цена: {price}")
                if description:
                    parts.append(f"   Описание: {description}...")
        
        result = "\n".join(parts)
        
        # Проверка на пустой контекст
        if result == "NO_INFORMATION_FOUND":
            return result
        
        return result
    
    async def _call_llm(self, messages: List[Dict]) -> str:
        """Вызов LLM API"""
        if not self.api_key:
            logger.warning("No API key configured, returning fallback response")
            return self._fallback_response()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"LLM API error: {response.status_code} - {response.text[:200]}")
                return self._fallback_response()
                
        except Exception as e:
            logger.error(f"Error calling LLM: {e}", exc_info=True)
            return self._fallback_response()
    
    def _fallback_response(self) -> str:
        """Резервный ответ если LLM недоступен"""
        return (
            "Я нашел подходящие продукты для вас. "
            "Посмотрите описания выше и выберите подходящий."
        )
    
    def get_cache_stats(self) -> Dict:
        """Получить статистику кэша"""
        return cache_service.get_stats()
    
    def clear_cache(self):
        """Очистить кэш"""
        cache_service.clear()
        logger.info("Cache cleared manually")


# Создаем глобальный экземпляр сервиса
llm_service = LLMService()