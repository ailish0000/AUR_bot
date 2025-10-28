"""
Special Handlers - специальные обработчики для разных типов запросов
"""
from typing import Optional, Dict, Any


# Ключевые слова для определения запросов об иммунитете
IMMUNITY_KEYWORDS = [
    "иммунитет", "имунитет", "иммунной", "защита от вирусов",
    "противовирусное", "для иммунитета", "укрепление иммунитета",
    "повышение иммунитета", "поддержка иммунитета"
]

# Ключевые слова для small-talk
SMALLTALK_GREETINGS = {
    "привет", "здравствуйте", "добрый день", "добрый вечер",
    "доброе утро", "здравствуй", "hi", "hello"
}

SMALLTALK_HOWRU = {
    "как дела?", "как дела", "как ты?", "как ты", "how are you"
}

# Ключевые слова для определения "все варианты"
ALL_OPTIONS_KEYWORDS = [
    "какой еще", "еще есть", "помимо этого", "что еще",
    "все варианты", "все продукты", "что еще есть",
    "какие еще", "другие варианты", "еще варианты",
    "полный обзор", "весь ассортимент", "все что есть"
]


def is_immunity_query(query: str) -> bool:
    """
    Определяет, является ли запрос вопросом об иммунитете
    
    Args:
        query: Запрос пользователя
    
    Returns:
        True если запрос об иммунитете
    """
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in IMMUNITY_KEYWORDS)


def is_small_talk(query: str) -> Optional[str]:
    """
    Определяет, является ли запрос small-talk и возвращает ответ
    
    Args:
        query: Запрос пользователя
    
    Returns:
        Ответ на small-talk или None
    """
    query_lower = query.strip().lower()
    
    # Приветствия
    if query_lower in SMALLTALK_GREETINGS:
        return (
            "Привет! Я помогу с подбором продуктов Авроры. "
            "Спроси, например: 'От простуды', 'Для печени', "
            "'Состав Солберри-H', 'Как принимать Битерон-H'."
        )
    
    # Как дела
    if query_lower in SMALLTALK_HOWRU:
        return (
            "Спасибо, все отлично и я готова помочь! "
            "Опиши проблему или спроси про продукт."
        )
    
    return None


def is_all_options_request(query: str) -> bool:
    """
    Определяет, просит ли пользователь показать все варианты
    
    Args:
        query: Запрос пользователя
    
    Returns:
        True если пользователь просит все варианты
    """
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in ALL_OPTIONS_KEYWORDS)


def detect_special_product_category(query: str) -> Optional[str]:
    """
    Определяет специальную категорию продуктов
    
    Args:
        query: Запрос пользователя
    
    Returns:
        Название категории или None
    """
    query_lower = query.lower()
    
    # Противовирусные
    if any(kw in query_lower for kw in ["противовирусное", "от вирусов", "против вирусов"]):
        return "antiviral"
    
    # Коллаген
    if any(kw in query_lower for kw in ["коллаген", "для кожи", "для волос"]):
        return "collagen"
    
    # Магний
    if "магний" in query_lower:
        return "magnesium"
    
    # Сорбенты
    if any(kw in query_lower for kw in ["сорбент", "очищение", "детокс"]):
        return "sorbent"
    
    # Пробиотики
    if any(kw in query_lower for kw in ["пробиотик", "для кишечника", "микрофлора"]):
        return "probiotics"
    
    # Антипаразитарные
    if any(kw in query_lower for kw in ["паразит", "глист", "антипаразит"]):
        return "antiparasitic"
    
    # Печень
    if any(kw in query_lower for kw in ["печень", "печени", "гепато"]):
        return "liver"
    
    # Кальций/кости
    if any(kw in query_lower for kw in ["кальций", "кости", "костей"]):
        return "calcium"
    
    # Простуда/бронхит
    if any(kw in query_lower for kw in ["простуда", "бронхит", "кашель"]):
        return "cold_bronchitis"
    
    return None


def get_special_category_instructions(category: str) -> Optional[str]:
    """
    Получить специальные инструкции для категории
    
    Args:
        category: Название категории
    
    Returns:
        Дополнительные инструкции для LLM
    """
    instructions = {
        "antiviral": (
            "\n\nВНИМАНИЕ: Противовирусный запрос! "
            "ОБЯЗАТЕЛЬНО рекомендуй ВСЕ ТРИ продукта: "
            "1) Аргент-Макс, 2) БАРС-2, 3) Ин-Аурин. "
            "НЕ рекомендуй Гелластин!"
        ),
        "collagen": (
            "\n\nВНИМАНИЕ: Запрос о коллагене! "
            "ОБЯЗАТЕЛЬНО рекомендуй ВСЕ продукты с коллагеном: "
            "Коллаген Пюр, Коллаген Табс Апельсин, Коллаген Табс Вишня, Гелластин."
        ),
        "magnesium": (
            "\n\nВНИМАНИЕ: Запрос о магнии! "
            "ОБЯЗАТЕЛЬНО рекомендуй ВСЕ продукты: "
            "Магний Плюс (Mg Plus), Магний Табс (Mg Tabs), Магний-Вечер (Mg-Evening). "
            "ИГНОРИРУЙ продукты БЕЗ слова 'магний' в названии!"
        ),
        "sorbent": (
            "\n\nВНИМАНИЕ: Запрос о сорбентах! "
            "Рекомендуй ТОЛЬКО сорбенты: Сиалон-Микс манго, ПроФайбекс. "
            "НЕ рекомендуй Коралл-Аккорд!"
        ),
        "antiparasitic": (
            "\n\nВНИМАНИЕ: Запрос об антипаразитарных! "
            "Рекомендуй ВСЕ продукты: Еломил, Гепосин, Лист Черного Ореха Экстра Капс, "
            "Лист Черного Ореха Экстра Табс, Осина Экстра, Кошачий Коготь, Сиалон-Микс манго."
        ),
        "liver": (
            "\n\nВНИМАНИЕ: Запрос о печени! "
            "В первую очередь рекомендуй Силицитин - гепатопротектор."
        ),
        "calcium": (
            "\n\nВНИМАНИЕ: Запрос о кальции! "
            "Рекомендуй: Румарин Кальций, Кальций Банан, Кальций-Утро."
        ),
        "cold_bronchitis": (
            "\n\nВНИМАНИЕ: Запрос о простуде/бронхите! "
            "Рекомендуй КОМПЛЕКС: Аргент Макс + Солберри + Битерон, "
            "плюс для иммунитета (Витамин С, Ин-Аурин, БАРС-2)."
        ),
    }
    
    return instructions.get(category)


def enhance_context_with_special_instructions(
    context: str,
    query: str
) -> str:
    """
    Дополнить контекст специальными инструкциями
    
    Args:
        context: Исходный контекст
        query: Запрос пользователя
    
    Returns:
        Дополненный контекст
    """
    enhanced_context = context
    
    # Проверяем специальную категорию
    category = detect_special_product_category(query)
    if category:
        instructions = get_special_category_instructions(category)
        if instructions:
            enhanced_context += instructions
    
    # Проверяем запрос "все варианты"
    if is_all_options_request(query):
        enhanced_context += (
            "\n\nВНИМАНИЕ: Пользователь просит ВСЕ варианты продуктов. "
            "РЕКОМЕНДУЙ ВСЕ НАЙДЕННЫЕ ПРОДУКТЫ!"
        )
    
    return enhanced_context
