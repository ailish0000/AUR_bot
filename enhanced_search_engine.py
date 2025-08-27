#!/usr/bin/env python3
"""
Усиленная система поиска с множественными стратегиями для максимальной точности
"""

import re
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from difflib import SequenceMatcher

@dataclass
class SearchStrategy:
    """Стратегия поиска"""
    name: str
    priority: int
    weight: float
    description: str

@dataclass
class EnhancedSearchResult:
    """Расширенный результат поиска"""
    content: str
    product: str
    chunk_type: str
    relevance_score: float
    confidence: float
    strategies_used: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""

class SearchStrategyType(Enum):
    """Типы стратегий поиска"""
    EXACT_MATCH = "exact_match"
    SEMANTIC_SEARCH = "semantic_search" 
    FUZZY_MATCH = "fuzzy_match"
    SYNONYM_EXPANSION = "synonym_expansion"
    CATEGORICAL_SEARCH = "categorical_search"
    COMPOSITIONAL_SEARCH = "compositional_search"
    HEALTH_CONDITION_SEARCH = "health_condition_search"
    INGREDIENT_SEARCH = "ingredient_search"
    BRAND_SEARCH = "brand_search"
    FALLBACK_BROAD = "fallback_broad"

class EnhancedSearchEngine:
    """Усиленная система поиска с множественными стратегиями"""
    
    def __init__(self, vector_db=None, nlp_processor=None):
        self.vector_db = vector_db
        self.nlp_processor = nlp_processor
        
        # Стратегии поиска в порядке приоритета
        self.search_strategies = {
            SearchStrategyType.EXACT_MATCH: SearchStrategy(
                "Точное совпадение", 1, 1.0, "Поиск точных фраз и названий"
            ),
            SearchStrategyType.SEMANTIC_SEARCH: SearchStrategy(
                "Семантический поиск", 2, 0.9, "Векторный поиск по смыслу"
            ),
            SearchStrategyType.SYNONYM_EXPANSION: SearchStrategy(
                "Расширение синонимами", 3, 0.8, "Поиск с использованием синонимов"
            ),
            SearchStrategyType.CATEGORICAL_SEARCH: SearchStrategy(
                "Поиск по категориям", 4, 0.7, "Поиск в конкретных категориях продуктов"
            ),
            SearchStrategyType.HEALTH_CONDITION_SEARCH: SearchStrategy(
                "Поиск по здоровью", 5, 0.85, "Поиск по состояниям здоровья"
            ),
            SearchStrategyType.INGREDIENT_SEARCH: SearchStrategy(
                "Поиск по составу", 6, 0.75, "Поиск по ингредиентам и компонентам"
            ),
            SearchStrategyType.FUZZY_MATCH: SearchStrategy(
                "Нечеткое совпадение", 7, 0.6, "Поиск с опечатками и вариациями"
            ),
            SearchStrategyType.BRAND_SEARCH: SearchStrategy(
                "Поиск по брендам", 8, 0.65, "Поиск конкретных брендов и линеек"
            ),
            SearchStrategyType.COMPOSITIONAL_SEARCH: SearchStrategy(
                "Композиционный поиск", 9, 0.55, "Поиск комбинаций ингредиентов"
            ),
            SearchStrategyType.FALLBACK_BROAD: SearchStrategy(
                "Широкий поиск", 10, 0.3, "Максимально широкий поиск"
            )
        }
        
        # Базы знаний для поиска
        self.knowledge_bases = {}
        self.category_mappings = {}
        self.health_mappings = {}
        self.ingredient_mappings = {}
        self.synonym_mappings = {}
        
        self._load_knowledge_bases()
        self._build_search_mappings()
    
    def _load_knowledge_bases(self):
        """Загружает все доступные базы знаний"""
        knowledge_files = [
            "knowledge_base.json",
            "knowledge_base_new.json", 
            "knowledge_base_fixed.json"
        ]
        
        for kb_file in knowledge_files:
            try:
                with open(kb_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.knowledge_bases[kb_file] = data
                    print(f"✅ Загружена база знаний: {kb_file} ({len(data)} продуктов)")
            except Exception as e:
                print(f"⚠️ Не удалось загрузить {kb_file}: {e}")
    
    def _build_search_mappings(self):
        """Строит индексы для быстрого поиска"""
        print("🔍 Строим поисковые индексы...")
        
        # Объединяем все продукты
        all_products = []
        for kb_data in self.knowledge_bases.values():
            all_products.extend(kb_data)
        
        # Индекс по категориям
        category_keywords = {
            "иммунитет": ["иммун", "защит", "простуд", "грипп", "вирус", "бактери", "инфекц"],
            "печень": ["печен", "гепат", "детокс", "очищен", "токсин", "силицитин", "силимарин", "расторопш"],
            "сердце": ["сердц", "сосуд", "давлен", "холестер", "кровообращен"],
            "кожа": ["кож", "дермат", "сыпь", "акне", "экзем", "псориаз"],
            "пищеварение": ["пищевар", "желудок", "кишечник", "гастрит", "диарея"],
            "нервы": ["нерв", "стресс", "депресс", "тревог", "бессонниц", "успокоен"],
            "кости": ["кост", "сустав", "артрит", "остеопороз", "кальций"],
            "энергия": ["энерг", "усталост", "вялост", "тонус", "бодрост"],
            "витамины": ["витамин", "минерал", "микроэлемент", "авитаминоз"],
            "дыхание": ["дыхан", "легк", "бронх", "астм", "кашель"]
        }
        
        for category, keywords in category_keywords.items():
            self.category_mappings[category] = []
            for product in all_products:
                product_text = self._get_full_product_text(product).lower()
                if any(keyword in product_text for keyword in keywords):
                    self.category_mappings[category].append(product)
        
        # Индекс по состояниям здоровья
        health_conditions = {
            "бронхит": ["бронхит", "кашель", "мокрота", "дыхательн", "легочн"],
            "простуда": ["простуд", "ОРВИ", "насморк", "температур", "озноб"],
            "гастрит": ["гастрит", "желудок", "изжог", "боль в желудке"],
            "стресс": ["стресс", "нервозност", "тревожност", "переживан"],
            "бессонница": ["бессонниц", "сон", "засыпан", "пробужден"],
            "усталость": ["усталост", "вялост", "слабост", "упадок сил"],
            "головная боль": ["головн боль", "мигрен", "цефалги"],
            "аллергия": ["аллерг", "зуд", "высыпан", "крапивниц"],
            "диабет": ["диабет", "сахар", "глюкоз", "инсулин"],
            "гипертония": ["гипертони", "давлен", "гипертензи"],
            "болезни печени": ["печен", "гепат", "желт", "цирроз", "фиброз", "жировая дистрофия", "токсин", "детоксикац"]
        }
        
        for condition, keywords in health_conditions.items():
            self.health_mappings[condition] = []
            for product in all_products:
                product_text = self._get_full_product_text(product).lower()
                if any(keyword in product_text for keyword in keywords):
                    self.health_mappings[condition].append(product)
        
        # Индекс по ингредиентам
        ingredients = {
            "серебро": ["серебр", "аргент", "ag"],
            "магний": ["магний", "магниев", "mg"],
            "кальций": ["кальций", "кальциев", "ca"],
            "витамин с": ["витамин с", "аскорбин", "аскорбиновая кислота"],
            "витамин д": ["витамин д", "витамин d", "холекальциферол"],
            "омега-3": ["омега", "рыбий жир", "жирные кислоты"],
            "пробиотики": ["пробиотик", "лактобактер", "бифидобактер"],
            "антиоксиданты": ["антиоксидант", "флавоноид", "полифенол"],
            "женьшень": ["женьшень", "ginseng"],
            "эхинацея": ["эхинацея", "echinacea"]
        }
        
        for ingredient, keywords in ingredients.items():
            self.ingredient_mappings[ingredient] = []
            for product in all_products:
                product_text = self._get_full_product_text(product).lower()
                if any(keyword in product_text for keyword in keywords):
                    self.ingredient_mappings[ingredient].append(product)
        
        print(f"✅ Построены индексы:")
        print(f"   📂 Категории: {len(self.category_mappings)}")
        print(f"   🏥 Состояния здоровья: {len(self.health_mappings)}")
        print(f"   🧪 Ингредиенты: {len(self.ingredient_mappings)}")
    
    def _get_full_product_text(self, product: Dict) -> str:
        """Получает весь текст продукта для поиска"""
        text_parts = []
        
        # Основные поля
        for field in ["product", "description", "composition", "dosage", "contraindications"]:
            if field in product:
                if isinstance(product[field], list):
                    text_parts.extend(product[field])
                else:
                    text_parts.append(str(product[field]))
        
        # Польза
        if "benefits" in product:
            if isinstance(product["benefits"], list):
                text_parts.extend(product["benefits"])
            else:
                text_parts.append(str(product["benefits"]))
        
        return " ".join(text_parts)
    
    def enhanced_search(self, query: str, max_results: int = 10, 
                       min_confidence: float = 0.3) -> List[EnhancedSearchResult]:
        """
        Выполняет многоуровневый поиск с использованием ВСЕХ стратегий
        """
        print(f"🔍 Усиленный поиск: '{query}'")
        
        # Нормализуем запрос
        normalized_query = self._normalize_query(query)
        
        # Результаты от всех стратегий
        all_results = []
        strategies_used = []
        
        # Применяем стратегии в порядке приоритета
        for strategy_type, strategy in self.search_strategies.items():
            print(f"   🎯 Применяем стратегию: {strategy.name}")
            
            strategy_results = self._apply_strategy(strategy_type, normalized_query, query)
            
            if strategy_results:
                print(f"      ✅ Найдено {len(strategy_results)} результатов")
                strategies_used.append(strategy.name)
                
                # Применяем вес стратегии
                for result in strategy_results:
                    result.relevance_score *= strategy.weight
                    result.strategies_used.append(strategy.name)
                
                all_results.extend(strategy_results)
            else:
                print(f"      ❌ Результатов нет")
        
        # Убираем дубликаты и ранжируем
        unique_results = self._deduplicate_and_rank(all_results)
        
        # Фильтруем по минимальной уверенности
        filtered_results = [r for r in unique_results if r.confidence >= min_confidence]
        
        print(f"📊 Итого:")
        print(f"   🎯 Стратегий использовано: {len(strategies_used)}")
        print(f"   📋 Результатов найдено: {len(all_results)}")
        print(f"   ✨ После дедупликации: {len(unique_results)}")
        print(f"   🎪 После фильтрации: {len(filtered_results)}")
        
        return filtered_results[:max_results]
    
    def _normalize_query(self, query: str) -> str:
        """Нормализует запрос для поиска"""
        # Приводим к нижнему регистру
        normalized = query.lower()
        
        # Убираем пунктуацию кроме важной
        normalized = re.sub(r'[^\w\s\-]', ' ', normalized)
        
        # Убираем лишние пробелы
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _apply_strategy(self, strategy_type: SearchStrategyType, 
                       normalized_query: str, original_query: str) -> List[EnhancedSearchResult]:
        """Применяет конкретную стратегию поиска"""
        
        if strategy_type == SearchStrategyType.EXACT_MATCH:
            return self._exact_match_search(normalized_query, original_query)
        
        elif strategy_type == SearchStrategyType.SEMANTIC_SEARCH:
            return self._semantic_search(normalized_query, original_query)
        
        elif strategy_type == SearchStrategyType.SYNONYM_EXPANSION:
            return self._synonym_expansion_search(normalized_query, original_query)
        
        elif strategy_type == SearchStrategyType.CATEGORICAL_SEARCH:
            return self._categorical_search(normalized_query, original_query)
        
        elif strategy_type == SearchStrategyType.HEALTH_CONDITION_SEARCH:
            return self._health_condition_search(normalized_query, original_query)
        
        elif strategy_type == SearchStrategyType.INGREDIENT_SEARCH:
            return self._ingredient_search(normalized_query, original_query)
        
        elif strategy_type == SearchStrategyType.FUZZY_MATCH:
            return self._fuzzy_match_search(normalized_query, original_query)
        
        elif strategy_type == SearchStrategyType.BRAND_SEARCH:
            return self._brand_search(normalized_query, original_query)
        
        elif strategy_type == SearchStrategyType.COMPOSITIONAL_SEARCH:
            return self._compositional_search(normalized_query, original_query)
        
        elif strategy_type == SearchStrategyType.FALLBACK_BROAD:
            return self._fallback_broad_search(normalized_query, original_query)
        
        return []
    
    def _exact_match_search(self, query: str, original: str) -> List[EnhancedSearchResult]:
        """Поиск точных совпадений"""
        results = []
        
        for kb_name, products in self.knowledge_bases.items():
            for product in products:
                product_text = self._get_full_product_text(product).lower()
                
                # Точное совпадение фразы
                if query in product_text:
                    score = 1.0
                    
                    # Бонус если совпадение в названии
                    if query in product.get("product", "").lower():
                        score = 1.2
                    
                    results.append(EnhancedSearchResult(
                        content=product_text[:500],
                        product=product.get("product", ""),
                        chunk_type="exact_match",
                        relevance_score=score,
                        confidence=0.95,
                        source=kb_name,
                        metadata={"match_type": "exact", "query": query}
                    ))
        
        return results
    
    def _semantic_search(self, query: str, original: str) -> List[EnhancedSearchResult]:
        """Семантический поиск через векторную БД"""
        if not self.vector_db:
            return []
        
        try:
            # Используем vector_db для семантического поиска
            vector_results = self.vector_db.search(original, limit=5)
            
            results = []
            for vr in vector_results:
                results.append(EnhancedSearchResult(
                    content=vr.chunk.text,
                    product=vr.chunk.product,
                    chunk_type=vr.chunk.chunk_type,
                    relevance_score=vr.score,
                    confidence=min(vr.score, 0.9),
                    source=vr.source,
                    metadata={"search_type": "semantic"}
                ))
            
            return results
        except Exception as e:
            print(f"⚠️ Ошибка семантического поиска: {e}")
            return []
    
    def _categorical_search(self, query: str, original: str) -> List[EnhancedSearchResult]:
        """Поиск по категориям"""
        results = []
        
        for category, products in self.category_mappings.items():
            if category in query or any(keyword in query for keyword in category.split()):
                for product in products:
                    results.append(EnhancedSearchResult(
                        content=self._get_full_product_text(product)[:500],
                        product=product.get("product", ""),
                        chunk_type="category_match",
                        relevance_score=0.8,
                        confidence=0.7,
                        source="category_index",
                        metadata={"category": category, "match_type": "categorical"}
                    ))
        
        return results
    
    def _health_condition_search(self, query: str, original: str) -> List[EnhancedSearchResult]:
        """Поиск по состояниям здоровья"""
        results = []
        
        for condition, products in self.health_mappings.items():
            condition_keywords = condition.split()
            if any(keyword in query for keyword in condition_keywords):
                for product in products:
                    results.append(EnhancedSearchResult(
                        content=self._get_full_product_text(product)[:500],
                        product=product.get("product", ""),
                        chunk_type="health_condition",
                        relevance_score=0.85,
                        confidence=0.8,
                        source="health_index",
                        metadata={"condition": condition, "match_type": "health"}
                    ))
        
        return results
    
    def _ingredient_search(self, query: str, original: str) -> List[EnhancedSearchResult]:
        """Поиск по ингредиентам"""
        results = []
        
        for ingredient, products in self.ingredient_mappings.items():
            ingredient_keywords = ingredient.split()
            if any(keyword in query for keyword in ingredient_keywords):
                for product in products:
                    results.append(EnhancedSearchResult(
                        content=self._get_full_product_text(product)[:500],
                        product=product.get("product", ""),
                        chunk_type="ingredient_match",
                        relevance_score=0.75,
                        confidence=0.75,
                        source="ingredient_index",
                        metadata={"ingredient": ingredient, "match_type": "ingredient"}
                    ))
        
        return results
    
    def _synonym_expansion_search(self, query: str, original: str) -> List[EnhancedSearchResult]:
        """Поиск с расширением синонимами"""
        
        # Простой словарь синонимов для базового расширения
        synonyms_map = {
            'магний': ['mg', 'магниевый'],
            'кальций': ['calcium', 'кальциевый'],
            'витамин': ['vitamin', 'вит'],
            'печень': ['гепато', 'liver', 'печеночный'],
            'иммунитет': ['immunity', 'иммунный', 'защита'],
            'стресс': ['stress', 'нервы', 'напряжение'],
            'сон': ['sleep', 'бессонница', 'расслабление']
        }
        
        try:
            expanded_terms = []
            words = original.lower().split()
            
            for word in words:
                expanded_terms.append(word)
                if word in synonyms_map:
                    expanded_terms.extend(synonyms_map[word])
            
            # Создаем расширенный запрос
            expanded_query = ' '.join(expanded_terms)
            
            if expanded_query != original:
                # Ищем по расширенному запросу
                return self._exact_match_search(expanded_query.lower(), expanded_query)
        except Exception as e:
            print(f"⚠️ Ошибка расширения синонимами: {e}")
        
        return []
    
    def _fuzzy_match_search(self, query: str, original: str) -> List[EnhancedSearchResult]:
        """Нечеткий поиск с учетом опечаток"""
        results = []
        query_words = query.split()
        
        for kb_name, products in self.knowledge_bases.items():
            for product in products:
                product_text = self._get_full_product_text(product).lower()
                product_words = product_text.split()
                
                # Ищем похожие слова
                max_similarity = 0
                for query_word in query_words:
                    for product_word in product_words:
                        if len(query_word) > 3 and len(product_word) > 3:
                            similarity = SequenceMatcher(None, query_word, product_word).ratio()
                            if similarity > max_similarity:
                                max_similarity = similarity
                
                # Если есть достаточно похожие слова
                if max_similarity > 0.8:
                    results.append(EnhancedSearchResult(
                        content=product_text[:500],
                        product=product.get("product", ""),
                        chunk_type="fuzzy_match",
                        relevance_score=max_similarity * 0.6,
                        confidence=max_similarity * 0.7,
                        source=kb_name,
                        metadata={"similarity": max_similarity, "match_type": "fuzzy"}
                    ))
        
        return results
    
    def _brand_search(self, query: str, original: str) -> List[EnhancedSearchResult]:
        """Поиск по брендам и линейкам"""
        brand_keywords = [
            "аврора", "aurora", "барс", "bars", "mg", "витамин", "солберри", 
            "аргент", "битерон", "гепосин", "симбион", "еломил"
        ]
        
        results = []
        for keyword in brand_keywords:
            if keyword in query:
                results.extend(self._exact_match_search(keyword, keyword))
        
        return results
    
    def _compositional_search(self, query: str, original: str) -> List[EnhancedSearchResult]:
        """Поиск комбинаций ингредиентов"""
        results = []
        
        # Ищем упоминания нескольких ингредиентов
        mentioned_ingredients = []
        for ingredient in self.ingredient_mappings.keys():
            if ingredient in query:
                mentioned_ingredients.append(ingredient)
        
        if len(mentioned_ingredients) >= 2:
            # Ищем продукты содержащие несколько ингредиентов
            for kb_name, products in self.knowledge_bases.items():
                for product in products:
                    product_text = self._get_full_product_text(product).lower()
                    
                    contained_ingredients = 0
                    for ingredient in mentioned_ingredients:
                        if ingredient in product_text:
                            contained_ingredients += 1
                    
                    if contained_ingredients >= 2:
                        score = contained_ingredients / len(mentioned_ingredients)
                        results.append(EnhancedSearchResult(
                            content=product_text[:500],
                            product=product.get("product", ""),
                            chunk_type="compositional",
                            relevance_score=score * 0.55,
                            confidence=score * 0.6,
                            source=kb_name,
                            metadata={
                                "ingredients_found": contained_ingredients,
                                "ingredients_total": len(mentioned_ingredients),
                                "match_type": "compositional"
                            }
                        ))
        
        return results
    
    def _fallback_broad_search(self, query: str, original: str) -> List[EnhancedSearchResult]:
        """Максимально широкий поиск как последняя надежда"""
        results = []
        query_words = [word for word in query.split() if len(word) > 2]
        
        if not query_words:
            return results
        
        for kb_name, products in self.knowledge_bases.items():
            for product in products:
                product_text = self._get_full_product_text(product).lower()
                
                # Считаем сколько слов из запроса есть в продукте
                word_matches = 0
                for word in query_words:
                    if word in product_text:
                        word_matches += 1
                
                # Если есть хотя бы одно совпадение
                if word_matches > 0:
                    score = word_matches / len(query_words)
                    results.append(EnhancedSearchResult(
                        content=product_text[:500],
                        product=product.get("product", ""),
                        chunk_type="broad_fallback",
                        relevance_score=score * 0.3,
                        confidence=score * 0.4,
                        source=kb_name,
                        metadata={
                            "word_matches": word_matches,
                            "total_words": len(query_words),
                            "match_type": "broad"
                        }
                    ))
        
        return results
    
    def _deduplicate_and_rank(self, results: List[EnhancedSearchResult]) -> List[EnhancedSearchResult]:
        """Убирает дубликаты и ранжирует результаты"""
        # Приоритеты продуктов для иммунитета (стабильное ранжирование)
        immunity_priorities = {
            # ПРЯМОЕ назначение для иммунитета
            'Аргент-Макс': 100,
            'Аргент Макс': 100,
            'Кошачий Коготь': 95,
            'Ин-Аурин': 90,
            'БАРС-2': 85,
            'Витамин С': 80,
            'Оранж Дей': 75,  # Витамин С в удобной форме
            
            # КОСВЕННОЕ влияние на иммунитет (общеукрепляющие)
            'Солберри-H': 60,      # Антиоксидант, косвенно поддерживает
            'Битерон-H': 55,       # Антиоксидант, косвенно поддерживает
            'Витамины группы В': 45,  # Поддержка нервной системы, косвенно
            'Омега-3': 40,            # Противовоспалительное, косвенно
            'Румарин Экстра': 30      # Регенерация, очень косвенно
        }
        
        # Группируем по продуктам
        product_groups = defaultdict(list)
        for result in results:
            product_groups[result.product].append(result)
        
        # Выбираем лучший результат для каждого продукта
        unique_results = []
        for product, group in product_groups.items():
            # Сортируем по relevance_score
            group.sort(key=lambda x: x.relevance_score, reverse=True)
            best_result = group[0]
            
            # Применяем приоритет для иммунитета
            if any(keyword in result.metadata.get('category', '') or 
                   keyword in result.content.lower() 
                   for keyword in ['иммун', 'immunity', 'защит'] 
                   for result in group):
                priority_score = immunity_priorities.get(product, 50)
                best_result.relevance_score = max(best_result.relevance_score, priority_score / 100.0)
            
            # Объединяем стратегии
            all_strategies = set()
            total_confidence = 0
            for result in group:
                all_strategies.update(result.strategies_used)
                total_confidence += result.confidence
            
            best_result.strategies_used = list(all_strategies)
            best_result.confidence = min(total_confidence / len(group), 1.0)
            
            unique_results.append(best_result)
        
        # Детерминированная сортировка: сначала по score, потом по алфавиту для стабильности
        unique_results.sort(key=lambda x: (-x.relevance_score, -x.confidence, x.product))
        
        return unique_results

# Создаем глобальный экземпляр
enhanced_search_engine = None

def initialize_enhanced_search(vector_db=None, nlp_processor=None):
    """Инициализирует усиленную систему поиска"""
    global enhanced_search_engine
    enhanced_search_engine = EnhancedSearchEngine(vector_db, nlp_processor)
    return enhanced_search_engine
