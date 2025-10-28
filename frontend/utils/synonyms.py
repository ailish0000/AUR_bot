"""
Synonyms utility - расширение запросов синонимами
"""
from typing import List, Dict

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

# Синонимы для витамина C
VITAMIN_C_SYNONYMS = [
    "витамин c", "витамин с", "vitamin c", "аскорбинка",
    "аскорбиновая кислота", "аскорбиновой кислоты"
]

# Синонимы для коллагена
COLLAGEN_SYNONYMS = [
    "коллаген", "коллагена", "коллагеном", "collagen",
    "для кожи", "для волос", "для ногтей", "для суставов",
    "гидролизованный коллаген", "морской коллаген"
]

# Синонимы для пробиотиков
PROBIOTICS_SYNONYMS = [
    "пробиотик", "пробиотики", "пробиотиков", "пробиотикам",
    "для кишечника", "для микрофлоры", "бактерии", "лактобактерии",
    "бифидобактерии", "для пищеварения"
]

# Синонимы для иммунитета
IMMUNITY_SYNONYMS = [
    "иммунитет", "иммунитета", "иммунной системы",
    "противовирусное", "от вирусов", "защита", "для защиты",
    "укрепление иммунитета", "повышение иммунитета"
]

# Словарь всех категорий синонимов
SYNONYM_CATEGORIES: Dict[str, List[str]] = {
    "omega": OMEGA_SYNONYMS,
    "magnesium": MAGNESIUM_SYNONYMS,
    "vitamin_c": VITAMIN_C_SYNONYMS,
    "collagen": COLLAGEN_SYNONYMS,
    "probiotics": PROBIOTICS_SYNONYMS,
    "immunity": IMMUNITY_SYNONYMS,
}


def expand_query_with_synonyms(query: str) -> str:
    """
    Расширяет запрос синонимами для улучшения поиска
    
    Args:
        query: Исходный запрос
    
    Returns:
        Расширенный запрос с синонимами
    """
    query_lower = query.lower()
    expanded_terms = []
    
    # Проверяем каждую категорию синонимов
    for category, synonyms in SYNONYM_CATEGORIES.items():
        for synonym in synonyms:
            if synonym in query_lower:
                # Добавляем все синонимы этой категории
                expanded_terms.extend(synonyms)
                break  # Прерываем после первого совпадения в категории
    
    # Если найдены синонимы, добавляем их к запросу
    if expanded_terms:
        # Убираем дубликаты и возвращаем
        unique_terms = list(set(expanded_terms))
        return f"{query} {' '.join(unique_terms)}"
    
    return query


def detect_category(query: str) -> str:
    """
    Определяет категорию запроса на основе ключевых слов
    
    Args:
        query: Запрос пользователя
    
    Returns:
        Название категории или 'unknown'
    """
    query_lower = query.lower()
    
    for category, synonyms in SYNONYM_CATEGORIES.items():
        for synonym in synonyms:
            if synonym in query_lower:
                return category
    
    return "unknown"


def get_category_synonyms(category: str) -> List[str]:
    """
    Получить все синонимы для заданной категории
    
    Args:
        category: Название категории
    
    Returns:
        Список синонимов
    """
    return SYNONYM_CATEGORIES.get(category, [])
