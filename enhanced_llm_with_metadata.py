#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Создаем копию enhanced_llm.py с интеграцией умного поиска
import shutil
import os

# Копируем оригинальный файл
if os.path.exists('enhanced_llm.py'):
    shutil.copy('enhanced_llm.py', 'enhanced_llm_backup.py')
    print("✅ Создана резервная копия enhanced_llm.py")

print("🔧 Теперь будем модифицировать enhanced_llm.py для интеграции умного поиска")





