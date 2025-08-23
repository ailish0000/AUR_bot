#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для автоматического создания кратких описаний
Генерирует short_description и short_benefits из полных описаний
"""

import json
import re
from typing import List, Dict, Any

def clean_text(text: str) -> str:
    """Очищает текст от лишних символов"""
    # Убираем множественные пробелы
    text = re.sub(r'\s+', ' ', text)
    # Убираем пробелы в начале и конце
    text = text.strip()
    return text

def extract_main_benefits(benefits: List[str], max_count: int = 3) -> List[str]:
    """Извлекает основные показания из полного списка"""
    if not benefits:
        return []
    
    # Сортируем по важности (короткие и информативные сначала)
    sorted_benefits = sorted(benefits, key=lambda x: (len(x), x))
    
    # Берем первые max_count
    main_benefits = sorted_benefits[:max_count]
    
    # Сокращаем длинные формулировки
    shortened_benefits = []
    for benefit in main_benefits:
        # Убираем лишние слова
        benefit = re.sub(r'^помощь при\s+', '', benefit)
        benefit = re.sub(r'^используется при\s+', '', benefit)
        benefit = re.sub(r'^обладает\s+', '', benefit)
        benefit = re.sub(r'^профилактика\s+', '', benefit)
        
        # Сокращаем до 50 символов
        if len(benefit) > 50:
            benefit = benefit[:47] + "..."
        
        shortened_benefits.append(benefit)
    
    return shortened_benefits

def create_short_description(description: str, max_length: int = 150) -> str:
    """Создает краткое описание из полного"""
    if not description:
        return ""
    
    # Очищаем текст
    clean_desc = clean_text(description)
    
    # Если описание уже короткое, возвращаем как есть
    if len(clean_desc) <= max_length:
        return clean_desc
    
    # Разбиваем на предложения
    sentences = re.split(r'[.!?]+', clean_desc)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return clean_desc[:max_length]
    
    # Берем первое предложение
    short_desc = sentences[0]
    
    # Если первое предложение слишком длинное, обрезаем
    if len(short_desc) > max_length:
        # Ищем место для обрезки (после запятой или пробела)
        words = short_desc.split()
        current = ""
        for word in words:
            if len(current + " " + word) <= max_length - 3:
                current += (" " + word) if current else word
            else:
                break
        
        short_desc = current + "..."
    
    # Если первое предложение короткое, добавляем второе
    elif len(sentences) > 1 and len(short_desc) < max_length // 2:
        second_sentence = sentences[1]
        combined = short_desc + ". " + second_sentence
        
        if len(combined) <= max_length:
            short_desc = combined
        else:
            # Обрезаем второе предложение
            remaining = max_length - len(short_desc) - 3  # ". " + "..."
            if remaining > 0:
                short_desc = short_desc + ". " + second_sentence[:remaining] + "..."
    
    return short_desc

def process_product(product: Dict[str, Any]) -> Dict[str, Any]:
    """Обрабатывает один продукт, добавляя краткие описания"""
    result = product.copy()
    
    # Создаем краткое описание
    if "description" in product and "short_description" not in product:
        short_desc = create_short_description(product["description"])
        result["short_description"] = short_desc
        print(f"✅ Добавлено краткое описание для {product['product']}: {short_desc[:50]}...")
    
    # Создаем краткие показания
    if "benefits" in product and "short_benefits" not in product:
        short_benefits = extract_main_benefits(product["benefits"])
        result["short_benefits"] = short_benefits
        print(f"✅ Добавлены краткие показания для {product['product']}: {short_benefits}")
    
    return result

def generate_short_descriptions(input_file: str = "knowledge_base.json", 
                              output_file: str = "knowledge_base_updated.json"):
    """Генерирует краткие описания для всех товаров"""
    
    print("🔄 Генерация кратких описаний...")
    
    # Загружаем данные
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            products = json.load(f)
    except FileNotFoundError:
        print(f"❌ Файл {input_file} не найден")
        return
    except json.JSONDecodeError:
        print(f"❌ Ошибка чтения JSON файла {input_file}")
        return
    
    print(f"📦 Найдено {len(products)} товаров")
    
    # Обрабатываем каждый товар
    updated_products = []
    updated_count = 0
    
    for product in products:
        original_keys = set(product.keys())
        updated_product = process_product(product)
        updated_keys = set(updated_product.keys())
        
        if updated_keys != original_keys:
            updated_count += 1
        
        updated_products.append(updated_product)
    
    # Сохраняем результат
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(updated_products, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Обновлено {updated_count} товаров")
        print(f"📁 Результат сохранен в {output_file}")
        
        # Показываем статистику
        print("\n📊 Статистика:")
        for product in updated_products:
            if "short_description" in product:
                desc_len = len(product["short_description"])
                full_len = len(product.get("description", ""))
                reduction = ((full_len - desc_len) / full_len * 100) if full_len > 0 else 0
                print(f"   {product['product']}: {desc_len}/{full_len} символов ({reduction:.1f}% сокращение)")
        
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")

def backup_original_file(filename: str = "knowledge_base.json"):
    """Создает резервную копию оригинального файла"""
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{filename}.backup_{timestamp}"
    
    try:
        shutil.copy2(filename, backup_name)
        print(f"💾 Создана резервная копия: {backup_name}")
        return backup_name
    except Exception as e:
        print(f"⚠️ Не удалось создать резервную копию: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Генератор кратких описаний товаров")
    print("=" * 50)
    
    # Создаем резервную копию
    backup_file = backup_original_file()
    
    # Генерируем краткие описания
    generate_short_descriptions()
    
    print("\n🎉 Генерация завершена!")
    print("\n📝 Следующие шаги:")
    print("1. Проверьте файл knowledge_base_updated.json")
    print("2. Если результат устраивает, замените knowledge_base.json")
    print("3. Запустите тест: python test_short_descriptions.py")






