import json
import shutil
from datetime import datetime

# Создаем резервную копию
shutil.copy('knowledge_base.json', 'knowledge_base_backup.json')
print("✅ Резервная копия создана: knowledge_base_backup.json")

# Загружаем полную базу
with open('knowledge_base.json', 'r', encoding='utf-8') as f:
    all_products = json.load(f)

print(f"📊 Загружено {len(all_products)} продуктов")

# Определяем топ-30 популярных продуктов для core базы
# Критерии: важные линейки + популярные категории + новые продукты
core_product_ids = [
    # Линейка Румарин (приоритет)
    'roomarine_extra', 'roomarine_calcium', 'roomarine_chitosan',
    
    # Популярные антиоксиданты
    'solberry_h', 'beeteron_h', 'orange_day', 'orange_tabs', 'orangemu',
    
    # Важные БАДы и витамины
    'selen_tabs', 'mg_evening', 'royal_jelly', 'omega3_fish_oil',
    'multi_zink_mussels', 'ognevitt',
    
    # Сорбенты и детокс
    'profibex', 'argent_max',
    
    # Мужское здоровье
    'aspen_extra', 'prostosin', 'bars_1',
    
    # Новые продукты
    'serotonin_drops',
    
    # Пептиды и красота
    'foam_washing', 'peptide_complex',
    
    # Травы и настои
    'propolux', 'propolux_tabs',
    
    # Лецитин
    'lecithin_vanilla', 'lecithin_tube_f',
    
    # Дополнительные важные
    'bwl_extra_caps', 'alfalfa_extra_tabs', 'mg_plus', 'mg_tabs'
]

# Создаем core базу
core_products = []
core_ids_found = []

for product in all_products:
    if product['id'] in core_product_ids:
        core_products.append(product)
        core_ids_found.append(product['id'])

# Добавляем продукты, которые не нашлись по ID, но важны
missing_core_ids = set(core_product_ids) - set(core_ids_found)
if missing_core_ids:
    print(f"⚠️  Не найдены продукты с ID: {missing_core_ids}")

# Если core получился меньше 25 продуктов, добавляем еще
if len(core_products) < 25:
    remaining_products = [p for p in all_products if p['id'] not in core_ids_found]
    # Добавляем по приоритету категорий
    priority_categories = ['Антиоксиданты', 'Румарины и БАРСы (З+А)', 'Сорбенты', 'Красота / Уход за телом']
    
    for category in priority_categories:
        for product in remaining_products:
            if len(core_products) >= 30:
                break
            if product.get('category') == category and product not in core_products:
                core_products.append(product)

# Если все еще мало, добавляем остальные
if len(core_products) < 30:
    remaining = [p for p in all_products if p not in core_products]
    core_products.extend(remaining[:30-len(core_products)])

# Сохраняем core базу
with open('knowledge_base_core.json', 'w', encoding='utf-8') as f:
    json.dump(core_products, f, ensure_ascii=False, indent=2)

# Сохраняем full базу (это та же полная база)
with open('knowledge_base_full.json', 'w', encoding='utf-8') as f:
    json.dump(all_products, f, ensure_ascii=False, indent=2)

print(f"\n✅ Создана оптимизированная структура:")
print(f"📁 knowledge_base_core.json - {len(core_products)} приоритетных продуктов")
print(f"📁 knowledge_base_full.json - {len(all_products)} всех продуктов")
print(f"📁 knowledge_base_backup.json - резервная копия")

print(f"\n🔥 CORE БАЗА ({len(core_products)} продуктов):")
print("=" * 60)
for i, product in enumerate(core_products, 1):
    category = product.get('category', 'Без категории')
    print(f"{i:2d}. {product['product']}")
    print(f"    Категория: {category}")

print("\n📊 Статистика по категориям в CORE:")
category_stats = {}
for product in core_products:
    cat = product.get('category', 'Без категории')
    category_stats[cat] = category_stats.get(cat, 0) + 1

for cat, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
    print(f"  {cat}: {count} продуктов")

print(f"\n💾 Размеры файлов:")
import os
core_size = os.path.getsize('knowledge_base_core.json') // 1024
full_size = os.path.getsize('knowledge_base_full.json') // 1024
print(f"  Core: {core_size} KB")
print(f"  Full: {full_size} KB") 
print(f"  Ускорение загрузки: ~{full_size//core_size}x")

# Создаем информационный файл
db_info = {
    "created": datetime.now().isoformat(),
    "structure": {
        "core": {
            "file": "knowledge_base_core.json",
            "products_count": len(core_products),
            "description": "Топ продукты для быстрых ответов",
            "size_kb": core_size
        },
        "full": {
            "file": "knowledge_base_full.json", 
            "products_count": len(all_products),
            "description": "Полная база всех продуктов",
            "size_kb": full_size
        },
        "backup": {
            "file": "knowledge_base_backup.json",
            "description": "Резервная копия"
        }
    },
    "usage": {
        "bot_logic": "1. Поиск в core → 2. При необходимости поиск в full",
        "update_procedure": "Обновлять core, full и backup одновременно"
    }
}

with open('database_info.json', 'w', encoding='utf-8') as f:
    json.dump(db_info, f, ensure_ascii=False, indent=2)

print(f"\n📋 Создан файл database_info.json с информацией о структуре")
print(f"\n🚀 Оптимизация завершена! Готово к использованию.")






