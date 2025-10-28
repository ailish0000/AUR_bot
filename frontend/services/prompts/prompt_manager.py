"""
Prompt Manager - управление промптами для разных типов запросов
"""
from typing import Optional
from enum import Enum

from .product_selection import PRODUCT_SELECTION_PROMPT
from .product_inquiry import PRODUCT_INQUIRY_PROMPT
from .general_question import GENERAL_QUESTION_PROMPT
from .product_comparison import PRODUCT_COMPARISON_PROMPT
from .composition_inquiry import COMPOSITION_INQUIRY_PROMPT
from .complaint import COMPLAINT_PROMPT


class IntentType(str, Enum):
    """Типы намерений пользователя"""
    PRODUCT_SELECTION = "product_selection"
    PRODUCT_INQUIRY = "product_inquiry"
    GENERAL_QUESTION = "general_question"
    PRODUCT_COMPARISON = "product_comparison"
    COMPOSITION_INQUIRY = "composition_inquiry"
    COMPLAINT = "complaint"
    UNKNOWN = "unknown"


class PromptManager:
    """Менеджер для работы с промптами"""
    
    def __init__(self):
        """Инициализация менеджера промптов"""
        self.prompts = {
            IntentType.PRODUCT_SELECTION: PRODUCT_SELECTION_PROMPT,
            IntentType.PRODUCT_INQUIRY: PRODUCT_INQUIRY_PROMPT,
            IntentType.GENERAL_QUESTION: GENERAL_QUESTION_PROMPT,
            IntentType.PRODUCT_COMPARISON: PRODUCT_COMPARISON_PROMPT,
            IntentType.COMPOSITION_INQUIRY: COMPOSITION_INQUIRY_PROMPT,
            IntentType.COMPLAINT: COMPLAINT_PROMPT,
        }
        
        # Промпт по умолчанию
        self.default_prompt = GENERAL_QUESTION_PROMPT
    
    def get_prompt(self, intent: Optional[IntentType] = None) -> str:
        """
        Получить промпт для заданного намерения
        
        Args:
            intent: Тип намерения пользователя
        
        Returns:
            Системный промпт
        """
        if intent is None or intent == IntentType.UNKNOWN:
            return self.default_prompt
        
        return self.prompts.get(intent, self.default_prompt)
    
    def get_prompt_by_keywords(self, query: str) -> str:
        """
        Определить промпт на основе ключевых слов в запросе
        
        Args:
            query: Запрос пользователя
        
        Returns:
            Системный промпт
        """
        query_lower = query.lower()
        
        # Ключевые слова для сравнения
        comparison_keywords = [
            "отличие", "различие", "разница", "сравни", 
            "или", "vs", "чем отличается", "что лучше"
        ]
        if any(keyword in query_lower for keyword in comparison_keywords):
            return self.get_prompt(IntentType.PRODUCT_COMPARISON)
        
        # Ключевые слова для состава
        composition_keywords = [
            "состав", "компонент", "ингредиент", "входит", 
            "содержит", "из чего"
        ]
        if any(keyword in query_lower for keyword in composition_keywords):
            return self.get_prompt(IntentType.COMPOSITION_INQUIRY)
        
        # Ключевые слова для подбора продуктов
        selection_keywords = [
            "нужно", "нужен", "нужна", "посоветуй", "порекомендуй",
            "что принимать", "что пить", "помоги выбрать", "какой продукт",
            "для иммунитета", "от простуды", "для печени"
        ]
        if any(keyword in query_lower for keyword in selection_keywords):
            return self.get_prompt(IntentType.PRODUCT_SELECTION)
        
        # Ключевые слова для информации о продукте
        inquiry_keywords = [
            "расскажи о", "что такое", "информация о", "свойства",
            "для чего", "зачем", "как работает"
        ]
        if any(keyword in query_lower for keyword in inquiry_keywords):
            return self.get_prompt(IntentType.PRODUCT_INQUIRY)
        
        # Ключевые слова для жалоб
        complaint_keywords = [
            "не помогает", "не работает", "плохо", "хуже",
            "побочный эффект", "аллергия", "не подошло"
        ]
        if any(keyword in query_lower for keyword in complaint_keywords):
            return self.get_prompt(IntentType.COMPLAINT)
        
        # По умолчанию - общий вопрос
        return self.get_prompt(IntentType.GENERAL_QUESTION)


# Создаем глобальный экземпляр менеджера
_prompt_manager = None


def get_prompt_manager() -> PromptManager:
    """Получить глобальный экземпляр менеджера промптов"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
