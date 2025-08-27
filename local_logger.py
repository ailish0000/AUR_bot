# local_logger.py
"""
Альтернативный локальный логгер для вопросов пользователей
Используется, если Google Sheets недоступен
"""
import os
import json
from datetime import datetime
from typing import Dict, List

class LocalQuestionLogger:
    def __init__(self, log_file: str = "user_questions.json"):
        self.log_file = log_file
        self.questions = self._load_existing_questions()
    
    def _load_existing_questions(self) -> List[Dict]:
        """Загружает существующие вопросы из файла"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Ошибка загрузки файла логов: {e}")
                return []
        return []
    
    def log_question(self, user_id: int, username: str, question: str) -> bool:
        """Логирует вопрос пользователя в локальный файл"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            question_data = {
                "timestamp": timestamp,
                "user_id": user_id,
                "username": username or "Unknown",
                "question": question
            }
            
            self.questions.append(question_data)
            
            # Сохраняем в файл
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.questions, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Вопрос сохранен локально: {question[:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка локального логирования: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Возвращает статистику по вопросам"""
        if not self.questions:
            return {"total": 0, "users": 0}
        
        unique_users = len(set(q["user_id"] for q in self.questions))
        return {
            "total": len(self.questions),
            "users": unique_users,
            "latest": self.questions[-1]["timestamp"] if self.questions else None
        }
    
    def export_to_csv(self, csv_file: str = "user_questions.csv") -> bool:
        """Экспортирует вопросы в CSV файл"""
        try:
            import csv
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "User ID", "Username", "Question"])
                
                for q in self.questions:
                    writer.writerow([
                        q["timestamp"],
                        q["user_id"],
                        q["username"],
                        q["question"]
                    ])
            
            print(f"✅ Данные экспортированы в {csv_file}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка экспорта в CSV: {e}")
            return False

# Глобальный экземпляр
local_logger = LocalQuestionLogger()

# Функция для использования в боте
def log_user_question_local(user_id: int, username: str, question: str) -> None:
    """Логирует вопрос пользователя локально"""
    try:
        local_logger.log_question(user_id, username, question)
    except Exception as e:
        print(f"⚠️ Ошибка локального логирования: {e}")

# Функция для получения статистики
def get_questions_statistics() -> Dict:
    """Возвращает статистику по вопросам"""
    return local_logger.get_statistics()

# Функция для экспорта в CSV
def export_questions_to_csv(csv_file: str = "user_questions.csv") -> bool:
    """Экспортирует вопросы в CSV файл"""
    return local_logger.export_to_csv(csv_file)

if __name__ == "__main__":
    # Тестирование
    print("🧪 ТЕСТИРОВАНИЕ ЛОКАЛЬНОГО ЛОГГЕРА")
    print("=" * 40)
    
    # Тестовые вопросы
    test_questions = [
        (123456789, "test_user1", "Что помогает от простуды?"),
        (987654321, "test_user2", "Как зарегистрироваться?"),
        (555666777, "test_user3", "Подскажите продукты для печени")
    ]
    
    for user_id, username, question in test_questions:
        success = local_logger.log_question(user_id, username, question)
        print(f"Вопрос '{question[:30]}...': {'✅' if success else '❌'}")
    
    # Статистика
    stats = local_logger.get_statistics()
    print(f"\n📊 Статистика:")
    print(f"   Всего вопросов: {stats['total']}")
    print(f"   Уникальных пользователей: {stats['users']}")
    print(f"   Последний вопрос: {stats['latest']}")
    
    # Экспорт в CSV
    export_success = local_logger.export_to_csv()
    print(f"   Экспорт в CSV: {'✅' if export_success else '❌'}")
    
    print("\n🎉 Тестирование завершено!")












