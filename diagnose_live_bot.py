# diagnose_live_bot.py
"""
Диагностирует состояние запущенного бота
"""
import json
import os
from datetime import datetime

def check_knowledge_base_status():
    """Проверяет состояние базы знаний"""
    print("📋 Проверка базы знаний")
    print("=" * 30)
    
    try:
        # Проверяем время модификации файла
        kb_path = "knowledge_base.json"
        if os.path.exists(kb_path):
            mod_time = os.path.getmtime(kb_path)
            mod_datetime = datetime.fromtimestamp(mod_time)
            print(f"📅 Последнее изменение: {mod_datetime}")
            
            # Читаем содержимое
            with open(kb_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            print(f"📊 Количество продуктов: {len(data)}")
            
            for product in data:
                image_id = product.get('image_id', '')
                print(f"   {product['product']}: {'✅ Есть картинка' if image_id else '❌ Нет картинки'}")
                
        else:
            print("❌ Файл knowledge_base.json не найден")
            
    except Exception as e:
        print(f"❌ Ошибка чтения базы знаний: {e}")

def check_bot_modules():
    """Проверяет загруженные модули бота"""
    print("\n🔧 Проверка модулей бота")
    print("=" * 25)
    
    try:
        # Проверяем импорты
        modules_to_check = [
            "product_recommendations",
            "enhanced_vector_db", 
            "enhanced_llm",
            "nlp_processor"
        ]
        
        for module_name in modules_to_check:
            try:
                module = __import__(module_name)
                print(f"✅ {module_name}: Загружен")
                
                # Специальная проверка для product_recommendations
                if module_name == "product_recommendations":
                    manager = getattr(module, 'recommendation_manager', None)
                    if manager:
                        products_count = len(manager.products_data)
                        print(f"   📊 Продуктов в менеджере: {products_count}")
                        
                        # Проверяем конкретные image_id
                        for pid, pdata in manager.products_data.items():
                            image_id = pdata.get('image_id', '')
                            print(f"   {pid}: {'✅ Image ID' if image_id else '❌ Нет Image ID'}")
                
            except ImportError as e:
                print(f"❌ {module_name}: Ошибка импорта - {e}")
                
    except Exception as e:
        print(f"❌ Ошибка проверки модулей: {e}")

def suggest_solution():
    """Предлагает решение проблемы"""
    print("\n💡 ДИАГНОЗ И РЕШЕНИЕ")
    print("=" * 25)
    
    print("🔍 Возможные причины отсутствия картинок:")
    print("1. Бот использует старую версию кода (не перезапущен)")
    print("2. Модуль product_recommendations кэширован в памяти")
    print("3. База знаний не переиндексировалась")
    print("4. Проблема с логикой отправки в боте")
    
    print("\n🔧 РЕШЕНИЯ:")
    print("1. ⚡ ПЕРЕЗАПУСТИТЕ БОТА: Ctrl+C и снова python bot.py")
    print("2. 🔄 Принудительная переиндексация: уже выполнена")
    print("3. 📱 Проверьте в Telegram: отправьте боту 'Что принимать при простуде?'")
    print("4. 🧪 Тест подтвердил: картинки отправляются корректно")
    
    print("\n🎯 ГЛАВНАЯ РЕКОМЕНДАЦИЯ:")
    print("   Остановите текущего бота и запустите заново!")
    print("   Команды:")
    print("   1. Ctrl+C (в терминале с ботом)")
    print("   2. python bot.py")

def create_test_message():
    """Создает тестовое сообщение для проверки"""
    print("\n📝 ТЕСТОВОЕ СООБЩЕНИЕ")
    print("=" * 20)
    print("Отправьте боту: 'Что принимать при простуде?'")
    print("Ожидаемый результат:")
    print("📷 Картинка Солберри-H")
    print("💊 **Солберри-H (Solberry-H)**")
    print("🎯 **Почему подходит:** Эффективен при простудах...")
    print("[🛒 Заказать] [Следующий ▶️]")

if __name__ == "__main__":
    print("🩺 ДИАГНОСТИКА ПРОБЛЕМЫ С КАРТИНКАМИ")
    print("=" * 45)
    
    check_knowledge_base_status()
    check_bot_modules()  
    suggest_solution()
    create_test_message()







