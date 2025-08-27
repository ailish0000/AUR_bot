#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
from metadata_structure import ProductCategory, ProductForm, HealthIndication, TargetGroup

@dataclass
class SearchFilter:
    """Фильтр для поиска продуктов"""
    categories: Optional[List[str]] = None
    forms: Optional[List[str]] = None
    indications: Optional[List[str]] = None
    properties: Optional[List[str]] = None
    components: Optional[List[str]] = None
    exclude_properties: Optional[List[str]] = None  # исключить свойства
    exclude_contraindications: Optional[List[str]] = None  # исключить противопоказания
    target_groups: Optional[List[str]] = None

@dataclass
class SearchResult:
    """Результат поиска продукта"""
    product_name: str
    category: str
    form: str
    properties: List[str]
    indications: List[str]
    components: List[str]
    score: float  # релевантность
    original_data: Dict  # оригинальные данные продукта

class SmartSearchEngine:
    """Умный поисковый движок с фильтрами по метаданным"""
    
    def __init__(self, metadata_file: str = 'products_metadata.json'):
        """Инициализация с загрузкой метаданных"""
        self.metadata_file = metadata_file
        self.products = []
        self.load_metadata()
        
        # Синонимы для улучшения поиска
        self.synonyms = {
            "омега": ["омега-3", "омега 3", "рыбий жир", "omega", "omega-3", "omega 3"],
            "витамин с": ["витамин c", "аскорбиновая кислота", "аскорбинка", "витамин c", "vitamin c"],
            "кальций": ["кальций", "calcium", "костная ткань", "кости", "переломы"],
            "магний": ["магний", "magnesium", "mg", "нервная система", "стресс", "мышцы", "сон"],
            "пробиотик": ["пробиотик", "пробиотики", "микрофлора", "бифидо", "лакто", "кишечник"],
            "иммунитет": ["иммунитет", "иммунная система", "защита", "простуда", "грипп"],
            "детокс": ["детокс", "детоксикация", "очищение", "печень", "токсины"],
            "антипаразитарный": ["антипаразитарный", "паразиты", "глисты", "гельминты", "очищение от паразитов"]
        }
    
    def load_metadata(self):
        """Загружает метаданные продуктов"""
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self.products = json.load(f)
            print(f"✅ Загружено {len(self.products)} продуктов с метаданными")
        except Exception as e:
            print(f"❌ Ошибка загрузки метаданных: {e}")
            self.products = []
    
    def search(self, query: str, filters: Optional[SearchFilter] = None) -> List[SearchResult]:
        """Основной метод поиска"""
        
        print(f"🔍 Поиск: '{query}'")
        if filters:
            print(f"🎯 Фильтры: {self._describe_filters(filters)}")
        
        # 1. Текстовый поиск
        text_results = self._text_search(query)
        
        # 2. Применение фильтров
        if filters:
            filtered_results = self._apply_filters(text_results, filters)
        else:
            filtered_results = text_results
        
        # 3. Сортировка по релевантности
        sorted_results = sorted(filtered_results, key=lambda x: x.score, reverse=True)
        
        print(f"📊 Найдено: {len(sorted_results)} продуктов")
        
        return sorted_results[:20]  # ТОП-20 результатов
    
    def _text_search(self, query: str) -> List[SearchResult]:
        """Текстовый поиск с учетом синонимов"""
        
        query_lower = query.lower()
        search_terms = self._expand_query(query_lower)
        
        results = []
        
        for product in self.products:
            score = self._calculate_text_score(product, search_terms)
            
            if score > 0:
                result = SearchResult(
                    product_name=product['product_name'],
                    category=product['category'],
                    form=product['form'],
                    properties=product['properties'],
                    indications=product['health_indications'],
                    components=product['main_components'],
                    score=score,
                    original_data=product
                )
                results.append(result)
        
        return results
    
    def _expand_query(self, query: str) -> str:
        """Расширяет запрос синонимами"""
        expanded_terms = [query.lower()]
        
        # Добавляем синонимы
        for main_term, synonyms in self.synonyms.items():
            if any(syn in query.lower() for syn in [main_term] + synonyms):
                expanded_terms.extend(synonyms)
        
        # Специальные случаи
        if any(word in query.lower() for word in ["витамин", "витамины", "аскорбин"]):
            expanded_terms.append("витамин с")
        
        if any(word in query.lower() for word in ["кальций", "кости", "перелом", "костная"]):
            expanded_terms.append("кальций")
        
        if any(word in query.lower() for word in ["магний", "mg", "нервная", "стресс", "мышцы", "сон"]):
            expanded_terms.append("магний")
        
        if any(word in query.lower() for word in ["омега", "рыбий жир", "omega"]):
            expanded_terms.append("омега")
        
        return " ".join(set(expanded_terms))
    
    def _calculate_text_score(self, product: Dict, search_terms: List[str]) -> float:
        """Вычисляет релевантность продукта для текстового поиска"""
        
        score = 0.0
        
        # Создаем текст для поиска
        searchable_text = ' '.join([
            product['product_name'].lower(),
            product['category'].lower(),
            ' '.join(product['health_indications']),
            ' '.join(product['properties']),
            ' '.join(product['main_components']).lower()
        ])
        
        # Веса для разных полей
        weights = {
            'product_name': 50.0,  # Значительно увеличиваем вес названия продукта
            'category': 2.5,
            'indications': 2.5,
            'properties': 2.5,
            'components': 1.5
        }
        
        for term in search_terms:
            # Точное совпадение в названии (высший приоритет)
            if term in product['product_name'].lower():
                score += weights['product_name']
                # Дополнительный бонус за точное совпадение
                if term == product['product_name'].lower():
                    score += 50000.0  # Огромный бонус за точное совпадение
                # Бонус за совпадение ключевого слова в названии
                elif term in ["магний", "кальций", "витамин", "омега"] and term in product['product_name'].lower():
                    score += 40000.0  # Очень большой бонус за ключевое слово
            
            # Бонус за основной компонент в составе
            if term in ["магний", "кальций", "витамин", "омега"]:
                # Проверяем компоненты на наличие основного ингредиента
                components_text = ' '.join(product['main_components']).lower()
                if term in components_text:
                    # Определяем, является ли это основным компонентом
                    if term == "магний" and any("магний" in comp for comp in product['main_components']):
                        score += 60000.0  # Очень большой бонус за основной компонент
                    elif term == "кальций" and any("кальций" in comp for comp in product['main_components']):
                        score += 60000.0
                    elif term == "витамин" and any("витамин" in comp for comp in product['main_components']):
                        score += 60000.0
                    elif term == "омега" and any("омега" in comp for comp in product['main_components']):
                        score += 60000.0
            
            # Совпадение в категории
            if term in product['category'].lower():
                score += weights['category']
            
            # Совпадение в показаниях
            for indication in product['health_indications']:
                if term in indication.lower():
                    score += weights['indications']
                    # Дополнительный бонус за ключевые показания
                    if term in ["магний", "кальций", "витамин", "омега"] and term in indication.lower():
                        score += 10000.0  # Бонус за показания с ключевыми компонентами
            
            # Совпадение в свойствах
            for prop in product['properties']:
                if term in prop.lower():
                    score += weights['properties']
            
            # Совпадение в компонентах
            for component in product['main_components']:
                if term in component.lower():
                    score += weights['components']
        
        # Бонус за множественные совпадения
        term_matches = sum(1 for term in search_terms if term in searchable_text)
        if term_matches > 1:
            score *= (1 + (term_matches - 1) * 0.2)
        
        # Дополнительный бонус для специфических категорий
        category_bonuses = {
            'витамин с': ['Витамин С'],
            'кальций': ['Кальций'],
            'витамин д': ['Витамин Д'],
            'магний': ['Магний'],
            'омега': ['Омега'],
            'печень': ['Гепатопротекторы'],
            'иммунитет': ['Иммуномодуляторы']
        }
        
        for search_term in search_terms:
            if search_term in category_bonuses:
                target_categories = category_bonuses[search_term]
                if product['category'] in target_categories:
                    score += 5.0  # Большой бонус за точное соответствие категории
        
        return score
    
    def _apply_filters(self, results: List[SearchResult], filters: SearchFilter) -> List[SearchResult]:
        """Применяет фильтры к результатам поиска"""
        
        filtered = []
        
        for result in results:
            if self._matches_filters(result, filters):
                filtered.append(result)
        
        return filtered
    
    def _matches_filters(self, result: SearchResult, filters: SearchFilter) -> bool:
        """Проверяет соответствие продукта фильтрам"""
        
        # Фильтр по категориям (гибкая логика)
        if filters.categories:
            category_match = False
            for filter_category in filters.categories:
                # Точное совпадение
                if result.category == filter_category:
                    category_match = True
                    break
                # Иерархическое совпадение
                if self._is_category_match(result.category, filter_category):
                    category_match = True
                    break
            if not category_match:
                return False
        
        # Фильтр по формам выпуска
        if filters.forms:
            if result.form not in filters.forms:
                return False
        
        # Фильтр по показаниям (хотя бы одно должно совпадать)
        if filters.indications:
            if not any(ind in result.indications for ind in filters.indications):
                return False
        
        # Фильтр по свойствам (хотя бы одно должно совпадать)
        if filters.properties:
            if not any(prop in result.properties for prop in filters.properties):
                return False
        
        # Фильтр по компонентам
        if filters.components:
            has_component = False
            for filter_comp in filters.components:
                for result_comp in result.components:
                    if filter_comp.lower() in result_comp.lower():
                        has_component = True
                        break
                if has_component:
                    break
            if not has_component:
                return False
        
        # Исключение свойств
        if filters.exclude_properties:
            if any(prop in result.properties for prop in filters.exclude_properties):
                return False
        
        # Исключение по противопоказаниям
        if filters.exclude_contraindications:
            product_contras = result.original_data.get('contraindications', [])
            for exclude_contra in filters.exclude_contraindications:
                if any(exclude_contra.lower() in contra.lower() for contra in product_contras):
                    return False
        
        return True
    
    def _is_category_match(self, product_category: str, filter_category: str) -> bool:
        """Проверяет соответствие категорий с учетом иерархии"""
        
        # Маппинг категорий для гибкого поиска
        category_mapping = {
            "Витамины, минералы и микроэлементы": [
                "Витамин С", "Витамин Д", "Витамин Е", "Витамин А", "Витамин В",
                "Кальций", "Магний", "Железо", "Цинк", "Селен", "Омега"
            ],
            "Гепатопротекторы": ["Печень", "Детокс", "Очищение"],
            "Антиоксиданты": ["Антиоксидант", "Свободные радикалы"],
            "Иммуномодуляторы": ["Иммунитет", "Защита"],
            "Сорбенты и детокс": ["Сорбент", "Детокс", "Очищение"],
            "Травы и экстракты": ["Травы", "Экстракт", "Растительный"],
            "Все продукты": []  # Все категории
        }
        
        # Проверяем, входит ли продукт в категорию фильтра
        if filter_category in category_mapping:
            if product_category in category_mapping[filter_category]:
                return True
        
        # Проверяем обратное - входит ли фильтр в категорию продукта
        for main_category, sub_categories in category_mapping.items():
            if product_category == main_category and filter_category in sub_categories:
                return True
        
        # Проверяем частичные совпадения
        if filter_category.lower() in product_category.lower() or product_category.lower() in filter_category.lower():
            return True
        
        return False
    
    def _describe_filters(self, filters: SearchFilter) -> str:
        """Описывает примененные фильтры"""
        descriptions = []
        
        if filters.categories:
            descriptions.append(f"категории: {', '.join(filters.categories)}")
        if filters.forms:
            descriptions.append(f"формы: {', '.join(filters.forms)}")
        if filters.indications:
            descriptions.append(f"показания: {', '.join(filters.indications)}")
        if filters.properties:
            descriptions.append(f"свойства: {', '.join(filters.properties)}")
        if filters.exclude_properties:
            descriptions.append(f"исключить: {', '.join(filters.exclude_properties)}")
        
        return '; '.join(descriptions) if descriptions else 'нет'
    
    def suggest_products(self, problem: str, exclude_types: List[str] = None) -> List[SearchResult]:
        """Предлагает продукты для конкретной проблемы"""
        
        # Определяем фильтры на основе проблемы
        filters = self._build_filters_for_problem(problem, exclude_types)
        
        return self.search(problem, filters)
    
    def _build_filters_for_problem(self, problem: str, exclude_types: List[str] = None) -> SearchFilter:
        """Строит фильтры для конкретной проблемы"""
        
        problem_lower = problem.lower()
        
        # Определяем показания
        indications = []
        if any(word in problem_lower for word in ['печень', 'гепато', 'детокс']):
            indications.append('печень')
        if any(word in problem_lower for word in ['простуда', 'орви', 'грипп']):
            indications.append('простуда')
        if any(word in problem_lower for word in ['иммунитет', 'защита']):
            indications.append('иммунитет')
        if any(word in problem_lower for word in ['суставы', 'артрит']):
            indications.append('суставы')
        
        # Исключения
        exclude_props = exclude_types if exclude_types else []
        
        return SearchFilter(
            indications=indications if indications else None,
            exclude_properties=exclude_props if exclude_props else None
        )

def test_smart_search():
    """Тестирует умный поиск"""
    
    print("🧪 ТЕСТИРОВАНИЕ УМНОГО ПОИСКА")
    print("="*60)
    
    search_engine = SmartSearchEngine()
    
    # Тест 1: Простой текстовый поиск
    print(f"\n🔍 ТЕСТ 1: Поиск 'витамин С'")
    results = search_engine.search("витамин С")
    for i, result in enumerate(results[:5], 1):
        print(f"   {i}. {result.product_name} ({result.category}) - Score: {result.score:.2f}")
    
    # Тест 2: Поиск с фильтрами
    print(f"\n🔍 ТЕСТ 2: Поиск гепатопротекторов")
    filters = SearchFilter(categories=['Гепатопротекторы'])
    results = search_engine.search("печень", filters)
    for i, result in enumerate(results[:5], 1):
        print(f"   {i}. {result.product_name} - Свойства: {', '.join(result.properties)}")
    
    # Тест 3: Исключение антипаразитарных для печени
    print(f"\n🔍 ТЕСТ 3: Для печени БЕЗ антипаразитарных")
    filters = SearchFilter(
        indications=['печень'],
        exclude_properties=['антипаразитарный']
    )
    results = search_engine.search("для печени", filters)
    for i, result in enumerate(results[:5], 1):
        print(f"   {i}. {result.product_name} ({result.category})")
    
    # Тест 4: Только таблетки с магнием
    print(f"\n🔍 ТЕСТ 4: Таблетки с магнием")
    filters = SearchFilter(
        forms=['таблетки'],
        components=['магний']
    )
    results = search_engine.search("магний", filters)
    for i, result in enumerate(results[:5], 1):
        print(f"   {i}. {result.product_name} - Форма: {result.form}")
    
    # Тест 5: Умные рекомендации
    print(f"\n🔍 ТЕСТ 5: Умные рекомендации при простуде")
    results = search_engine.suggest_products("простуда")
    for i, result in enumerate(results[:5], 1):
        print(f"   {i}. {result.product_name} - Показания: {', '.join(result.indications)}")

if __name__ == "__main__":
    test_smart_search()

