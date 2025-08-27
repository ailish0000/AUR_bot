# enhanced_llm.py
import os
import requests
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv
from nlp_processor import nlp_processor, Intent, ProcessedMessage
from enhanced_vector_db import enhanced_vector_db, SearchResult
from smart_search_engine import SmartSearchEngine
from enhanced_search_engine import initialize_enhanced_search, enhanced_search_engine
from immunity_recommendations import get_immunity_recommendation_template

# Синонимы для поиска омега-3
OMEGA_SYNONYMS = [
    "омега-3", "омега 3", "омега3", "omega", "omega-3", "omega 3", "omega3",
    "рыбий жир", "рыбьего жира", "рыбьим жиром", "рыбьему жиру",
    "пнжк", "полиненасыщенные жирные кислоты", "жирные кислоты",
    "эпк", "дгк", "epa", "dha"
]

# Синонимы для поиска магния
MAGNESIUM_SYNONYMS = [
    "магний", "магния", "магнием", "магнию", "magnesium", "mg",
    "продукты с магнием", "содержащие магний", "с содержанием магния"
]

from smart_nlp_parser import SmartNLPParser

load_dotenv()

@dataclass
class ResponseContext:
    message: ProcessedMessage
    search_results: List[SearchResult]
    cached_response: Optional[str] = None

class EnhancedLLM:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions" if os.getenv("OPENROUTER_API_KEY") else "https://api.openai.com/v1/chat/completions"
        model_name = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        # Исправляем неправильные названия моделей
        if "GPT-5" in model_name or "gpt-5" in model_name:
            model_name = "openai/gpt-4o-mini"  # Более доступная модель
        elif "Chat" in model_name:
            model_name = "openai/gpt-3.5-turbo"
        self.model = model_name
        
        # Максимальная длина ответа убрана - обрабатывается в bot.py
        # self.max_response_length = 900
        
        # Инициализируем усиленную систему поиска
        try:
            global enhanced_search_engine
            if enhanced_search_engine is None:
                enhanced_search_engine = initialize_enhanced_search(
                    vector_db=enhanced_vector_db,
                    nlp_processor=nlp_processor
                )
                print("🚀 Усиленная система поиска инициализирована")
        except Exception as e:
            print(f"⚠️ Ошибка инициализации усиленного поиска: {e}")
        
        # Инициализируем умный поиск
        try:
            self.smart_search = SmartSearchEngine()
            self.smart_nlp = SmartNLPParser()
            print("🧠 Умный поиск инициализирован")
        except Exception as e:
            print(f"⚠️ Умный поиск недоступен: {e}")
            self.smart_search = None
            self.smart_nlp = None
        
        # Системные промпты для разных типов запросов
        self.system_prompts = {
            Intent.PRODUCT_SELECTION: """
Ты - консультант по продукции компании Аврора. 
Ты даешь рекомендации по продуктам на основе официальных данных с сайта Aurora.

🚨 КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА - НАРУШЕНИЕ НЕДОПУСТИМО:
1. Отвечай только на основе предоставленной информации из базы знаний
2. РЕКОМЕНДУЙ ВСЕ НАЙДЕННЫЕ ПРОДУКТЫ ТОЛЬКО ЕСЛИ:
   - Пользователь явно просит "все варианты", "все продукты", "что еще есть"
   - Пользователь спрашивает "какой еще", "еще есть", "помимо этого"
   - Пользователь хочет полный обзор ассортимента
3. В ОБЫЧНЫХ СЛУЧАЯХ рекомендуй 2-4 наиболее подходящих продукта
4. При запросах об антипаразитарных средствах ОБЯЗАТЕЛЬНО рекомендуй ВСЕ доступные продукты: Еломил, Гепосин, Лист Черного Ореха Экстра Капс (BWL Extra Caps), Лист Черного Ореха Экстра Табс (BWL Extra Tabs), Осина Экстра, Кошачий Коготь, Сиалон-Микс манго
5. При простуде/бронхите ОБЯЗАТЕЛЬНО рекомендуй КОМПЛЕКС: Аргент Макс (антибактериальный) + Солберри + Битерон, плюс для иммунитета (Витамин С, Ин-Аурин, БАРС-2)
6. Для печени - гепатопротекторы (Силицитин в первую очередь)
7. При запросах о кальции/костях ОБЯЗАТЕЛЬНО рекомендуй: Румарин Кальций, Кальций Банан, Кальций-Утро
8. При запросах о магнии ОБЯЗАТЕЛЬНО рекомендуй ВСЕ продукты: Магний Плюс (Mg Plus), Магний Табс (Mg Tabs), Магний-Вечер (Mg-Evening). ИГНОРИРУЙ любые продукты БЕЗ слова "магний" в названии при запросах о магнии
9. При запросах о коллагене - если пользователь просит "все варианты" или "что еще есть", то рекомендуй ВСЕ найденные продукты с коллагеном
10. Если продукт не подходит по описанию проблемы - все равно укажи его, но отметь особенности применения
11. Укажи способ применения и синергию продуктов
12. ОТВЕТ ДОЛЖЕН БЫТЬ ИНФОРМАТИВНЫМ И ПОЛНЫМ

🚨 СТРОГИЕ ПРАВИЛА ОБЩЕНИЯ - ОБЯЗАТЕЛЬНО:
- Ты даешь рекомендации по продуктам на основе данных Aurora
- Продукты безопасные и качественные на основе официальных данных
- Можешь рекомендовать продукты для поддержания здоровья и восстановления
- При запросах об антипаразитарных средствах предлагай ВСЕ доступные варианты
- ЗАПРЕЩЕНО: слово "врач" - ВСЕГДА используй "СПЕЦИАЛИСТ"
- ЗАПРЕЩЕНО: "проконсультируйтесь с врачом" - используй "получить рекомендации от специалиста"
- ЗАПРЕЩЕНО: "убедиться в безопасности" - используй "получить индивидуальные рекомендации"
- ЗАПРЕЩЕНО: "безопасности применения" - используй "подобрать оптимальную дозировку"
- При вопросах о детях: рекомендуй консультацию со СПЕЦИАЛИСТОМ
- Говори о пользе индивидуальных рекомендаций без запугиваний
- Всегда подчеркивай, что это рекомендации по продуктам Aurora
- ЗАПРЕЩЕНО: использовать markdown-разметку (###, **, __, *, #) - пиши обычным текстом
10. В конце предложи:
   - 2-3 контекстных вопроса по рекомендованным продуктам
   - "Нужна ссылка на какой-то из продуктов?"
""",
            Intent.PRODUCT_INQUIRY: """
Ты - консультант по продукции компании Аврора.
Ты даешь информацию о продуктах на основе официальных данных с сайта Aurora.

🚨 КРИТИЧЕСКИ ВАЖНО:
1. РАССКАЗЫВАЙ ТОЛЬКО О ЗАПРАШИВАЕМОМ ПРОДУКТЕ
2. НЕ предлагай другие продукты без прямого запроса
3. НЕ рекомендуй комплексные решения
4. Фокусируйся на конкретном продукте из вопроса

Что включить:
- Назначение и показания к применению
- Способ применения и дозировка  
- Основные свойства и преимущества
- Противопоказания (если есть)
- Форма выпуска

🚨 СТРОГИЕ ПРАВИЛА ОБЩЕНИЯ - ОБЯЗАТЕЛЬНО:
- Ты даешь информацию о продуктах на основе данных Aurora
- Можешь рассказывать о свойствах и пользе продуктов
- ЗАПРЕЩЕНО: слово "врач" - ВСЕГДА используй "СПЕЦИАЛИСТ"
- ЗАПРЕЩЕНО: "проконсультируйтесь с врачом" - используй "получить рекомендации от специалиста"
- ЗАПРЕЩЕНО: "убедиться в безопасности" - используй "получить индивидуальные рекомендации"
- ЗАПРЕЩЕНО: "безопасности применения" - используй "подобрать оптимальную дозировку"
- Всегда подчеркивай, что это информация о продуктах Aurora
- ЗАПРЕЩЕНО: использовать markdown-разметку (###, **, __, *, #) - пиши обычным текстом

В конце предложи:
- 2-3 контекстных вопроса по ЭТОМУ продукту
- "Показать ссылку на этот продукт?"
""",
            Intent.COMPOSITION_INQUIRY: """
Ты - консультант по продукции компании Аврора.
Ты даешь информацию о составе продуктов на основе официальных данных с сайта Aurora.

Правила:
1. Перечисли все компоненты из базы знаний
2. Объясни пользу основных ингредиентов
3. Укажи источник информации
4. Будь информативной но понятной
5. ОТВЕТ ДОЛЖЕН БЫТЬ КРАТКИМ (до 800 символов)
6. Если информации недостаточно, извинись и предложи обратиться к консультанту Наталье
7. ЗАПРЕЩЕНО: использовать markdown-разметку (###, **, __, *, #) - пиши обычным текстом
8. В конце предложи:
   - 2-3 контекстных вопроса по компонентам
   - "Заказать этот продукт?" (если обсуждался конкретный продукт)
""",
            Intent.COMPLAINT: """
Ты - консультант по продукции компании Аврора.
Ты помогаешь с вопросами по продуктам на основе официальных данных с сайта Aurora.

Правила:
1. Проявляй понимание и сочувствие
2. Предложи альтернативные варианты применения
3. Рекомендуй комплексные решения
4. Предложи обратиться к специалисту
5. Не обещай то, чего нет в базе знаний
6. ОТВЕТ ДОЛЖЕН БЫТЬ КРАТКИМ (до 800 символов)
7. Если информации недостаточно, извинись и предложи обратиться к консультанту Наталье
8. ЗАПРЕЩЕНО: использовать markdown-разметку (###, **, __, *, #) - пиши обычным текстом
9. В конце предложи 2-3 дополнительных вопроса ТОЛЬКО о продуктах из контекста (например: "Состав и компоненты", "Способ применения", "Противопоказания")
""",
            Intent.GENERAL_QUESTION: """
Ты - консультант по продукции компании Аврора.
Ты отвечаешь на вопросы о продуктах на основе официальных данных с сайта Aurora.

Правила:
1. Используй только информацию из базы знаний
2. Рекомендуй конкретные продукты если подходящие есть
3. Будь дружелюбной и профессиональной
4. Указывай источники информации
5. При необходимости рекомендуй консультацию специалиста
6. ОТВЕТ ДОЛЖЕН БЫТЬ КРАТКИМ (до 800 символов)
7. Если информации недостаточно, извинись и предложи обратиться к консультанту Наталье
8. ЗАПРЕЩЕНО: использовать markdown-разметку (###, **, __, *, #) - пиши обычным текстом
9. В конце предложи 2-3 дополнительных вопроса ТОЛЬКО о продуктах из контекста (например: "Состав и компоненты", "Способ применения", "Противопоказания")
"""
        }
    
    def _build_context(self, search_results: List[SearchResult]) -> str:
        """Создает контекст для LLM на основе результатов поиска"""
        if not search_results:
            return "NO_INFORMATION_FOUND"
        
        context_parts = []
        sources = set()
        
        for result in search_results:
            chunk = result.chunk
            source = result.source
            sources.add(source)
            
            context_part = f"""
Продукт: {chunk.product}
Тип информации: {chunk.chunk_type}
Содержание: {chunk.text}
Релевантность: {result.score:.2f}
Источник: {source}
"""
            
            # Добавляем метаданные если есть
            if chunk.metadata:
                if "category" in chunk.metadata:
                    context_part += f"Категория: {chunk.metadata['category']}\n"
                if "use_cases" in chunk.metadata:
                    context_part += f"Применение: {', '.join(chunk.metadata['use_cases'][:3])}\n"
            
            context_parts.append(context_part)
        
        # Добавляем список источников
        sources_text = f"\n\nИсточники информации: {', '.join(sources)}"
        
        return "\n---\n".join(context_parts) + sources_text
    
    def _get_system_prompt(self, intent: Intent) -> str:
        """Возвращает системный промпт для конкретного намерения"""
        return self.system_prompts.get(intent, self.system_prompts[Intent.GENERAL_QUESTION])
    
    def _should_search_immediately(self, intent: Intent) -> bool:
        """Определяет, нужно ли сразу искать в базе для данного намерения"""
        immediate_search_intents = {
            Intent.PRODUCT_SELECTION,
            Intent.PRODUCT_INQUIRY,
            Intent.COMPOSITION_INQUIRY,
            Intent.DOSAGE_INQUIRY,
            Intent.CONTRAINDICATIONS
        }
        return intent in immediate_search_intents
    
    def _get_search_filters(self, message: ProcessedMessage) -> Optional[Dict[str, Any]]:
        """Создает фильтры для поиска на основе обработанного сообщения"""
        filters = {}
        
        # Если найдены продукты в сообщении, фильтруем по ним
        if message.entities:
            products = [entity.text for entity in message.entities if entity.label == "PRODUCT"]
            if products:
                filters["product"] = products[0]  # Берем первый найденный продукт
        
        # Фильтры по типу намерения
        if message.intent == Intent.COMPOSITION_INQUIRY:
            filters["chunk_type"] = "composition"
        elif message.intent == Intent.DOSAGE_INQUIRY:
            filters["chunk_type"] = "dosage"
        elif message.intent == Intent.CONTRAINDICATIONS:
            filters["chunk_type"] = "contraindications"
        elif message.intent == Intent.PRODUCT_SELECTION:
            # Для подбора продуктов ищем в benefits и description
            filters["chunk_type"] = ["benefits", "description"]
        
        return filters if filters else None
    
    def process_query(self, user_text: str) -> str:
        """Основной метод обработки запроса пользователя"""
        try:
            # 0. Быстрая обработка small-talk без поиска
            smalltalk = user_text.strip().lower()
            if smalltalk in {"привет", "здравствуйте", "добрый день", "добрый вечер"}:
                return (
                    "Привет! Я помогу с подбором продуктов Авроры. "
                    "Спроси, например: 'От простуды', 'Для печени', 'Состав Солберри-H', 'Как принимать Битерон-H'."
                )
            if smalltalk in {"как дела?", "как дела", "как ты?", "как ты"}:
                return (
                    "Спасибо, все отлично и я готова помочь! Опиши проблему или спроси про продукт."
                )
            # 1.5. Специальная обработка запросов об иммунитете (приоритет над кэшем)
            if self._is_immunity_query(user_text):
                # Проверяем кэш для запросов об иммунитете
                cached_response = enhanced_vector_db.get_cached_response(user_text)
                if cached_response:
                    immunity_response = f"{cached_response}\n\n💡 _Информация из кэша для быстрого ответа_"
                else:
                    immunity_response = get_immunity_recommendation_template()
                    enhanced_vector_db.cache_response(user_text, immunity_response)
                
                # ВСЕГДА возвращаем контекст для запросов об иммунитете
                from immunity_recommendations import IMMUNITY_CORE_PRODUCTS
                immunity_context = []
                for product_info in IMMUNITY_CORE_PRODUCTS:
                    immunity_context.append({
                        "product": product_info["name"],
                        "url": "",  # Будет найден при запросе ссылки
                        "image_id": "",  # Будет найден при запросе ссылки
                        "short_description": product_info["description"]
                    })
                
                return immunity_response, immunity_context
            
            # 1. Проверяем кэш для всех остальных запросов
            cached_response = enhanced_vector_db.get_cached_response(user_text)
            if cached_response:
                return f"{cached_response}\n\n💡 _Информация из кэша для быстрого ответа_"
            
            
            # 2. Обрабатываем сообщение через NLP
            processed_message = nlp_processor.process_message(user_text)
            
            # 3. УСИЛЕННЫЙ МНОГОУРОВНЕВЫЙ ПОИСК
            search_results = []
            
            # Используем усиленную систему поиска для ВСЕХ запросов
            if enhanced_search_engine:
                print(f"🚀 Используем усиленную систему поиска")
                enhanced_results = enhanced_search_engine.enhanced_search(
                    query=processed_message.expanded_query,
                    max_results=8,  # Больше результатов для лучшего покрытия
                    min_confidence=0.2  # Снижаем порог для широкого охвата
                )
                
                # Конвертируем результаты в формат SearchResult
                for er in enhanced_results:
                    search_results.append(SearchResult(
                        chunk=type('Chunk', (), {
                            'product': er.product,
                            'chunk_type': er.chunk_type,
                            'text': er.content,
                            'metadata': er.metadata
                        })(),
                        score=er.relevance_score,
                        source=f"{er.source} ({', '.join(er.strategies_used)})"
                    ))
                
                print(f"🎯 Усиленный поиск нашел {len(search_results)} результатов")
            
            # 4. FALLBACK: если усиленный поиск не дал результатов, используем старую систему
            if not search_results:
                print(f"🔄 Fallback к старой системе поиска")
                if self._should_search_immediately(processed_message.intent):
                    filters = self._get_search_filters(processed_message)
                    search_results = enhanced_vector_db.search(
                        query=processed_message.expanded_query,
                        filters=filters,
                        limit=3
                    )
                
                # Поиск по продуктам
                if processed_message.entities:
                    for entity in processed_message.entities:
                        if entity.label == "PRODUCT":
                            product_results = enhanced_vector_db.search_by_product(
                                entity.text, limit=2
                            )
                            search_results.extend(product_results)
                
                # Поиск по случаю применения
                if not search_results and processed_message.intent in [
                    Intent.GENERAL_QUESTION, Intent.PRODUCT_SELECTION
                ]:
                    search_results = enhanced_vector_db.search_by_use_case(
                        processed_message.expanded_query, limit=3
                    )
                
                # Общий поиск
                if not search_results:
                    search_results = enhanced_vector_db.search(
                        processed_message.expanded_query, limit=2
                    )

            # 5.1. Локальный поиск всегда имеет приоритет - для ЛЮБЫХ запросов 
            local_context = self._build_local_kb_context(processed_message.expanded_query)
            if local_context:
                # Всегда используем локальный контекст для LLM (лучшие результаты поиска)
                local_info = self._build_context_from_local(local_context)
                if local_info and local_info != "NO_INFORMATION_FOUND":
                    context = local_info
                    print(f"🔍 Используем локальный поиск (найдено продуктов: {local_context.count('Продукт: ')})")
                # Если нет API ключа, возвращаем fallback ответ
                if not self.api_key:
                    provisional = self._fallback_response(local_context)
                    return provisional
            
            # 6. Формируем контекст для LLM
            if 'context' not in locals() or not context:
                context = self._build_context(search_results)
            
            # 6.1. Проверяем, есть ли информация
            if context == "NO_INFORMATION_FOUND":
                # Создаем вежливый ответ с предложением обратиться к консультанту
                response = (
                    "😔 Извините, но у меня нет информации по вашему вопросу в базе знаний.\n\n"
                    "💡 Возможно, стоит:\n"
                    "• Переформулировать вопрос\n"
                    "• Уточнить название продукта\n"
                    "• Обратиться к консультанту\n\n"
                    "✉️ Напишите Наталье — она обязательно поможет!"
                )
                return response
            
            # 7. Если это жалоба с негативной тональностью, добавляем особую обработку
            if (processed_message.intent == Intent.COMPLAINT or 
                processed_message.sentiment == "negative"):
                context += "\n\nВНИМАНИЕ: Пользователь выражает недовольство. Нужно проявить понимание и предложить решение."
            
            # 7.1. Проверяем, просит ли пользователь "все варианты"
            all_options_keywords = ["какой еще", "еще есть", "помимо этого", "что еще", "все варианты", "все продукты", "что еще есть", "какие еще", "другие варианты", "еще варианты", "полный обзор", "весь ассортимент"]
            user_text_lower = processed_message.text.lower()
            is_all_options_request = any(keyword in user_text_lower for keyword in all_options_keywords)
            
            if is_all_options_request:
                context += "\n\nВНИМАНИЕ: Пользователь просит ВСЕ варианты продуктов. РЕКОМЕНДУЙ ВСЕ НАЙДЕННЫЕ ПРОДУКТЫ!"
            
            # 8. Отправляем запрос к LLM
            response = self._ask_llm(
                processed_message.text,
                context,
                processed_message.intent
            )
            
            # 9. Кэшируем ответ для популярных вопросов
            if len(user_text.strip()) > 20:  # Кэшируем только развернутые вопросы
                enhanced_vector_db.cache_response(user_text, response)
            
            return response
            
        except Exception as e:
            print(f"❌ Ошибка при обработке запроса: {e}")
            return "Извините, произошла ошибка при обработке вашего запроса. Попробуйте переформулировать вопрос."

    def _expand_query_with_synonyms(self, query: str) -> str:
        """Расширяет запрос синонимами омега-3 и магния"""
        query_lower = query.lower()
        
        # Проверяем, содержит ли запрос синонимы омега-3
        for synonym in OMEGA_SYNONYMS:
            if synonym in query_lower:
                # Добавляем все синонимы омега-3 к запросу
                expanded_terms = " ".join(OMEGA_SYNONYMS)
                return f"{query} {expanded_terms}"
        
        # Проверяем, содержит ли запрос синонимы магния
        for synonym in MAGNESIUM_SYNONYMS:
            if synonym in query_lower:
                # Добавляем все синонимы магния к запросу
                expanded_terms = " ".join(MAGNESIUM_SYNONYMS)
                return f"{query} {expanded_terms}"
        
        return query

    def _build_local_kb_context(self, expanded_query: str) -> Optional[str]:
        """Умный поиск с фильтрами по метаданным"""
        try:
            # Расширяем запрос синонимами омега-3
            expanded_query = self._expand_query_with_synonyms(expanded_query)
            
            # Используем умный поиск если доступен
            if self.smart_search and self.smart_nlp:
                return self._smart_search_context(expanded_query)
            else:
                # Fallback к старому поиску
                return self._fallback_local_search(expanded_query)
        except Exception as e:
            print(f"Ошибка в _build_local_kb_context: {e}")
            return None
    
    def _build_context_from_local(self, local_context: str) -> str:
        """Конвертирует локальный контекст в формат для LLM"""
        if not local_context:
            return "NO_INFORMATION_FOUND"
        
        # Парсим локальный контекст и форматируем для LLM
        lines = local_context.split('\n')
        products = []
        current_product = {}
        
        for line in lines:
            if line.startswith('Продукт: '):
                if current_product:
                    products.append(current_product)
                current_product = {'name': line.replace('Продукт: ', '').strip()}
            elif line.startswith('Категория: '):
                current_product['category'] = line.replace('Категория: ', '').strip()
            elif line.startswith('Краткое описание: '):
                current_product['description'] = line.replace('Краткое описание: ', '').strip()
        
        if current_product:
            products.append(current_product)
        
        if not products:
            return "NO_INFORMATION_FOUND"
        
        # Форматируем для LLM
        formatted_chunks = []
        for product in products:
            chunk = f"Продукт: {product['name']}\n"
            if 'category' in product:
                chunk += f"Категория: {product['category']}\n"
            if 'description' in product:
                chunk += f"Описание: {product['description']}\n"
            formatted_chunks.append(chunk)
        
        return "\n---\n".join(formatted_chunks)

    def _search_in_kb(self, kb_data: list, terms: list, source: str, found_products: set) -> list:
        """Поиск в конкретной базе знаний с ранжированием по релевантности"""
        matches = []
        for item in kb_data:
            product = item.get("product", "")
            product_id = item.get("id", "")
            
            # Проверяем все поля на вхождение терминов
            searchable_fields = {
                "product": item.get("product", ""),
                "description": item.get("description", ""),
                "short_description": item.get("short_description", ""),
                "benefits": "; ".join(item.get("benefits", [])),
                "short_benefits": "; ".join(item.get("short_benefits", [])),
                "composition": item.get("composition", ""),
                "dosage": item.get("dosage", ""),
                "contraindications": item.get("contraindications", ""),
                "category": item.get("category", ""),
            }
            
            # Подсчитываем релевантность
            relevance_score = 0
            matching_fields = []
            
            for field_name, field_text in searchable_fields.items():
                if field_text:
                    matches_in_field = sum(1 for term in terms if term in field_text.lower())
                    if matches_in_field > 0:
                        matching_fields.append(field_name)
                        # Гораздо более высокий вес для названия продукта
                        if field_name == "product":
                            relevance_score += matches_in_field * 10  # Максимальный приоритет названию
                        elif field_name in ["short_description", "benefits"]:
                            relevance_score += matches_in_field * 3
                        else:
                            relevance_score += matches_in_field
            
            if relevance_score > 0 and product_id not in found_products:
                found_products.add(product_id)
                
                # Формируем краткую информацию о продукте
                category = item.get("category", "")
                form = item.get("form", "")
                short_desc = item.get("short_description", "")
                
                part = (
                    f"Продукт: {product}\n"
                    f"Категория: {category}\n"
                    f"Форма: {form}\n"
                    f"Краткое описание: {short_desc}\n"
                    f"Релевантность: {min(0.95, 0.50 + relevance_score * 0.1):.2f}\n"
                    f"Источник: {source}\n"
                )
                matches.append((relevance_score, part))
        
        # Сортируем по релевантности и берем ВСЕ найденные продукты
        matches.sort(key=lambda x: x[0], reverse=True)
        return [match[1] for match in matches]
    
    def _ask_llm(self, question: str, context: str, intent: Intent) -> str:
        """Отправляет запрос к OpenAI API"""
        if not self.api_key:
            return self._fallback_response(context)
        
        system_prompt = self._get_system_prompt(intent)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"Контекст из базы знаний:\n{context}\n\nВопрос пользователя: {question}"
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                answer = result["choices"][0]["message"]["content"]
                
                # Конвертируем Markdown в HTML для корректного отображения
                answer = self._convert_markdown_to_html(answer)
                
                # Заменяем стандартную подпись LLM на нашу
                import re
                answer = re.sub(r'\(Источник:.*?\)', '', answer)
                answer = answer.strip()
                
                # Добавляем нашу подпись
                answer += "\n\n*📚 Рекомендация на основе данных с сайта Aurora*"
                
                # Ограничение длины убрано - обрабатывается в bot.py
                # answer = self._limit_response_length(answer)
                
                return answer
            else:
                print(f"❌ Ошибка API ({response.status_code}): {response.text[:200]}")
                return self._fallback_response(context)
                
        except Exception as e:
            print(f"❌ Ошибка при запросе к LLM: {e}")
            return self._fallback_response(context)
    
    def _convert_markdown_to_html(self, text: str) -> str:
        """Конвертирует Markdown разметку в обычный текст без HTML тегов"""
        import re
        
        # Убираем все HTML теги
        text = re.sub(r'<[^>]+>', '', text)
        
        # Заменяем **text** на обычный текст (убираем звездочки)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        
        # Заменяем *text* на обычный текст (убираем звездочки)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        
        # Заменяем `text` на обычный текст (убираем обратные кавычки)
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        # Заменяем _text_ на обычный текст (убираем подчеркивания)
        text = re.sub(r'_(.*?)_', r'\1', text)
        
        return text
    
    def _generate_follow_up_questions(self, products_info: dict) -> str:
        """Генерирует предложения дополнительных вопросов на основе найденных продуктов"""
        if not products_info:
            return ""
        
        questions = []
        
        for product_name in products_info.keys():
            product_lower = product_name.lower()
            
            # Вопросы о составе
            if "солберри" in product_lower or "облепих" in product_lower:
                questions.extend([
                    "• Расскажи о пользе облепихи",
                    "• Какие витамины содержит облепиха?",
                    "• Как облепиха укрепляет иммунитет?"
                ])
            elif "битерон" in product_lower or "свекл" in product_lower:
                questions.extend([
                    "• Расскажи о пользе свеклы",
                    "• Как свекла влияет на кровь?",
                    "• Какие вещества содержит свекла?"
                ])
            elif "аргент" in product_lower or "серебр" in product_lower:
                questions.extend([
                    "• Как работает серебро против бактерий?",
                    "• Расскажи о применении серебра",
                    "• Безопасно ли серебро для организма?"
                ])
            
            # Общие вопросы о продукте
            questions.extend([
                f"• Подробнее о составе {product_name}",
                f"• Как правильно принимать {product_name}?",
                f"• Есть ли противопоказания у {product_name}?",
                f"• Можно ли сочетать {product_name} с другими продуктами?"
            ])
        
        # Убираем дубликаты и ограничиваем количество
        unique_questions = list(dict.fromkeys(questions))[:6]
        
        if unique_questions:
            return (
                "\n\n💡 Могу рассказать подробнее:\n" + 
                "\n".join(unique_questions) +
                "\n\n💬 Просто спроси!"
            )
        
        return ""

    def _fallback_response(self, context: str) -> str:
        """Создает ответ без использования LLM с предложением выбора продуктов"""
        if not context or context == "NO_INFORMATION_FOUND" or "Информация не найдена" in context:
            response = (
                "😔 Извините, но у меня нет информации по вашему вопросу в базе знаний.\n\n"
                "💡 Возможно, стоит:\n"
                "• Переформулировать вопрос\n"
                "• Уточнить название продукта\n"
                "• Обратиться к консультанту\n\n"
                "✉️ Напишите Наталье — она обязательно поможет!"
            )
            return response
        
        # Парсим контекст для извлечения информации о продуктах
        lines = context.split('\n')
        products = []
        current_product = {}
        
        for line in lines:
            if line.startswith('Продукт: '):
                if current_product:
                    products.append(current_product)
                current_product = {'name': line.replace('Продукт: ', '').strip()}
            elif line.startswith('Категория: '):
                current_product['category'] = line.replace('Категория: ', '').strip()
            elif line.startswith('Форма: '):
                current_product['form'] = line.replace('Форма: ', '').strip()
            elif line.startswith('Краткое описание: '):
                current_product['description'] = line.replace('Краткое описание: ', '').strip()
        
        if current_product:
            products.append(current_product)
        
        if not products:
            return "Информация найдена, но требует уточнения. Пожалуйста, обратитесь к консультанту."
        
        # Формируем ответ с предложением выбора
        if len(products) == 1:
            product = products[0]
            response = f"🌿 **{product['name']}**\n\n"
            if 'category' in product:
                response += f"📂 Категория: {product['category']}\n"
            if 'form' in product:
                response += f"💊 Форма: {product['form']}\n"
            if 'description' in product:
                response += f"📝 {product['description']}\n\n"
            response += "💡 Задайте вопрос о составе, способе применения или противопоказаниях для получения подробной информации."
        else:
            response = f"🔍 Найдено **{len(products)} продуктов** по вашему запросу:\n\n"
            
            for i, product in enumerate(products, 1):
                response += f"**{i}. {product['name']}**\n"
                if 'category' in product:
                    response += f"   📂 {product['category']}\n"
                if 'form' in product:
                    response += f"   💊 {product['form']}\n"
                if 'description' in product:
                    response += f"   📝 {product['description'][:100]}...\n"
                response += "\n"
            
            response += "💡 **Выберите продукт и задайте вопрос о нем:**\n"
            response += "• Состав и компоненты\n"
            response += "• Способ применения\n"
            response += "• Противопоказания\n"
            response += "• Полезные свойства"
        
        return response

    def _limit_response_length(self, response: str, max_length: int = None) -> str:
        """Ограничивает длину ответа до указанного количества символов"""
        # Метод отключен - вся логика обрезания теперь в bot.py
        return response
    
    def _smart_search_context(self, query: str) -> Optional[str]:
        """Умный поиск с использованием NLP и фильтров"""
        try:
            # Парсим запрос для извлечения фильтров
            parsed_query = self.smart_nlp.parse_query(query)
            
            print(f"🧠 Умный поиск: '{query}' (уверенность: {parsed_query.confidence:.2f})")
            
            # Выполняем поиск с фильтрами, используя оригинальный запрос
            results = self.smart_search.search(query, parsed_query.filters)
            
            if not results:
                print("❌ Умный поиск не дал результатов")
                # Пробуем поиск без фильтров
                print("🔄 Пробуем поиск без фильтров...")
                results = self.smart_search.search(query)
                
                if not results:
                    print("❌ Поиск без фильтров тоже не дал результатов")
                    return None
                else:
                    print(f"✅ Поиск без фильтров нашел {len(results)} продуктов")
            
            print(f"✅ Найдено {len(results)} продуктов умным поиском")
            
            # Формируем контекст для LLM в старом формате
            context_parts = []
            
            for result in results:
                part = f"Продукт: {result.product_name}\n"
                part += f"Категория: {result.category}\n"
                
                # Добавляем краткое описание из свойств
                if result.properties:
                    part += f"Свойства: {', '.join(result.properties[:3])}\n"
                
                if result.indications:
                    part += f"Показания: {', '.join(result.indications[:2])}\n"
                
                # Добавляем оригинальные данные
                original = result.original_data.get('original_data', {})
                if original.get('short_description'):
                    part += f"Краткое описание: {original['short_description']}\n"
                
                context_parts.append(part)
            
            return "\n---\n".join(context_parts)
            
        except Exception as e:
            print(f"Ошибка умного поиска: {e}")
            return None
    
    def _fallback_local_search(self, expanded_query: str) -> Optional[str]:
        """Fallback к старому локальному поиску"""
        try:
            import json
            # Ищем по значимым словам (длиной больше 2 символов, исключая служебные слова)
            stop_words = {"с", "и", "для", "на", "от", "по", "в", "к", "из", "до", "за", "при", "про", "без", "под", "над", "о", "об", "что", "как", "где", "когда", "who", "what", "where", "when", "how", "with", "and", "for", "the", "of", "to", "in", "a", "an"}
            terms = [t.strip().lower() for t in expanded_query.split() 
                    if len(t.strip()) > 2 and t.strip().lower() not in stop_words]
            if not terms:
                return None
            
            matches = []
            found_products = set()  # Для отслеживания уникальных продуктов
            
            # Поиск в основной базе знаний
            try:
                with open("knowledge_base.json", "r", encoding="utf-8") as f:
                    kb_main = json.load(f)
                matches.extend(self._search_in_kb(kb_main, terms, "knowledge_base.json", found_products))
            except Exception as e:
                print(f"Ошибка чтения knowledge_base.json: {e}")
            
            # Поиск в новой базе знаний
            try:
                with open("knowledge_base_new.json", "r", encoding="utf-8") as f:
                    kb_new = json.load(f)
                matches.extend(self._search_in_kb(kb_new, terms, "knowledge_base_new.json", found_products))
            except Exception as e:
                print(f"Ошибка чтения knowledge_base_new.json: {e}")
            
            if matches:
                return "\n---\n".join(matches)
            return None
            
        except Exception as e:
            print(f"Ошибка локального поиска: {e}")
            return None
    
    def _is_immunity_query(self, query: str) -> bool:
        """Проверяет является ли запрос о иммунитете"""
        immunity_keywords = [
            'иммунитет', 'иммунн', 'immunity', 
            'для укрепления иммунитета', 'укрепления иммунитета',
            'для иммунитета', 'укрепить иммунитет', 'повысить иммунитет',
            'поддержать иммунитет', 'поддержка иммунитета',
            'защитные силы', 'защитных сил', 'защита организма',
            'сопротивляемость организма', 'повысить сопротивляемость'
        ]
        
        query_lower = query.lower().strip()
        return any(keyword in query_lower for keyword in immunity_keywords)

# Создаем глобальный экземпляр
enhanced_llm = EnhancedLLM()
