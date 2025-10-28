"""
Скрипт миграции данных из knowledge_base.json в новую базу данных
"""
import json
import sys
import os
from pathlib import Path

# Добавляем путь к backend в sys.path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from core.database import create_tables, SessionLocal
from repositories.product_repo import ProductRepository
from models.product import ProductCreate
from sqlalchemy.orm import Session


def load_knowledge_base(file_path: str) -> list:
    """Загружает данные из knowledge_base.json"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Файл {file_path} не найден")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        return []


def convert_to_product_create(item: dict) -> ProductCreate:
    """Конвертирует элемент из knowledge_base.json в ProductCreate"""
    
    # Генерируем ID на основе названия
    product_id = item.get("id", item.get("product", "")).lower().replace(" ", "-").replace("_", "-")
    
    return ProductCreate(
        id=product_id,
        name=item.get("product", ""),
        description=item.get("description", ""),
        short_description=item.get("short_description", ""),
        category=item.get("category", ""),
        price=item.get("price"),
        benefits=item.get("benefits", []),
        short_benefits=item.get("short_benefits", []),
        composition=item.get("composition", ""),
        dosage=item.get("dosage", ""),
        contraindications=item.get("contraindications", ""),
        indications=item.get("indications", []),
        properties=item.get("properties", []),
        components=item.get("components", []),
        image_id=item.get("image_id"),
        url=item.get("url"),
        form=item.get("form"),
        weight=item.get("weight"),
        volume=item.get("volume"),
        is_available=item.get("is_available", True),
        rating=item.get("rating", 0.0),
        review_count=item.get("review_count", 0),
        tags=item.get("tags", []),
        product_metadata=item.get("metadata", {})
    )


def migrate_products(db: Session, knowledge_data: list) -> int:
    """Мигрирует продукты в базу данных"""
    product_repo = ProductRepository(db)
    migrated_count = 0
    error_count = 0
    
    print(f"Начинаем миграцию {len(knowledge_data)} продуктов...")
    
    for i, item in enumerate(knowledge_data, 1):
        try:
            # Конвертируем в ProductCreate
            product_data = convert_to_product_create(item)
            
            # Проверяем, не существует ли уже продукт
            existing_product = product_repo.get_by_id(product_data.id)
            if existing_product:
                print(f"ПРЕДУПРЕЖДЕНИЕ: Продукт {product_data.name} уже существует, пропускаем")
                continue
            
            # Создаем продукт
            product_repo.create(product_data)
            migrated_count += 1
            
            if i % 10 == 0:
                print(f"Обработано {i}/{len(knowledge_data)} продуктов...")
                
        except Exception as e:
            print(f"ОШИБКА: Ошибка при миграции продукта {item.get('product', 'Unknown')}: {e}")
            error_count += 1
            continue
    
    print(f"Миграция завершена:")
    print(f"   Успешно мигрировано: {migrated_count}")
    print(f"   Ошибок: {error_count}")
    print(f"   Всего обработано: {len(knowledge_data)}")
    
    return migrated_count


def main():
    """Основная функция миграции"""
    print("Запуск миграции данных...")
    
    # Путь к knowledge_base.json
    knowledge_base_path = Path(__file__).parent.parent.parent / "knowledge_base.json"
    
    if not knowledge_base_path.exists():
        print(f"ОШИБКА: Файл {knowledge_base_path} не найден")
        print("Убедитесь, что вы запускаете скрипт из корневой директории проекта")
        return
    
    # Загружаем данные
    print(f"Загружаем данные из {knowledge_base_path}")
    knowledge_data = load_knowledge_base(str(knowledge_base_path))
    
    if not knowledge_data:
        print("ОШИБКА: Нет данных для миграции")
        return
    
    # Создаем таблицы
    print("Создаем таблицы в базе данных...")
    create_tables()
    
    # Подключаемся к базе данных
    db = SessionLocal()
    
    try:
        # Мигрируем продукты
        migrated_count = migrate_products(db, knowledge_data)
        
        if migrated_count > 0:
            print(f"УСПЕХ: Миграция завершена! Мигрировано {migrated_count} продуктов.")
        else:
            print("ПРЕДУПРЕЖДЕНИЕ: Ни один продукт не был мигрирован")
            
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
