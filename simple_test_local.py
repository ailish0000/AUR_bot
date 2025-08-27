import os
import json

print("🧪 ПРОСТОЙ ТЕСТ ЛОКАЛЬНОГО ЛОГИРОВАНИЯ")
print("=" * 45)

# Проверяем модуль
try:
    from local_logger import log_user_question_local
    print("✅ Модуль local_logger импортирован")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    exit(1)

# Тестируем запись
print("\n📝 Тестирование записи...")

test_question = "Тестовый вопрос для проверки локального логирования"
user_id = 123456789
username = "test_user"

print(f"Записываем: '{test_question}'")
log_user_question_local(user_id, username, test_question)

# Проверяем файл
json_file = "user_questions.json"
if os.path.exists(json_file):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ JSON файл создан, записей: {len(data)}")
        
        if data:
            last_record = data[-1]
            print(f"📋 Последняя запись:")
            print(f"   Время: {last_record['timestamp']}")
            print(f"   Пользователь: {last_record['username']}")
            print(f"   Вопрос: {last_record['question']}")
            
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
else:
    print("❌ JSON файл не найден")

print("\n🎉 Тест завершен!")












