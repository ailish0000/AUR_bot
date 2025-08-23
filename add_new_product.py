import json

def add_product_to_new_db(product_data):
    """
    Добавляет новый продукт в knowledge_base_new.json
    """
    try:
        # Загружаем существующие продукты из нового файла
        with open('knowledge_base_new.json', 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        # Проверяем, нет ли уже такого ID
        existing_ids = [p['id'] for p in products]
        if product_data['id'] in existing_ids:
            print(f"⚠️  Продукт с ID '{product_data['id']}' уже существует")
            return False
        
        # Добавляем новый продукт
        products.append(product_data)
        
        # Сохраняем обновленный файл
        with open('knowledge_base_new.json', 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Продукт добавлен в knowledge_base_new.json")
        print(f"📊 Всего продуктов в новой базе: {len(products)}")
        print(f"🆕 Добавлен: {product_data['product']}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении продукта: {e}")
        return False

def show_all_databases():
    """
    Показывает статистику по всем базам данных
    """
    print("📊 СТАТИСТИКА БАЗ ДАННЫХ:")
    print("=" * 50)
    
    # Основная база
    try:
        with open('knowledge_base.json', 'r', encoding='utf-8') as f:
            main_products = json.load(f)
        print(f"📁 knowledge_base.json: {len(main_products)} продуктов")
    except:
        print("📁 knowledge_base.json: ❌ не удалось загрузить")
    
    # Новая база
    try:
        with open('knowledge_base_new.json', 'r', encoding='utf-8') as f:
            new_products = json.load(f)
        print(f"📁 knowledge_base_new.json: {len(new_products)} продуктов")
        
        if new_products:
            print("\n🆕 НОВЫЕ ПРОДУКТЫ:")
            for i, product in enumerate(new_products, 1):
                print(f"  {i}. {product['product']}")
    except:
        print("📁 knowledge_base_new.json: ❌ не удалось загрузить")

if __name__ == "__main__":
    show_all_databases()






