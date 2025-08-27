#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
    print("🔄 Импортируем enhanced_llm...")
    from enhanced_llm import enhanced_llm
    print("✅ Импорт успешен")
    
    print("🔄 Тестируем Румарин Экстра...")
    answer = enhanced_llm.process_query('Для чего применяют Румарин Экстра')
    
    print(f"📏 Длина ответа: {len(answer)} символов")
    print(f"🔍 Больше 900: {len(answer) > 900}")
    
    # Показываем начало и конец
    print(f"📝 Начало: {answer[:100]}...")
    print(f"📝 Конец: ...{answer[-100:]}")
    
    # Сохраняем
    with open('rumarin_test_result.txt', 'w', encoding='utf-8') as f:
        f.write(f"Длина: {len(answer)} символов\n")
        f.write(f"Больше 900: {len(answer) > 900}\n\n")
        f.write(answer)
    
    print("✅ Тест завершен, результат в rumarin_test_result.txt")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
except Exception as e:
    print(f"❌ Общая ошибка: {e}")
    import traceback
    traceback.print_exc()





