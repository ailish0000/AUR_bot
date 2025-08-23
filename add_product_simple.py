import json

def add_product(product_data):
    # Загружаем новую базу
    with open('knowledge_base_new.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    # Добавляем продукт
    products.append(product_data)
    
    # Сохраняем
    with open('knowledge_base_new.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Добавлен: {product_data['product']}")
    print(f"📊 Всего в новой базе: {len(products)} продуктов")

# Проверим текущее состояние
with open('knowledge_base.json', 'r', encoding='utf-8') as f:
    main_db = json.load(f)

with open('knowledge_base_new.json', 'r', encoding='utf-8') as f:
    new_db = json.load(f)

print("📊 СТРУКТУРА БАЗ ДАННЫХ:")
print(f"📁 knowledge_base.json (основная): {len(main_db)} продуктов")
print(f"📁 knowledge_base_new.json (новая): {len(new_db)} продуктов")
print(f"🔢 Общий итог: {len(main_db) + len(new_db)} продуктов")
print("\n✅ Готово к добавлению новых продуктов в knowledge_base_new.json!")






