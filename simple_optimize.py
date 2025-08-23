import json
import shutil

print("Создаем оптимизированную структуру базы данных...")

# 1. Создаем резервную копию
try:
    shutil.copy('knowledge_base.json', 'knowledge_base_backup.json')
    print("✅ Резервная копия создана")
except Exception as e:
    print(f"❌ Ошибка создания резервной копии: {e}")
    exit(1)

# 2. Загружаем все продукты
try:
    with open('knowledge_base.json', 'r', encoding='utf-8') as f:
        all_products = json.load(f)
    print(f"✅ Загружено {len(all_products)} продуктов")
except Exception as e:
    print(f"❌ Ошибка загрузки базы: {e}")
    exit(1)

# 3. Создаем CORE базу - первые 30 продуктов (самые важные)
core_products = all_products[:30]

# 4. Сохраняем файлы
try:
    # Core база
    with open('knowledge_base_core.json', 'w', encoding='utf-8') as f:
        json.dump(core_products, f, ensure_ascii=False, indent=2)
    
    # Full база (копия оригинала)
    with open('knowledge_base_full.json', 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    
    print("✅ Файлы созданы успешно")
    
except Exception as e:
    print(f"❌ Ошибка сохранения: {e}")
    exit(1)

# 5. Показываем результат
print(f"\n📊 РЕЗУЛЬТАТ:")
print(f"📁 knowledge_base_core.json - {len(core_products)} приоритетных продуктов")
print(f"📁 knowledge_base_full.json - {len(all_products)} всех продуктов") 
print(f"📁 knowledge_base_backup.json - резервная копия")

print(f"\n🔥 CORE БАЗА (первые 10 из {len(core_products)}):")
for i, product in enumerate(core_products[:10], 1):
    print(f"{i:2d}. {product['product']}")

print(f"\n🚀 Оптимизация завершена!")
print(f"💡 Core база загружается в ~{len(all_products)//len(core_products)}x раз быстрее")






