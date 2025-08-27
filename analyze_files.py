#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

def check_file_content(file_path):
    """Проверяет содержимое файла на признаки другого проекта"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Признаки другого проекта Aurora
        other_project_indicators = [
            # Другие названия ботов
            'aurora assistant',
            'aurora helper',
            'aurora support',
            # Другие функциональности
            'order',
            'заказ',
            'payment',
            'оплата',
            'delivery',
            'доставка',
            'shipping',
            'cart',
            'корзина',
            # Другие технологии
            'django',
            'flask',
            'fastapi',
            'sqlalchemy',
            'postgresql',
            'mysql',
            # Другие сервисы
            'stripe',
            'paypal',
            'yandex.money',
            'qiwi',
            # Другие API
            'telegram bot api',
            'botfather',
            # Другие структуры
            'models.py',
            'views.py',
            'urls.py',
            'settings.py',
            'admin.py',
            'forms.py',
            'serializers.py',
            # Другие файлы конфигурации
            'dockerfile',
            'docker-compose',
            'kubernetes',
            'helm',
            # Другие тесты
            'pytest',
            'unittest',
            'test_',
            'spec_',
            # Другие документы
            'api.md',
            'deployment.md',
            'architecture.md',
            'design.md'
        ]
        
        content_lower = content.lower()
        for indicator in other_project_indicators:
            if indicator in content_lower:
                return True
        
        return False
        
    except Exception as e:
        print(f"Ошибка чтения {file_path}: {e}")
        return False

def check_filename_suspicious(file_path):
    """Проверяет подозрительные имена файлов"""
    filename = os.path.basename(file_path).lower()
    
    suspicious_patterns = [
        # Другие проекты
        'shop',
        'store',
        'ecommerce',
        'marketplace',
        'order',
        'payment',
        'delivery',
        'cart',
        'checkout',
        'billing',
        # Другие боты
        'assistant',
        'helper',
        'support',
        'chatbot',
        # Другие технологии
        'django',
        'flask',
        'fastapi',
        'react',
        'vue',
        'angular',
        # Другие сервисы
        'stripe',
        'paypal',
        'yandex',
        'qiwi',
        # Другие конфигурации
        'docker',
        'kubernetes',
        'helm',
        'terraform',
        'ansible',
        # Другие тесты
        'spec_',
        'test_',
        'unit_',
        'integration_',
        'e2e_',
        # Другие документы
        'api_',
        'deployment_',
        'architecture_',
        'design_',
        'specification_'
    ]
    
    for pattern in suspicious_patterns:
        if pattern in filename:
            return True
    
    return False

def analyze_project():
    """Анализирует весь проект"""
    print("🔍 АНАЛИЗ ПРОЕКТА НА ПРЕДМЕТ ЧУЖИХ ФАЙЛОВ")
    print("=" * 60)
    
    suspicious_files = []
    normal_files = []
    
    # Получаем список всех файлов
    for root, dirs, files in os.walk('.'):
        # Пропускаем .git и __pycache__
        if '.git' in root or '__pycache__' in root:
            continue
            
        for file in files:
            file_path = os.path.join(root, file)
            
            # Пропускаем бинарные файлы
            if file.endswith(('.db', '.pyc', '.exe', '.dll', '.so')):
                continue
                
            # Проверяем подозрительность
            is_suspicious = check_filename_suspicious(file_path) or check_file_content(file_path)
            
            if is_suspicious:
                suspicious_files.append(file_path)
            else:
                normal_files.append(file_path)
    
    print(f"✅ Нормальные файлы: {len(normal_files)}")
    print(f"❌ Подозрительные файлы: {len(suspicious_files)}")
    
    print("\n📁 ПОДОЗРИТЕЛЬНЫЕ ФАЙЛЫ (возможно из другого проекта):")
    print("-" * 60)
    
    # Группируем по расширениям
    extensions = {}
    for file_path in suspicious_files:
        ext = os.path.splitext(file_path)[1]
        if ext not in extensions:
            extensions[ext] = []
        extensions[ext].append(file_path)
    
    for ext, files in sorted(extensions.items()):
        print(f"\n{ext.upper()} файлы ({len(files)}):")
        for file_path in sorted(files):
            print(f"  - {file_path}")
    
    return suspicious_files

if __name__ == "__main__":
    suspicious_files = analyze_project()
    
    print(f"\n" + "=" * 60)
    print(f"📊 ИТОГО: {len(suspicious_files)} подозрительных файлов")
    print("Эти файлы могут быть из другого проекта Aurora!")
