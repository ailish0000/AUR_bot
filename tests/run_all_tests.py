#!/usr/bin/env python3
"""
Главный скрипт для запуска всех автотестов бота Aurora
"""

import sys
import os
import asyncio
import argparse
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_framework import BotTestFramework
from test_nlp_processor import create_nlp_tests
from test_product_search import create_product_search_tests  
from test_llm_responses import create_llm_tests
from test_user_interactions import create_user_interaction_tests
from test_regression import create_regression_tests

class TestRunner:
    """Главный класс для запуска всех тестов"""
    
    def __init__(self):
        self.framework = BotTestFramework()
        self.test_modules = []
        
    def setup_all_tests(self):
        """Настройка всех тестовых модулей"""
        print("🔧 Настройка тестовых модулей...")
        
        # Регистрируем все тесты
        self.test_modules = [
            ("NLP Processor", create_nlp_tests(self.framework)),
            ("Product Search", create_product_search_tests(self.framework)),
            ("LLM Responses", create_llm_tests(self.framework)),
            ("User Interactions", create_user_interaction_tests(self.framework)),
            ("Regression Tests", create_regression_tests(self.framework))
        ]
        
        print(f"✅ Зарегистрировано {len(self.framework.test_cases)} тестов в {len(self.test_modules)} модулях")
        
        # Показываем статистику по категориям
        categories = {}
        priorities = {}
        
        for test in self.framework.test_cases:
            cat = test.category
            prio = test.priority
            
            categories[cat] = categories.get(cat, 0) + 1
            priorities[prio] = priorities.get(prio, 0) + 1
        
        print("\n📊 Статистика тестов:")
        print("   По категориям:")
        for cat, count in sorted(categories.items()):
            print(f"      {cat}: {count}")
        
        print("   По приоритетам:")
        for prio, count in sorted(priorities.items()):
            icon = {"critical": "🚨", "high": "⚡", "medium": "📋", "low": "📝"}.get(prio, "❓")
            print(f"      {icon} {prio}: {count}")
    
    async def run_tests(self, categories=None, priorities=None, include_regression=True):
        """Запуск тестов с фильтрацией"""
        
        # Фильтр по умолчанию
        if not categories and not priorities:
            if include_regression:
                # Все тесты включая регрессионные
                pass  # Без фильтров
            else:
                # Исключаем регрессионные тесты
                categories = [cat for cat in ["nlp_intents", "nlp_entities", "nlp_sentiment", 
                                             "product_search", "product_extraction",
                                             "llm_quality", "llm_safety", "llm_technical", 
                                             "llm_formatting", "llm_product_knowledge", "llm_links",
                                             "bot_commands", "dialog_scenarios", "context_management", "error_handling"]
                            if "regression" not in cat]
        
        print(f"\n🚀 Запуск тестов...")
        if categories:
            print(f"   Категории: {', '.join(categories)}")
        if priorities:
            print(f"   Приоритеты: {', '.join(priorities)}")
        
        start_time = datetime.now()
        
        # Запускаем тесты
        results = await self.framework.run_all_tests(categories, priorities)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n⏱️ Тесты завершены за {duration:.2f} секунд")
        
        return results
    
    def analyze_results(self, results):
        """Анализ результатов тестирования"""
        if not results:
            print("❌ Результаты тестирования отсутствуют")
            return
        
        # Общая статистика
        total = len(results)
        passed = len([r for r in results if r.result.value == "PASS"])
        failed = len([r for r in results if r.result.value == "FAIL"])
        
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"\n📈 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"   Всего тестов: {total}")
        print(f"   ✅ Пройдено: {passed}")
        print(f"   ❌ Провалено: {failed}")
        print(f"   🎯 Успешность: {success_rate:.1f}%")
        
        # Анализ критических проблем
        critical_failures = [r for r in results if r.test_case.priority == "critical" and r.result.value == "FAIL"]
        if critical_failures:
            print(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ({len(critical_failures)}):")
            for result in critical_failures:
                print(f"   ❌ {result.test_case.name}")
                print(f"      {result.message}")
        
        # Анализ регрессий
        regression_failures = [r for r in results if "regression" in r.test_case.category and r.result.value == "FAIL"]
        if regression_failures:
            print(f"\n🐛 РЕГРЕССИИ ({len(regression_failures)}):")
            for result in regression_failures:
                print(f"   ❌ {result.test_case.name}")
                print(f"      {result.message}")
        
        # Рекомендации
        if critical_failures or regression_failures:
            print(f"\n💡 РЕКОМЕНДАЦИИ:")
            if critical_failures:
                print("   🚨 Немедленно исправьте критические проблемы!")
            if regression_failures:
                print("   🐛 Проверьте регрессии - возможно нарушена работа бота!")
            print("   📋 Запустите тесты повторно после исправлений")
        else:
            print(f"\n🎉 ОТЛИЧНО! Все критические тесты пройдены!")
            if success_rate >= 95:
                print("   🏆 Качество кода превосходное!")
            elif success_rate >= 90:
                print("   ✨ Качество кода отличное!")
            elif success_rate >= 80:
                print("   👍 Качество кода хорошее, есть что улучшить")
            else:
                print("   ⚠️ Качество кода требует внимания")
    
    def generate_reports(self, results, save_to_file=True):
        """Генерация отчетов"""
        if save_to_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Полный отчет
            full_report_name = f"full_test_report_{timestamp}.txt"
            self.framework.save_report(full_report_name)
            print(f"\n📄 Полный отчет сохранен: {full_report_name}")
            
            # Краткий отчет с только провалившимися тестами
            failed_results = [r for r in results if r.result.value == "FAIL"]
            if failed_results:
                failures_report = f"failures_report_{timestamp}.txt"
                with open(failures_report, 'w', encoding='utf-8') as f:
                    f.write("🚨 ОТЧЕТ О ПРОВАЛИВШИХСЯ ТЕСТАХ\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for result in failed_results:
                        f.write(f"❌ {result.test_case.name}\n")
                        f.write(f"   Категория: {result.test_case.category}\n")
                        f.write(f"   Приоритет: {result.test_case.priority}\n")
                        f.write(f"   Описание: {result.test_case.description}\n")
                        f.write(f"   Ошибка: {result.message}\n")
                        if result.error_details:
                            f.write(f"   Детали: {result.error_details}\n")
                        f.write("\n" + "-" * 40 + "\n\n")
                
                print(f"🔴 Отчет о провалах сохранен: {failures_report}")
        
        return self.framework.generate_report()

async def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description="Автотесты для бота Aurora")
    parser.add_argument("--categories", nargs="*", help="Категории тестов для запуска")
    parser.add_argument("--priorities", nargs="*", help="Приоритеты тестов (critical, high, medium, low)")
    parser.add_argument("--no-regression", action="store_true", help="Исключить regression тесты")
    parser.add_argument("--only-critical", action="store_true", help="Только критические тесты")
    parser.add_argument("--only-regression", action="store_true", help="Только regression тесты")
    parser.add_argument("--no-reports", action="store_true", help="Не сохранять отчеты в файлы")
    
    args = parser.parse_args()
    
    print("🧪 СИСТЕМА АВТОТЕСТОВ БОТА AURORA")
    print("=" * 50)
    
    runner = TestRunner()
    runner.setup_all_tests()
    
    # Настройка фильтров
    categories = args.categories
    priorities = args.priorities
    include_regression = not args.no_regression
    
    if args.only_critical:
        priorities = ["critical"]
    
    if args.only_regression:
        categories = ["critical_regression", "technical_regression", "scenario_regression", "regression"]
    
    # Запуск тестов
    try:
        results = await runner.run_tests(categories, priorities, include_regression)
        
        # Анализ и отчеты
        runner.analyze_results(results)
        
        if not args.no_reports:
            runner.generate_reports(results)
        
        # Код возврата для CI/CD
        failed_count = len([r for r in results if r.result.value == "FAIL"])
        critical_failures = len([r for r in results if r.test_case.priority == "critical" and r.result.value == "FAIL"])
        
        if critical_failures > 0:
            print(f"\n🚨 КРИТИЧЕСКИЕ ТЕСТЫ ПРОВАЛИЛИСЬ - КОД ВОЗВРАТА 2")
            return 2
        elif failed_count > 0:
            print(f"\n⚠️ ЕСТЬ ПРОВАЛИВШИЕСЯ ТЕСТЫ - КОД ВОЗВРАТА 1")
            return 1
        else:
            print(f"\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ - КОД ВОЗВРАТА 0")
            return 0
            
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА ТЕСТИРОВАНИЯ: {e}")
        import traceback
        traceback.print_exc()
        return 3

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Непредвиденная ошибка: {e}")
        sys.exit(1)

