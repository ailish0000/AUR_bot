# google_sheets.py
"""
Модуль для интеграции с Google Sheets
Сохраняет вопросы пользователей для анализа и улучшения бота
"""
import os
import asyncio
from datetime import datetime
from typing import Optional
import aiohttp
import json
from dotenv import load_dotenv

load_dotenv()

class GoogleSheetsLogger:
    def __init__(self):
        self.sheet_id = "1d9O9TOEUe0iUtN08HOBAIG_F3HV1qP5kfjHpt3gJLDc"
        self.api_key = os.getenv("GOOGLE_SHEETS_API_KEY")
        self.base_url = "https://sheets.googleapis.com/v4/spreadsheets"
        self.range_name = "Лист1!A:A"  # Колонка A
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            print("⚠️ GOOGLE_SHEETS_API_KEY не найден. Логирование в Google Sheets отключено.")
    
    async def log_question(self, user_id: int, username: str, question: str) -> bool:
        """
        Добавляет вопрос пользователя в Google таблицу
        
        Args:
            user_id: ID пользователя Telegram
            username: Имя пользователя
            question: Текст вопроса
            
        Returns:
            bool: True если успешно добавлено, False если ошибка
        """
        if not self.enabled:
            return False
            
        try:
            # Формируем строку для записи
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} | {username or 'Unknown'} ({user_id}) | {question}"
            
            # Используем append для добавления в конец таблицы
            success = await self._append_to_sheet(log_entry)
            
            if success:
                print(f"✅ Вопрос сохранен в Google Sheets: {question[:50]}...")
            else:
                print(f"❌ Ошибка сохранения в Google Sheets: {question[:50]}...")
                
            return success
            
        except Exception as e:
            print(f"❌ Ошибка Google Sheets API: {e}")
            return False
    
    async def _append_to_sheet(self, value: str) -> bool:
        """Добавляет значение в конец таблицы"""
        try:
            # Используем append endpoint для добавления в конец
            url = f"{self.base_url}/{self.sheet_id}/values/A1:append?valueInputOption=RAW&key={self.api_key}"
            
            data = {
                "values": [[value]]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        return True
                    else:
                        response_text = await response.text()
                        print(f"❌ Ошибка записи в Google Sheets: {response.status} - {response_text}")
                        return False
                        
        except Exception as e:
            print(f"❌ Ошибка записи: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Тестирует подключение к Google Sheets API"""
        if not self.enabled:
            print("❌ Google Sheets API не настроен")
            return False
            
        try:
            url = f"{self.base_url}/{self.sheet_id}/values/A1?key={self.api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Google Sheets подключен. Заголовок: {data.get('values', [['Нет данных']])[0][0]}")
                        return True
                    else:
                        print(f"❌ Ошибка подключения: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Ошибка тестирования: {e}")
            return False

# Глобальный экземпляр
google_sheets_logger = GoogleSheetsLogger()

# Асинхронная функция-обертка для использования в боте
async def log_user_question(user_id: int, username: str, question: str) -> None:
    """
    Логирует вопрос пользователя в Google Sheets асинхронно
    
    Args:
        user_id: ID пользователя
        username: Имя пользователя
        question: Текст вопроса
    """
    try:
        await google_sheets_logger.log_question(user_id, username, question)
    except Exception as e:
        # Не прерываем работу бота из-за ошибок логирования
        print(f"⚠️ Ошибка логирования в Google Sheets: {e}")

# Функция для тестирования (можно вызвать отдельно)
async def test_google_sheets():
    """Тестирует работу с Google Sheets"""
    print("🧪 ТЕСТИРОВАНИЕ GOOGLE SHEETS")
    print("=" * 30)
    
    # Тест подключения
    connection_ok = await google_sheets_logger.test_connection()
    
    if connection_ok:
        # Тест записи
        test_question = f"Тестовый вопрос - {datetime.now().strftime('%H:%M:%S')}"
        success = await google_sheets_logger.log_question(
            user_id=123456789,
            username="test_user",
            question=test_question
        )
        
        if success:
            print("✅ Тестовая запись успешна")
        else:
            print("❌ Ошибка тестовой записи")
            
        return success
    else:
        print("❌ Подключение не установлено")
        return False

if __name__ == "__main__":
    # Прямой вызов для тестирования
    asyncio.run(test_google_sheets())
