import json
import os
from datetime import datetime

def merge_products():
    """Объединяет новые продукты с основной базой знаний"""
    
    print("🔄 Начинаем объединение продуктов...")
    
    # Загружаем основную базу знаний
    try:
        with open('knowledge_base.json', 'r', encoding='utf-8-sig') as f:
            main_products = json.load(f)
        print(f"✅ Основная база загружена: {len(main_products)} продуктов")
    except FileNotFoundError:
        print("❌ Файл knowledge_base.json не найден")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка чтения основной базы: {e}")
        return
    
    # Загружаем новые продукты
    try:
        with open('knowledge_base_new.json', 'r', encoding='utf-8-sig') as f:
            new_products = json.load(f)
        print(f"✅ Новая база загружена: {len(new_products)} продуктов")
    except FileNotFoundError:
        print("❌ Файл knowledge_base_new.json не найден")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка чтения новой базы: {e}")
        return
    
    # Создаем резервную копию
    backup_filename = f"knowledge_base_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(main_products, f, ensure_ascii=False, indent=2)
        print(f"✅ Резервная копия создана: {backup_filename}")
    except Exception as e:
        print(f"❌ Ошибка создания резервной копии: {e}")
        return
    
    # Проверяем дубликаты и добавляем новые продукты
    existing_ids = {product['id'] for product in main_products}
    added_count = 0
    skipped_count = 0
    
    for new_product in new_products:
        if new_product['id'] in existing_ids:
            print(f"⚠️ Продукт {new_product['product']} уже существует, пропускаем")
            skipped_count += 1
        else:
            main_products.append(new_product)
            print(f"✅ Добавлен: {new_product['product']}")
            added_count += 1
    
    # Сохраняем обновленную базу
    try:
        with open('knowledge_base.json', 'w', encoding='utf-8') as f:
            json.dump(main_products, f, ensure_ascii=False, indent=2)
        print(f"✅ Обновленная база сохранена")
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return
    
    # Обновляем векторную базу данных
    try:
        from enhanced_vector_db import enhanced_vector_db
        print("🔄 Обновляем векторную базу данных...")
        enhanced_vector_db.index_knowledge()
        print("✅ Векторная база обновлена")
    except ImportError:
        print("⚠️ Модуль enhanced_vector_db недоступен, пропускаем обновление векторов")
    except Exception as e:
        print(f"❌ Ошибка обновления векторной базы: {e}")
    
    # Итоговая статистика
    print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"📈 Всего продуктов в базе: {len(main_products)}")
    print(f"✅ Добавлено новых: {added_count}")
    print(f"⚠️ Пропущено дубликатов: {skipped_count}")
    print(f"💾 Резервная копия: {backup_filename}")
    
    # Показываем добавленные продукты
    if added_count > 0:
        print(f"\n🆕 ДОБАВЛЕННЫЕ ПРОДУКТЫ:")
        for product in new_products:
            if product['id'] not in existing_ids:
                print(f"• {product['product']} (ID: {product['id']})")

if __name__ == "__main__":
    merge_products()
