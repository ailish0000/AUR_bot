#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from smart_search_engine import SearchFilter

@dataclass
class ParsedQuery:
    """Распознанный запрос пользователя"""
    base_query: str  # основной запрос
    filters: SearchFilter  # извлеченные фильтры
    intent: str  # тип запроса
    confidence: float  # уверенность в распознавании

class SmartNLPParser:
    """Умный парсер для понимания естественных запросов с фильтрами"""
    
    def __init__(self):
        # Словари для распознавания
        self.category_patterns = {
            'Гепатопротекторы': [
                r'гепатопротектор', r'для печени', r'печеночн', r'гепато'
            ],
            'Витамин С': [
                r'витамин\s*с', r'vitamin\s*c', r'аскорбин', r'оранж'
            ],
            'Витамины, минералы и микроэлементы': [
                r'витамин', r'минерал', r'микроэлемент', r'авитаминоз',
                r'витамин\s*[а-я]', r'витамин\s*[a-z]', r'витамин\s*д',
                r'витамин\s*b', r'витамин\s*в',
                r'магний', r'кальций', r'железо', r'цинк', r'селен'
            ],
            'Сорбенты и детокс': [
                r'сорбент', r'детокс', r'очищение', r'токсины', r'шлаки'
            ],
            'Пробиотики': [
                r'пробиотик', r'бифидо', r'лакто', r'микрофлора'
            ],
            'Антипаразитарные': [
                r'антипаразитарн', r'паразиты', r'глисты', r'гельминты'
            ]
        }
        
        self.form_patterns = {
            'капсулы': [r'капсул', r'капс'],
            'таблетки': [r'таблетк', r'табс', r'пилюл'],
            'жидкий': [r'жидк', r'сок', r'концентрат', r'раствор'],
            'порошок': [r'порошок', r'саше', r'сухая смесь'],
            'крем': [r'крем', r'мазь', r'гель']
        }
        
        self.indication_patterns = {
            'печень': [
                r'печень', r'печени', r'гепато', r'желчь', r'детоксикация'
            ],
            'иммунитет': [
                r'иммунитет', r'защитные силы', r'сопротивляемость', 
                r'иммунн', r'защита организма'
            ],
            'простуда': [
                r'простуда', r'орви', r'грипп', r'кашель', r'насморк',
                r'температура', r'вирус'
            ],
            'суставы': [
                r'суставы', r'суставов', r'артрит', r'артроз', r'хрящи',
                r'связки', r'подвижность'
            ],
            'пищеварение': [
                r'пищеварение', r'жкт', r'желудок', r'кишечник', r'переваривание'
            ]
        }
        
        self.property_patterns = {
            'сорбент': [r'сорбент', r'адсорбент', r'поглощает', r'выводит'],
            'гепатопротектор': [r'гепатопротектор', r'защита печени'],
            'антиоксидант': [r'антиоксидант', r'свободные радикалы'],
            'противовоспалительный': [r'противовоспалительн', r'воспаление'],
            'антипаразитарный': [r'антипаразитарн', r'от паразитов']
        }
        
        # Паттерны для исключений
        self.exclusion_patterns = [
            r'без\s+(\w+)',
            r'не\s+(\w+)',
            r'исключ\w*\s+(\w+)',
            r'кроме\s+(\w+)',
            r'только\s+не\s+(\w+)'
        ]
        
        # Паттерны для ограничений
        self.limitation_patterns = [
            r'только\s+(\w+)',
            r'исключительно\s+(\w+)',
            r'лишь\s+(\w+)'
        ]
        
        # Паттерны для компонентов
        self.component_patterns = [
            r'с\s+(\w+)',
            r'содержащ\w*\s+(\w+)',
            r'в\s+составе\s+(\w+)',
            r'на\s+основе\s+(\w+)'
        ]
        
        # Паттерны для целевых групп
        self.target_group_patterns = {
            'беременные': [r'беременн', r'для беременных'],
            'дети': [r'детск', r'для детей', r'ребенк'],
            'пожилые': [r'пожил', r'старш', r'возрастн'],
            'спортсмены': [r'спортсмен', r'атлет', r'фитнес']
        }
    
    def parse_query(self, query: str) -> ParsedQuery:
        """Основной метод парсинга запроса"""
        
        query_lower = query.lower().strip()
        
        # Извлекаем фильтры
        filters = self._extract_filters(query_lower)
        
        # Определяем базовый запрос (убираем распознанные фильтры)
        base_query = self._extract_base_query(query_lower, filters)
        
        # Определяем тип запроса
        intent = self._determine_intent(query_lower, filters)
        
        # Вычисляем уверенность
        confidence = self._calculate_confidence(query_lower, filters)
        
        return ParsedQuery(
            base_query=base_query,
            filters=filters,
            intent=intent,
            confidence=confidence
        )
    
    def _extract_filters(self, query: str) -> SearchFilter:
        """Извлекает фильтры из запроса"""
        
        # Инициализируем фильтры
        categories = []
        forms = []
        indications = []
        properties = []
        components = []
        exclude_properties = []
        exclude_contraindications = []
        target_groups = []
        
        # Извлекаем категории
        for category, patterns in self.category_patterns.items():
            if any(re.search(pattern, query) for pattern in patterns):
                categories.append(category)
        
        # Извлекаем формы выпуска
        for form, patterns in self.form_patterns.items():
            if any(re.search(pattern, query) for pattern in patterns):
                forms.append(form)
        
        # Извлекаем показания
        for indication, patterns in self.indication_patterns.items():
            if any(re.search(pattern, query) for pattern in patterns):
                indications.append(indication)
        
        # Извлекаем свойства
        for prop, patterns in self.property_patterns.items():
            if any(re.search(pattern, query) for pattern in patterns):
                properties.append(prop)
        
        # Извлекаем компоненты
        for pattern in self.component_patterns:
            matches = re.findall(pattern, query)
            components.extend(matches)
        
        # Извлекаем исключения
        for pattern in self.exclusion_patterns:
            matches = re.findall(pattern, query)
            for match in matches:
                # Определяем тип исключения
                if self._is_property(match):
                    exclude_properties.append(match)
                elif self._is_contraindication(match):
                    exclude_contraindications.append(match)
        
        # Извлекаем целевые группы
        for group, patterns in self.target_group_patterns.items():
            if any(re.search(pattern, query) for pattern in patterns):
                target_groups.append(group)
        
        # Специальная логика для медицинской безопасности
        if any(word in query for word in ['беременн', 'кормящ', 'лактац']):
            exclude_contraindications.extend(['беременность', 'лактация'])
        
        if any(word in query for word in ['детск', 'ребенк']) and 'до' in query:
            exclude_contraindications.append('дети')
        
        return SearchFilter(
            categories=categories if categories else None,
            forms=forms if forms else None,
            indications=indications if indications else None,
            properties=properties if properties else None,
            components=components if components else None,
            exclude_properties=exclude_properties if exclude_properties else None,
            exclude_contraindications=exclude_contraindications if exclude_contraindications else None,
            target_groups=target_groups if target_groups else None
        )
    
    def _is_property(self, word: str) -> bool:
        """Проверяет является ли слово свойством продукта"""
        return any(word.lower() in pattern for patterns in self.property_patterns.values() 
                  for pattern in patterns)
    
    def _is_contraindication(self, word: str) -> bool:
        """Проверяет является ли слово противопоказанием"""
        contraindication_words = [
            'беременн', 'лактац', 'детск', 'аллерг', 'диабет', 'гипертони'
        ]
        return any(contra in word.lower() for contra in contraindication_words)
    
    def _extract_base_query(self, query: str, filters: SearchFilter) -> str:
        """Извлекает базовый запрос, убирая распознанные фильтры"""
        
        base = query
        
        # Убираем распознанные паттерны
        remove_patterns = [
            r'только\s+\w+',
            r'без\s+\w+',
            r'не\s+\w+',
            r'в\s+капсулах',
            r'в\s+таблетках',
            r'жидк\w*\s*форм\w*',
            r'для\s+беременных',
            r'детск\w*'
        ]
        
        for pattern in remove_patterns:
            base = re.sub(pattern, '', base).strip()
        
        # Убираем лишние пробелы
        base = re.sub(r'\s+', ' ', base).strip()
        
        return base if base else query
    
    def _determine_intent(self, query: str, filters: SearchFilter) -> str:
        """Определяет тип запроса"""
        
        if filters.categories and len(filters.categories) == 1:
            return 'category_search'
        elif filters.indications:
            return 'problem_solving'
        elif filters.forms and not filters.indications:
            return 'form_preference'
        elif filters.exclude_properties:
            return 'safe_selection'
        else:
            return 'general_search'
    
    def _calculate_confidence(self, query: str, filters: SearchFilter) -> float:
        """Вычисляет уверенность в распознавании"""
        
        confidence = 0.5  # базовая уверенность
        
        # Повышаем уверенность за каждый найденный фильтр
        if filters.categories:
            confidence += 0.15 * len(filters.categories)
        if filters.indications:
            confidence += 0.20 * len(filters.indications)
        if filters.properties:
            confidence += 0.10 * len(filters.properties)
        if filters.forms:
            confidence += 0.10 * len(filters.forms)
        if filters.exclude_properties:
            confidence += 0.20  # высокая ценность исключений
        
        return min(confidence, 1.0)

def test_smart_nlp():
    """Тестирует умный NLP парсер"""
    
    print("🧠 ТЕСТИРОВАНИЕ УМНОГО NLP ПАРСЕРА")
    print("="*60)
    
    parser = SmartNLPParser()
    
    test_queries = [
        "Что есть для печени без антипаразитарных?",
        "Покажи все гепатопротекторы в капсулах",
        "Витамины с магнием только в таблетках",
        "Сорбенты для детоксикации",
        "Что можно беременным от простуды?",
        "Пробиотики для кишечника",
        "Антиоксиданты без противопоказаний",
        "Жидкие витамины группы В",
        "Для суставов не антипаразитарные",
        "Капсулы с лецитином для печени"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 ТЕСТ {i}: '{query}'")
        print("-" * 40)
        
        parsed = parser.parse_query(query)
        
        print(f"   Базовый запрос: '{parsed.base_query}'")
        print(f"   Тип запроса: {parsed.intent}")
        print(f"   Уверенность: {parsed.confidence:.2f}")
        
        filters = parsed.filters
        print(f"   Фильтры:")
        
        if filters.categories:
            print(f"     Категории: {', '.join(filters.categories)}")
        if filters.forms:
            print(f"     Формы: {', '.join(filters.forms)}")
        if filters.indications:
            print(f"     Показания: {', '.join(filters.indications)}")
        if filters.properties:
            print(f"     Свойства: {', '.join(filters.properties)}")
        if filters.components:
            print(f"     Компоненты: {', '.join(filters.components)}")
        if filters.exclude_properties:
            print(f"     Исключить свойства: {', '.join(filters.exclude_properties)}")
        if filters.exclude_contraindications:
            print(f"     Исключить противопоказания: {', '.join(filters.exclude_contraindications)}")
        
        if not any([filters.categories, filters.forms, filters.indications, 
                   filters.properties, filters.components, filters.exclude_properties]):
            print(f"     Нет фильтров")

if __name__ == "__main__":
    test_smart_nlp()
