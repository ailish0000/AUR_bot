import json

# Загружаем основную базу знаний
with open('knowledge_base.json', 'r', encoding='utf-8-sig') as f:
    products = json.load(f)

# Переименовываем категорию
updated_count = 0
for product in products:
    if product['category'] == 'Витамины и минералы':
        product['category'] = 'Витамины, минералы и микроэлементы'
        updated_count += 1
        print(f"✅ Обновлен продукт: {product['product']}")

if updated_count == 0:
    print("❌ Продукты с категорией 'Витамины и минералы' не найдены")
    exit(1)

# Создаем резервную копию
from datetime import datetime
backup_filename = f"knowledge_base_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(backup_filename, 'w', encoding='utf-8') as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

# Сохраняем обновленную базу
with open('knowledge_base.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

print(f"✅ Резервная копия создана: {backup_filename}")
print("✅ Обновленная база сохранена")

# Показываем обновленные продукты
print(f"\n📋 ОБНОВЛЕННЫЕ ПРОДУКТЫ:")
for product in products:
    if product['category'] == 'Витамины, минералы и микроэлементы':
        print(f"• {product['product']}")

# Обновляем векторную базу данных
try:
    from enhanced_vector_db import enhanced_vector_db
    print("\n🔄 Обновляем векторную базу данных...")
    enhanced_vector_db.index_knowledge()
    print("✅ Векторная база обновлена")
except ImportError:
    print("⚠️ Модуль enhanced_vector_db недоступен, пропускаем обновление векторов")
except Exception as e:
    print(f"❌ Ошибка обновления векторной базы: {e}")

print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
print(f"📈 Всего продуктов в базе: {len(products)}")
print(f"✅ Обновлено категорий: {updated_count}")
print(f"💾 Резервная копия: {backup_filename}")
print(f"🔄 Категория изменена: 'Витамины и минералы' → 'Витамины, минералы и микроэлементы'")





