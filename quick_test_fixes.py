#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

def test_magnesium_in_kb():
    """Проверяет наличие магния в базе знаний"""
    print("🔍 Проверяем магний в базе знаний...")
    
    try:
        with open("knowledge_base.json", "r", encoding="utf-8") as f:
            kb_data = json.load(f)
        
        magnesium_products = []
        for product in kb_data:
            product_name = product.get("product", "").lower()
            if "магний" in product_name:
                magnesium_products.append(product.get("product", ""))
        
        print(f"✅ Найдено продуктов с магнием: {len(magnesium_products)}")
        for product in magnesium_products:
            print(f"  - {product}")
            
        return len(magnesium_products) > 0
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_argent_in_kb():
    """Проверяет наличие Аргент-Макс в базе знаний"""
    print("\n🔍 Проверяем Аргент-Макс в базе знаний...")
    
    try:
        with open("knowledge_base.json", "r", encoding="utf-8") as f:
            kb_data = json.load(f)
        
        argent_products = []
        for product in kb_data:
            product_name = product.get("product", "").lower()
            if "аргент" in product_name:
                argent_products.append({
                    "name": product.get("product", ""),
                    "url": product.get("url", ""),
                    "image_id": product.get("image_id", "")
                })
        
        print(f"✅ Найдено продуктов с Аргент: {len(argent_products)}")
        for product in argent_products:
            print(f"  - {product['name']}")
            print(f"    URL: {product['url']}")
            print(f"    Image ID: {product['image_id']}")
            
        return len(argent_products) > 0
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_smart_search_engine():
    """Проверяет исправления в smart_search_engine.py"""
    print("\n🔧 Проверяем исправления в smart_search_engine.py...")
    
    try:
        # Проверяем наличие магния в синонимах
        with open("smart_search_engine.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        has_magnesium_synonyms = '"магний"' in content and 'magnesium' in content
        has_magnesium_expansion = 'expanded_terms.append("магний")' in content
        
        print(f"✅ Магний в синонимах: {'ДА' if has_magnesium_synonyms else 'НЕТ'}")
        print(f"✅ Расширение запроса магния: {'ДА' if has_magnesium_expansion else 'НЕТ'}")
        
        return has_magnesium_synonyms and has_magnesium_expansion
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_bot_context():
    """Проверяет исправления в bot.py"""
    print("\n🤖 Проверяем исправления в bot.py...")
    
    try:
        with open("bot.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        has_magnesium_context = '"магний"' in content and '"кальций"' in content
        has_context_fix = 'len(text) > 30' in content
        
        print(f"✅ Магний в контексте: {'ДА' if has_magnesium_context else 'НЕТ'}")
        print(f"✅ Исправление очистки контекста: {'ДА' if has_context_fix else 'НЕТ'}")
        
        return has_magnesium_context and has_context_fix
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("🧪 БЫСТРЫЙ ТЕСТ ИСПРАВЛЕНИЙ")
    print("=" * 50)
    
    results = []
    results.append(test_magnesium_in_kb())
    results.append(test_argent_in_kb())
    results.append(test_smart_search_engine())
    results.append(test_bot_context())
    
    print("\n" + "=" * 50)
    print(f"✅ Успешных тестов: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ УСПЕШНО!")
    else:
        print("⚠️ Некоторые исправления не применены")




