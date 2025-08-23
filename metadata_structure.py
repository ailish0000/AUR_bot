#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from enum import Enum

class ProductCategory(Enum):
    """Категории продуктов"""
    VITAMINS_MINERALS = "Витамины, минералы и микроэлементы"
    VITAMIN_C = "Витамин С"
    HERBS_EXTRACTS = "Травы и экстракты"
    PROBIOTICS = "Пробиотики"
    SORBENTS = "Сорбенты и детокс"
    IMMUNITY = "Для иммунитета"
    DIGESTION = "Для пищеварения"
    JOINTS_BONES = "Для суставов и костей"
    HEART_VESSELS = "Для сердца и сосудов"
    NERVOUS_SYSTEM = "Для нервной системы"
    SKIN_BEAUTY = "Для кожи и красоты"
    ENERGY_METABOLISM = "Энергия и метаболизм"
    ANTIPARASITIC = "Антипаразитарные"
    HEPATOPROTECTORS = "Гепатопротекторы"

class ProductForm(Enum):
    """Формы выпуска"""
    CAPSULES = "капсулы"
    TABLETS = "таблетки"
    POWDER = "порошок"
    LIQUID = "жидкий"
    SACHETS = "саше"
    CREAM = "крем"
    DROPS = "капли"

class TargetGroup(Enum):
    """Целевые группы"""
    ADULTS = "взрослые"
    CHILDREN = "дети"
    PREGNANT = "беременные"
    ELDERLY = "пожилые"
    ATHLETES = "спортсмены"
    UNIVERSAL = "универсальный"

class HealthIndication(Enum):
    """Показания к применению"""
    # Системы организма
    LIVER = "печень"
    KIDNEYS = "почки" 
    HEART = "сердце"
    VESSELS = "сосуды"
    STOMACH = "желудок"
    INTESTINES = "кишечник"
    JOINTS = "суставы"
    BONES = "кости"
    SKIN = "кожа"
    HAIR = "волосы"
    NAILS = "ногти"
    NERVOUS_SYSTEM = "нервная система"
    IMMUNITY = "иммунитет"
    
    # Состояния и симптомы
    COLD = "простуда"
    FATIGUE = "усталость"
    STRESS = "стресс"
    INFLAMMATION = "воспаление"
    DETOX = "детоксикация"
    DIGESTION = "пищеварение"
    METABOLISM = "обмен веществ"
    REGENERATION = "регенерация"
    ANTIOXIDANT = "антиоксидантное"
    PARASITES = "паразиты"

@dataclass
class ProductMetadata:
    """Структурированные метаданные продукта"""
    # Основная информация (обязательные поля)
    product_name: str
    category: ProductCategory
    form: ProductForm
    target_group: TargetGroup
    health_indications: List[HealthIndication]
    main_components: List[str]
    properties: List[str]  # ["сорбент", "гепатопротектор", "антиоксидант"]
    contraindications: List[str]
    dosage_form: str
    
    # Дополнительные свойства (опциональные поля)
    age_restrictions: Optional[str] = None
    dosage_frequency: Optional[str] = None
    course_duration: Optional[str] = None
    origin: Optional[str] = None  # "растительный", "синтетический"
    price_range: Optional[str] = None  # "бюджетный", "средний", "премиум"
    synergy_with: List[str] = None  # совместимые продукты
    
    def __post_init__(self):
        if self.synergy_with is None:
            self.synergy_with = []

class MetadataExtractor:
    """Извлекает метаданные из текстового описания продукта"""
    
    def __init__(self):
        # Словари для автоматического извлечения
        self.category_keywords = {
            ProductCategory.VITAMIN_C: [
                "витамин с", "vitamin c", "аскорбин", "оранж табс", "оранж дей"
            ],
            ProductCategory.VITAMINS_MINERALS: [
                "витамин", "минерал", "магний", "кальций", "железо", "цинк", 
                "витамин d", "витамин b", "фолиевая кислота"
            ],
            ProductCategory.HERBS_EXTRACTS: [
                "экстракт", "трава", "растительный", "фитокомплекс", "настойка",
                "расторопша", "артишок", "лопух", "солодка", "тимьян"
            ],
            ProductCategory.SORBENTS: [
                "сорбент", "диатомит", "детокс", "очищение", "токсины", 
                "шлаки", "кизельгур", "адсорбент"
            ],
            ProductCategory.HEPATOPROTECTORS: [
                "печень", "гепатопротектор", "силимарин", "расторопша",
                "желчегонный", "детоксикация печени"
            ],
            ProductCategory.PROBIOTICS: [
                "пробиотик", "бифидо", "лакто", "микрофлора", "кишечник",
                "бактерии", "пребиотик"
            ]
        }
        
        self.indication_keywords = {
            HealthIndication.LIVER: [
                "печень", "гепато", "желчь", "детоксикация", "токсины"
            ],
            HealthIndication.IMMUNITY: [
                "иммунитет", "защитные силы", "сопротивляемость", "антитела"
            ],
            HealthIndication.COLD: [
                "простуда", "орви", "грипп", "кашель", "насморк"
            ],
            HealthIndication.JOINTS: [
                "суставы", "хрящи", "связки", "артрит", "артроз"
            ]
        }
        
        self.form_keywords = {
            ProductForm.CAPSULES: ["капсул", "капс"],
            ProductForm.TABLETS: ["таблет", "табс"],
            ProductForm.POWDER: ["порошок", "сухая смесь"],
            ProductForm.LIQUID: ["сок", "концентрат", "жидкий"],
            ProductForm.SACHETS: ["саше", "пакет"]
        }
    
    def extract_metadata(self, product_data: Dict) -> ProductMetadata:
        """Извлекает метаданные из данных продукта"""
        
        product_name = product_data.get('product', '')
        description = product_data.get('description', '').lower()
        benefits = ' '.join(product_data.get('benefits', [])).lower()
        composition = product_data.get('composition', '').lower()
        full_text = f"{product_name.lower()} {description} {benefits} {composition}"
        
        # Определяем категорию
        category = self._detect_category(full_text)
        
        # Определяем форму выпуска
        form = self._detect_form(full_text)
        
        # Извлекаем показания
        indications = self._extract_indications(full_text)
        
        # Извлекаем компоненты
        components = self._extract_components(composition)
        
        # Определяем свойства
        properties = self._extract_properties(full_text)
        
        # Противопоказания
        contraindications = self._extract_contraindications(
            product_data.get('contraindications', '')
        )
        
        return ProductMetadata(
            product_name=product_name,
            category=category,
            form=form,
            target_group=TargetGroup.ADULTS,  # по умолчанию
            health_indications=indications,
            main_components=components,
            properties=properties,
            contraindications=contraindications,
            dosage_form=product_data.get('dosage', ''),
        )
    
    def _detect_category(self, text: str) -> ProductCategory:
        """Определяет категорию по ключевым словам с приоритетом"""
        # Сначала проверяем специализированные категории (высокий приоритет)
        priority_categories = [
            ProductCategory.VITAMIN_C,
            ProductCategory.HEPATOPROTECTORS,
            ProductCategory.SORBENTS,
            ProductCategory.ANTIPARASITIC,
            ProductCategory.PROBIOTICS,
            ProductCategory.VITAMINS_MINERALS
        ]
        
        for category in priority_categories:
            keywords = self.category_keywords.get(category, [])
            if any(keyword in text for keyword in keywords):
                return category
        
        # Затем проверяем остальные категории
        for category, keywords in self.category_keywords.items():
            if category not in priority_categories:
                if any(keyword in text for keyword in keywords):
                    return category
        
        return ProductCategory.HERBS_EXTRACTS  # по умолчанию
    
    def _detect_form(self, text: str) -> ProductForm:
        """Определяет форму выпуска"""
        for form, keywords in self.form_keywords.items():
            if any(keyword in text for keyword in keywords):
                return form
        return ProductForm.CAPSULES  # по умолчанию
    
    def _extract_indications(self, text: str) -> List[HealthIndication]:
        """Извлекает показания к применению"""
        indications = []
        for indication, keywords in self.indication_keywords.items():
            if any(keyword in text for keyword in keywords):
                indications.append(indication)
        return indications
    
    def _extract_components(self, composition: str) -> List[str]:
        """Извлекает основные компоненты"""
        if not composition:
            return []
        
        # Простое извлечение через запятые
        components = [c.strip() for c in composition.split(',')]
        return components[:5]  # берем первые 5
    
    def _extract_properties(self, text: str) -> List[str]:
        """Извлекает свойства продукта"""
        properties = []
        
        property_keywords = {
            "сорбент": ["сорбент", "адсорбент", "поглощает", "выводит токсины"],
            "гепатопротектор": ["гепатопротектор", "защита печени", "восстановление печени"],
            "антиоксидант": ["антиоксидант", "свободные радикалы", "окислительный стресс"],
            "противовоспалительный": ["противовоспалительн", "воспаление", "антивоспалительн"],
            "иммуномодулятор": ["иммуномодулятор", "иммунитет", "защитные силы"],
            "детоксикант": ["детокс", "очищение", "токсины", "шлаки"],
            "антипаразитарный": ["антипаразитарн", "паразиты", "глисты", "гельминты"]
        }
        
        for property_name, keywords in property_keywords.items():
            if any(keyword in text for keyword in keywords):
                properties.append(property_name)
        
        return properties
    
    def _extract_contraindications(self, contraindications: str) -> List[str]:
        """Извлекает противопоказания"""
        if not contraindications:
            return []
        
        # Простое разделение через запятые и очистка
        contras = [c.strip() for c in contraindications.split(',')]
        return [c for c in contras if c]

# Пример использования
if __name__ == "__main__":
    extractor = MetadataExtractor()
    
    # Тестовый продукт
    test_product = {
        'product': 'Силицитин',
        'description': 'натуральный гепатопротектор для очищения и защиты печени',
        'benefits': ['защита печени', 'детоксикация', 'антиоксидантное действие'],
        'composition': 'семена расторопши, экстракт овса, лецитин',
        'contraindications': 'индивидуальная непереносимость компонентов',
        'dosage': 'по 2 капсулы 3 раза в день'
    }
    
    metadata = extractor.extract_metadata(test_product)
    print("🧪 ТЕСТ ИЗВЛЕЧЕНИЯ МЕТАДАННЫХ")
    print(f"Продукт: {metadata.product_name}")
    print(f"Категория: {metadata.category.value}")
    print(f"Форма: {metadata.form.value}")
    print(f"Показания: {[i.value for i in metadata.health_indications]}")
    print(f"Свойства: {metadata.properties}")
    print(f"Компоненты: {metadata.main_components}")
