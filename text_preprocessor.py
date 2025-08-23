# text_preprocessor.py
"""
Модуль для очистки и нормализации текста
"""
import re
import string
from typing import Dict, List

class TextPreprocessor:
    def __init__(self):
        # Словарь для исправления частых опечаток
        self.typo_corrections = {
            # Глаголы
            "посоветую": "посоветуй",
            "подскажу": "подскажи", 
            "помогу": "помоги",
            "расскажу": "расскажи",
            "покажу": "покажи",
            "объясню": "объясни",
            
            # Продукты
            "солбери": "солберри",
            "солберий": "солберри", 
            "салберри": "солберри",
            "битерон": "битерон",
            "биторон": "битерон",
            "бетерон": "битерон",
            
            # Проблемы со здоровьем
            "простуда": "простуда",
            "простуды": "простуда",
            "грип": "грипп",
            "гриппа": "грипп",
            "печень": "печень",
            "печени": "печень",
            "холестерин": "холестерин",
            "холестерина": "холестерин",
            "усталость": "усталость",
            "усталости": "усталость",
            
            # Частые опечатки
            "чтонибудь": "что-нибудь",
            "чтонибуть": "что-нибудь",
            "что-нибуть": "что-нибудь",
            "чтото": "что-то",
            "как-то": "как то",
            "почему-то": "почему то",
            
            # Вопросительные слова
            "что": "что",
            "чего": "что",
            "какой": "какой",
            "какая": "какой",
            "какое": "какой",
            "какие": "какой",
            "как": "как",
            "где": "где",
            "куда": "где",
            "когда": "когда",
            "почему": "почему",
            "зачем": "почему",
            
            # Предлоги и частицы
            "от": "от",
            "для": "для",
            "при": "при",
            "во время": "при",
            "в время": "при",
            "вовремя": "при",
            
            # Регистрация
            "зарегестрироваться": "зарегистрироваться",
            "зарегистрация": "регистрация",
            "региcтрация": "регистрация",
            "регестрация": "регистрация",
        }
        
        # Паттерны для очистки
        self.cleanup_patterns = [
            (r'\s+', ' '),  # Множественные пробелы
            (r'[.]{2,}', '.'),  # Множественные точки
            (r'[!]{2,}', '!'),  # Множественные восклицательные знаки
            (r'[?]{2,}', '?'),  # Множественные вопросительные знаки
            (r'[,]{2,}', ','),  # Множественные запятые
            (r'\s*([.!?,:;])\s*', r'\1 '),  # Пробелы вокруг пунктуации
            (r'([.!?])\s*$', r'\1'),  # Убираем пробелы в конце после пунктуации
        ]
        
        # Стоп-слова, которые можно убрать для лучшего поиска
        self.stop_words = {
            "а", "и", "но", "или", "да", "нет", "не", "ни", "же", "ли", "бы", "ж", "то", "те", "эти", "эта", "этот", "это",
            "такой", "такая", "такое", "такие", "очень", "более", "менее", "самый", "самая", "самое", "самые",
            "может", "можете", "можешь", "можно", "нужно", "надо", "стоит", "следует", "должен", "должна", "должно"
        }

    def clean_text(self, text: str) -> str:
        """Основная функция очистки текста"""
        if not text or not isinstance(text, str):
            return ""
        
        # 1. Приводим к нижнему регистру
        text = text.lower().strip()
        
        # 2. Убираем лишние символы (но оставляем русские буквы, цифры и основную пунктуацию)
        text = re.sub(r'[^\w\s.!?,:;()-]+', '', text, flags=re.UNICODE)
        
        # 3. Применяем паттерны очистки
        for pattern, replacement in self.cleanup_patterns:
            text = re.sub(pattern, replacement, text)
        
        # 4. Исправляем опечатки
        text = self.fix_typos(text)
        
        # 5. Финальная очистка
        text = text.strip()
        
        return text

    def fix_typos(self, text: str) -> str:
        """Исправляет частые опечатки"""
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Убираем пунктуацию для проверки
            clean_word = word.strip('.,!?:;()-')
            
            # Проверяем точное совпадение
            if clean_word in self.typo_corrections:
                # Заменяем, сохраняя пунктуацию
                punct_before = ''
                punct_after = ''
                
                if word != clean_word:
                    # Извлекаем пунктуацию
                    start_idx = word.find(clean_word)
                    if start_idx > 0:
                        punct_before = word[:start_idx]
                    end_idx = start_idx + len(clean_word)
                    if end_idx < len(word):
                        punct_after = word[end_idx:]
                
                corrected_word = punct_before + self.typo_corrections[clean_word] + punct_after
                corrected_words.append(corrected_word)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)

    def normalize_for_search(self, text: str) -> str:
        """Нормализует текст для поиска (более агрессивная очистка)"""
        # Начинаем с базовой очистки
        text = self.clean_text(text)
        
        # Убираем стоп-слова
        words = text.split()
        meaningful_words = [word for word in words if word not in self.stop_words and len(word) > 2]
        
        # Убираем пунктуацию для поиска
        clean_words = []
        for word in meaningful_words:
            clean_word = word.strip('.,!?:;()-')
            if clean_word:
                clean_words.append(clean_word)
        
        return ' '.join(clean_words)

    def preprocess_knowledge_base_text(self, text: str) -> str:
        """Предобработка текста из базы знаний"""
        if not text or not isinstance(text, str):
            return ""
        
        # Базовая очистка
        text = self.clean_text(text)
        
        # Дополнительная очистка для базы знаний
        # Убираем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', ' ', text)
        
        # Стандартизируем некоторые фразы
        text = re.sub(r'показания?\s+к\s+применению', 'показания к применению', text)
        text = re.sub(r'способ\s+применения', 'применение', text)
        text = re.sub(r'состав\s+продукта?', 'состав', text)
        
        return text.strip()

    def debug_preprocessing(self, original_text: str) -> Dict[str, str]:
        """Отладочная функция - показывает все этапы обработки"""
        result = {
            "original": original_text,
            "cleaned": self.clean_text(original_text),
            "normalized_for_search": self.normalize_for_search(original_text),
            "knowledge_base_format": self.preprocess_knowledge_base_text(original_text)
        }
        return result

# Создаем глобальный экземпляр
text_preprocessor = TextPreprocessor()







