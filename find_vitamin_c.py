#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

def find_vitamin_c_products():
    """Ищет продукты с витамином С в базах знаний"""
    
    print("🔍 ПОИСК ПРОДУКТОВ С ВИТАМИНОМ С")
    print("="*50)
    
    vitamin_c_products = []
    
    for kb_file in ['knowledge_base.json', 'knowledge_base_new.json']:
        print(f"\n📂 Ищем в {kb_file}...")
        
        try:
            with open(kb_file, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
            
            for item in kb_data:
                product_name = item.get('product', '')
                description = item.get('description', '').lower()
                composition = item.get('composition', '').lower()
                benefits = ' '.join(item.get('benefits', [])).lower()
                
                # Ищем витамин С
                search_text = f"{product_name.lower()} {description} {composition} {benefits}"
                
                if any(term in search_text for term in [
                    'витамин с', 'vitamin c', 'аскорбин', 'оранж'
                ]):
                    vitamin_c_products.append({
                        'product': product_name,
                        'file': kb_file,
                        'description': item.get('description', '')[:300],
                        'composition': item.get('composition', '')[:300],
                        'benefits': item.get('benefits', [])[:3]
                    })
                    
                    print(f"✅ Найден: {product_name}")
                    if 'витамин с' in search_text:
                        print("   🎯 Прямое упоминание 'витамин С'")
                    if 'аскорбин' in search_text:
                        print("   🎯 Содержит аскорбиновую кислоту")
                    if 'оранж' in search_text:
                        print("   🍊 Оранж продукт (обычно с витамином С)")
                        
        except Exception as e:
            print(f"❌ Ошибка чтения {kb_file}: {e}")
    
    print(f"\n📊 ИТОГО НАЙДЕНО: {len(vitamin_c_products)} продуктов")
    
    return vitamin_c_products

def check_metadata_for_vitamin_c():
    """Проверяет как витамин С представлен в метаданных"""
    
    print(f"\n" + "="*50)
    print("🔬 ПРОВЕРКА МЕТАДАННЫХ ДЛЯ ВИТАМИНА С")
    print("="*50)
    
    try:
        with open('products_metadata.json', 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        vitamin_c_in_metadata = []
        
        for item in metadata:
            product_name = item['product_name'].lower()
            components = [c.lower() for c in item.get('main_components', [])]
            
            # Ищем витамин С в метаданных
            if any(term in product_name for term in ['оранж']) or \
               any('витамин с' in comp or 'аскорбин' in comp for comp in components):
                
                vitamin_c_in_metadata.append({
                    'product': item['product_name'],
                    'category': item['category'],
                    'components': item.get('main_components', [])[:5],
                    'properties': item.get('properties', [])
                })
                
                print(f"✅ В метаданных: {item['product_name']}")
                print(f"   Категория: {item['category']}")
                print(f"   Компоненты: {', '.join(item.get('main_components', [])[:3])}")
        
        print(f"\n📊 В метаданных найдено: {len(vitamin_c_in_metadata)} продуктов")
        
        return vitamin_c_in_metadata
        
    except Exception as e:
        print(f"❌ Ошибка чтения метаданных: {e}")
        return []

def test_vitamin_c_search():
    """Тестирует поиск витамина С умным поиском"""
    
    print(f"\n" + "="*50)
    print("🧪 ТЕСТ ПОИСКА ВИТАМИНА С")
    print("="*50)
    
    try:
        from smart_search_engine import SmartSearchEngine
        
        search_engine = SmartSearchEngine()
        
        queries = [
            "витамин С",
            "vitamin c", 
            "аскорбиновая кислота",
            "оранж табс",
            "содержит витамин с"
        ]
        
        for query in queries:
            print(f"\n🔍 Запрос: '{query}'")
            results = search_engine.search(query)
            
            if results:
                print(f"   ✅ Найдено: {len(results)} продуктов")
                for r in results[:3]:
                    print(f"      • {r.product_name} (score: {r.score:.1f})")
            else:
                print(f"   ❌ Ничего не найдено")
                
    except Exception as e:
        print(f"❌ Ошибка умного поиска: {e}")

if __name__ == "__main__":
    # Ищем в исходных базах
    products = find_vitamin_c_products()
    
    # Проверяем метаданные
    metadata_products = check_metadata_for_vitamin_c()
    
    # Тестируем умный поиск
    test_vitamin_c_search()





