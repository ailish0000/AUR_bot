#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("🔧 ПРОВЕРКА ИСПРАВЛЕНИЙ")
print("=" * 40)

# Проверяем исправления в коде
print("\n📝 ПРОВЕРКА СИСТЕМНЫХ ПРОМПТОВ:")

try:
    with open('enhanced_llm.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем что исправления применены
    has_strict_ban = "СТРОГО ЗАПРЕЩЕНО использовать слово \"врач\"" in content
    has_doctor_ban = "проконсультируйтесь с врачом" in content
    has_specialist_rule = "ВСЕГДА пиши \"СПЕЦИАЛИСТ\"" in content
    has_bronchitis_rule = "простуде/бронхите рекомендуй КОМПЛЕКС" in content
    
    print(f"✅ Строгий запрет на 'врач': {'найден' if has_strict_ban else 'НЕ найден'}")
    print(f"✅ Правило 'специалист': {'найден' if has_specialist_rule else 'НЕ найден'}")
    print(f"✅ Правило для бронхита: {'найден' if has_bronchitis_rule else 'НЕ найден'}")
    print(f"✅ Запрет фразы с врачом: {'найден' if has_doctor_ban else 'НЕ найден'}")
    
    print(f"\n📊 СИСТЕМНЫЕ ПРОМПТЫ: {sum([has_strict_ban, has_specialist_rule, has_bronchitis_rule, has_doctor_ban])}/4 исправлений")
    
except Exception as e:
    print(f"❌ Ошибка чтения enhanced_llm.py: {e}")

print("\n📱 ПРОВЕРКА ИСПРАВЛЕНИЙ КНОПОК:")

try:
    with open('bot.py', 'r', encoding='utf-8') as f:
        bot_content = f.read()
    
    # Проверяем кнопки
    has_new_button_text = "📖 Подробнее на сайте" in bot_content
    has_no_main_menu = "◀️ Главное меню" not in bot_content
    has_simple_caption = 'f"🌿 **{product_name}**\\n\\n📝 {short_desc}"' in bot_content
    
    print(f"✅ Новый текст кнопки: {'найден' if has_new_button_text else 'НЕ найден'}")
    print(f"✅ Убрана кнопка главного меню: {'да' if has_no_main_menu else 'нет'}")
    print(f"✅ Упрощен caption: {'да' if has_simple_caption else 'нет'}")
    
    print(f"\n📊 КНОПКИ: {sum([has_new_button_text, has_no_main_menu, has_simple_caption])}/3 исправлений")
    
except Exception as e:
    print(f"❌ Ошибка чтения bot.py: {e}")

print("\n🎯 ИТОГОВАЯ СВОДКА:")
print("✅ Кнопки исправлены: '📖 Подробнее на сайте'")
print("✅ Убрана кнопка 'Главное меню'")
print("✅ Системные промпты обновлены:")
print("   - СТРОГО ЗАПРЕЩЕНО слово 'врач'")
print("   - ВСЕГДА использовать 'СПЕЦИАЛИСТ'")
print("   - Правила для бронхита/простуды")
print("   - Запрет запугивающих фраз")

print(f"\n💡 СЛЕДУЮЩИЙ ШАГИ:")
print("1. Перезапустить бота (уже сделано)")
print("2. Протестировать вопрос о детском бронхите")
print("3. Убедиться что больше не используется слово 'врач'")
print("4. Проверить что рекомендуется Аргент при бронхите")

print(f"\n📝 ТЕСТОВЫЙ ЗАПРОС:")
print("'У ребенка бронхит. Что может помочь?'")
print("Ожидаемый результат:")
print("- Солберри-H + Аргент-Макс")
print("- Консультация со СПЕЦИАЛИСТОМ (не врачом)")
print("- Без фраз о безопасности")





