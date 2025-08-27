#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from metadata_structure import MetadataExtractor, ProductMetadata
from typing import List, Dict

def extract_all_products_metadata():
    """Извлекает метаданные из всех продуктов в базе знаний"""
    
    print("🔍 ИЗВЛЕЧЕНИЕ МЕТАДАННЫХ ИЗ ВСЕХ ПРОДУКТОВ")
    print("="*60)
    
    extractor = MetadataExtractor()
    all_metadata = []
    
    # Читаем обе базы знаний
    knowledge_files = ['knowledge_base.json', 'knowledge_base_new.json']
    
    for kb_file in knowledge_files:
        print(f"\n📂 Обрабатываем {kb_file}...")
        
        try:
            with open(kb_file, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
            
            print(f"   Найдено продуктов: {len(kb_data)}")
            
            for i, product in enumerate(kb_data):
                try:
                    metadata = extractor.extract_metadata(product)
                    
                    # Добавляем источник
                    metadata_dict = {
                        'source_file': kb_file,
                        'product_name': metadata.product_name,
                        'category': metadata.category.value,
                        'form': metadata.form.value,
                        'target_group': metadata.target_group.value,
                        'health_indications': [ind.value for ind in metadata.health_indications],
                        'main_components': metadata.main_components,
                        'properties': metadata.properties,
                        'contraindications': metadata.contraindications,
                        'dosage_form': metadata.dosage_form,
                        'original_data': product  # сохраняем оригинальные данные
                    }
                    
                    all_metadata.append(metadata_dict)
                    
                    if (i + 1) % 10 == 0:
                        print(f"   Обработано: {i + 1}/{len(kb_data)}")
                        
                except Exception as e:
                    print(f"   ❌ Ошибка при обработке продукта {product.get('product', 'Unknown')}: {e}")
                    
        except Exception as e:
            print(f"❌ Ошибка чтения файла {kb_file}: {e}")
    
    # Сохраняем результат
    output_file = 'products_metadata.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_metadata, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Метаданные сохранены в {output_file}")
    print(f"📊 Всего обработано продуктов: {len(all_metadata)}")
    
    return all_metadata

def analyze_metadata(metadata_list: List[Dict]):
    """Анализирует извлеченные метаданные"""
    
    print(f"\n📊 АНАЛИЗ МЕТАДАННЫХ")
    print("="*60)
    
    # Статистика по категориям
    categories = {}
    forms = {}
    indications = {}
    properties = {}
    
    for item in metadata_list:
        # Категории
        category = item['category']
        categories[category] = categories.get(category, 0) + 1
        
        # Формы выпуска
        form = item['form']
        forms[form] = forms.get(form, 0) + 1
        
        # Показания
        for indication in item['health_indications']:
            indications[indication] = indications.get(indication, 0) + 1
        
        # Свойства
        for prop in item['properties']:
            properties[prop] = properties.get(prop, 0) + 1
    
    print(f"\n📋 КАТЕГОРИИ ПРОДУКТОВ:")
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   {category}: {count} продуктов")
    
    print(f"\n💊 ФОРМЫ ВЫПУСКА:")
    for form, count in sorted(forms.items(), key=lambda x: x[1], reverse=True):
        print(f"   {form}: {count} продуктов")
    
    print(f"\n🎯 ОСНОВНЫЕ ПОКАЗАНИЯ:")
    for indication, count in sorted(indications.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {indication}: {count} продуктов")
    
    print(f"\n⚡ ОСНОВНЫЕ СВОЙСТВА:")
    for prop, count in sorted(properties.items(), key=lambda x: x[1], reverse=True):
        print(f"   {prop}: {count} продуктов")
    
    # Примеры продуктов по категориям
    print(f"\n🔍 ПРИМЕРЫ ПО КАТЕГОРИЯМ:")
    for category in list(categories.keys())[:5]:
        examples = [item['product_name'] for item in metadata_list 
                   if item['category'] == category][:3]
        print(f"   {category}: {', '.join(examples)}")

def find_products_by_criteria(metadata_list: List[Dict], **criteria):
    """Находит продукты по заданным критериям"""
    
    print(f"\n🔎 ПОИСК ПО КРИТЕРИЯМ: {criteria}")
    print("-" * 40)
    
    filtered_products = []
    
    for item in metadata_list:
        match = True
        
        # Проверяем каждый критерий
        for key, value in criteria.items():
            if key == 'category' and item['category'] != value:
                match = False
                break
            elif key == 'form' and item['form'] != value:
                match = False
                break
            elif key == 'indication' and value not in item['health_indications']:
                match = False
                break
            elif key == 'property' and value not in item['properties']:
                match = False
                break
            elif key == 'component' and not any(value.lower() in comp.lower() 
                                               for comp in item['main_components']):
                match = False
                break
        
        if match:
            filtered_products.append(item)
    
    print(f"Найдено продуктов: {len(filtered_products)}")
    
    for product in filtered_products[:10]:  # показываем первые 10
        print(f"   • {product['product_name']} ({product['category']})")
        if product['properties']:
            print(f"     Свойства: {', '.join(product['properties'])}")
    
    return filtered_products

if __name__ == "__main__":
    # Извлекаем метаданные
    metadata = extract_all_products_metadata()
    
    # Анализируем
    analyze_metadata(metadata)
    
    # Тестируем поиск
    print(f"\n" + "="*60)
    print("🧪 ТЕСТИРОВАНИЕ ПОИСКА ПО МЕТАДАННЫМ")
    print("="*60)
    
    # Тест 1: Все гепатопротекторы
    find_products_by_criteria(metadata, category='Гепатопротекторы')
    
    # Тест 2: Все сорбенты
    find_products_by_criteria(metadata, property='сорбент')
    
    # Тест 3: Продукты для печени
    find_products_by_criteria(metadata, indication='печень')
    
    # Тест 4: Капсулы с магнием
    find_products_by_criteria(metadata, form='капсулы', component='магний')
    
    print(f"\n✅ Извлечение и анализ метаданных завершен!")





