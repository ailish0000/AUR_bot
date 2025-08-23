import json
import os
from datetime import datetime

def update_category_in_file(file_path):
    """Обновляет категорию в указанном файле"""
    try:
        # Загружаем файл
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            products = json.load(f)
        
        # Переименовываем категорию
        updated_count = 0
        for product in products:
            if product['category'] == 'Витамины и минералы':
                product['category'] = 'Витамины, минералы и микроэлементы'
                updated_count += 1
                print(f"  ✅ Обновлен: {product['product']}")
        
        if updated_count > 0:
            # Создаем резервную копию
            backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            
            # Сохраняем обновленный файл
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            
            print(f"  💾 Резервная копия: {backup_path}")
            return updated_count
        else:
            print(f"  ⚠️ Продукты с категорией 'Витамины и минералы' не найдены")
            return 0
            
    except Exception as e:
        print(f"  ❌ Ошибка обработки файла: {e}")
        return 0

def main():
    """Основная функция обновления всех файлов"""
    print("🔄 Обновляем категорию 'Витамины и минералы' во всех файлах...")
    
    # Список файлов для обновления
    files_to_update = [
        'knowledge_base.json',
        'knowledge_base_new.json',
        'knowledge_base_fixed.json',
        'knowledge_base_backup.json'
    ]
    
    # Добавляем все резервные копии
    backup_files = [f for f in os.listdir('.') if f.startswith('knowledge_base_backup_') and f.endswith('.json')]
    files_to_update.extend(backup_files)
    
    total_updated = 0
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            print(f"\n📁 Обрабатываем файл: {file_path}")
            updated_count = update_category_in_file(file_path)
            total_updated += updated_count
        else:
            print(f"\n📁 Файл не найден: {file_path}")
    
    print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"📈 Всего обновлено категорий: {total_updated}")
    
    if total_updated > 0:
        print("✅ Обновление завершено успешно!")
        print("🔄 Категория изменена: 'Витамины и минералы' → 'Витамины, минералы и микроэлементы'")
        
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
    else:
        print("❌ Продукты с категорией 'Витамины и минералы' не найдены ни в одном файле")

if __name__ == "__main__":
    main()





