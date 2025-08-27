#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

def check_vitamin_c_category():
    """Ищет категорию Витамин С в базах знаний"""
    
    print("🔍 ПОИСК КАТЕГОРИИ 'ВИТАМИН С'")
    print("="*40)
    
    all_categories = set()
    vitamin_c_products = []
    
    for kb_file in ['knowledge_base.json', 'knowledge_base_new.json']:
        print(f"\n📂 Проверяем {kb_file}...")
        
        try:
            with open(kb_file, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
            
            for item in kb_data:
                category = item.get('category', '')
                product = item.get('product', '')
                
                if category:
                    all_categories.add(category)
                
                # Ищем категорию с витамином С
                if category and ('витамин с' in category.lower() or 'vitamin c' in category.lower()):
                    vitamin_c_products.append({
                        'product': product,
                        'category': category,
                        'file': kb_file
                    })
                    print(f"✅ Найден: {product} в категории '{category}'")
                    
        except Exception as e:
            print(f"❌ Ошибка чтения {kb_file}: {e}")
    
    print(f"\n📋 ВСЕ УНИКАЛЬНЫЕ КАТЕГОРИИ ({len(all_categories)}):")
    for category in sorted(all_categories):
        if 'витамин' in category.lower():
            print(f"  🎯 {category}")  # выделяем витаминные категории
        else:
            print(f"  • {category}")
    
    if vitamin_c_products:
        print(f"\n✅ НАЙДЕНА КАТЕГОРИЯ 'ВИТАМИН С'!")
        print(f"Продуктов в этой категории: {len(vitamin_c_products)}")
        
        for item in vitamin_c_products:
            print(f"  • {item['product']} ({item['file']})")
        
        return vitamin_c_products
    else:
        print(f"\n❌ Категория 'Витамин С' не найдена")
        
        # Ищем продукты с витамином С в других категориях
        print("\n🔍 Ищем продукты с витамином С в других категориях...")
        
        for kb_file in ['knowledge_base.json', 'knowledge_base_new.json']:
            try:
                with open(kb_file, 'r', encoding='utf-8') as f:
                    kb_data = json.load(f)
                
                for item in kb_data:
                    product = item.get('product', '')
                    category = item.get('category', '')
                    description = item.get('description', '').lower()
                    composition = item.get('composition', '').lower()
                    
                    search_text = f"{product.lower()} {description} {composition}"
                    
                    if 'оранж' in search_text or 'аскорбин' in search_text:
                        print(f"  📦 {product} ({category}) - содержит витамин С")
                        
            except Exception as e:
                continue
        
        return []

if __name__ == "__main__":
    vitamin_c_products = check_vitamin_c_category()
    
    if vitamin_c_products:
        print(f"\n🔧 НУЖНО ДОБАВИТЬ В smart_nlp_parser.py:")
        print(f"'Витамин С': [r'витамин\\s*с', r'vitamin\\s*c'],")
    else:
        print(f"\n💡 Возможно, категория называется по-другому или нужно создать её")





