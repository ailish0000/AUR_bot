import json

# Загружаем данные
with open('knowledge_base.json', 'r', encoding='utf-8') as f:
    all_products = json.load(f)

print(f"Загружено {len(all_products)} продуктов")

# Создаем core базу (первые 30 самых важных продуктов)
core_products = all_products[:30]

# Сохраняем все файлы
files_to_create = [
    ('knowledge_base_backup.json', all_products, 'Резервная копия'),
    ('knowledge_base_core.json', core_products, 'Core база'),
    ('knowledge_base_full.json', all_products, 'Full база')
]

for filename, data, description in files_to_create:
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ {description}: {filename} ({len(data)} продуктов)")

print(f"\n🔥 CORE БАЗА (ТОП-{len(core_products)} продуктов):")
for i, product in enumerate(core_products, 1):
    print(f"{i:2d}. {product['product']}")

print(f"\n🚀 Готово! Структура оптимизирована для качественных ответов бота.")






