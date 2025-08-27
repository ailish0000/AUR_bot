# 🧠 Интеграция контекстной системы в Aurora Bot

## 📋 Обзор системы

Контекстная система превращает Aurora Bot в **интеллектуального консультанта**, который:
- 🧠 **Помнит историю диалога** с каждым пользователем
- 🎯 **Понимает контекст** и связи между вопросами
- 🎪 **Персонализирует рекомендации** на основе предпочтений
- 🔄 **Ведет диалог** с уточняющими вопросами
- 📈 **Анализирует намерения** и готовность к покупке

## 🏗️ Архитектура системы

### Основные компоненты:

1. **`conversation_memory.py`** - Система памяти диалогов
2. **`context_analyzer.py`** - Анализатор контекста и связей
3. **`personalized_recommendations.py`** - Персонализированные рекомендации
4. **`conversation_flow.py`** - Управление потоком диалога
5. **`contextual_bot_integration.py`** - Интеграционный слой

## 🚀 Интеграция в существующий bot.py

### Шаг 1: Импорт контекстной системы

Добавьте в начало `bot.py`:

```python
from contextual_bot_integration import contextual_integration
```

### Шаг 2: Модификация handle_message

Замените основную логику в `handle_message`:

```python
async def handle_message(message: types.Message):
    user_id = str(message.from_user.id)
    user_message = message.text
    
    try:
        # Обрабатываем через контекстную систему
        context_result = contextual_integration.process_user_message(
            user_id, user_message
        )
        
        # Получаем контекстный промпт
        contextual_prompt = context_result.get('contextual_prompt', user_message)
        
        # Проверяем, нужно ли задать уточняющий вопрос
        if context_result.get('should_ask_clarifying_question', False):
            guidance = context_result.get('conversation_guidance', {})
            clarifying_question = guidance.get('recommended_action', {}).get('content', '')
            
            if clarifying_question:
                await message.reply(clarifying_question)
                return
        
        # Стандартная обработка с контекстным промптом
        intent = nlp_processor.analyze_intent(user_message)
        response = await llm.process_query(contextual_prompt, intent)
        
        # Извлекаем продукты
        found_products = extract_products_from_answer(response)
        
        # Улучшаем ответ через контекстную систему
        enhancement = contextual_integration.enhance_bot_response(
            user_id, response, found_products
        )
        
        enhanced_response = enhancement.get('enhanced_response', response)
        
        # Отправляем улучшенный ответ
        await message.reply(enhanced_response, parse_mode='Markdown')
        
        # Добавляем предложения для продолжения диалога
        follow_ups = enhancement.get('follow_up_suggestions', [])
        if follow_ups:
            await asyncio.sleep(1)
            await message.reply(f"💡 {follow_ups[0]}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_message: {e}")
        await message.reply("Извините, произошла ошибка. Попробуйте еще раз.")
```

### Шаг 3: Модификация handle_product_selection

```python
async def handle_product_selection(message: types.Message):
    user_id = str(message.from_user.id)
    selection = message.text
    
    try:
        # Обрабатываем выбор через контекстную систему
        selection_result = contextual_integration.handle_product_selection(
            user_id, selection
        )
        
        # Генерируем ответ с учетом контекста
        response = f"🌿 {selection}\n\nОтличный выбор!"
        
        # Добавляем персонализированную информацию
        if selection_result.get('should_offer_synergy', False):
            response += "\n\n💫 Этот продукт отлично сочетается с другими нашими добавками."
        
        # Предлагаем следующие действия
        next_actions = selection_result.get('next_actions', [])
        if next_actions:
            response += "\n\nМогу помочь с:\n"
            for i, action in enumerate(next_actions, 1):
                response += f"{i}. {action}\n"
        
        await message.reply(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_product_selection: {e}")
        # Стандартная обработка как fallback
        await handle_standard_product_selection(message)
```

### Шаг 4: Модификация handle_product_link_request

```python
async def handle_product_link_request(message: types.Message):
    user_id = str(message.from_user.id)
    
    try:
        # Определяем запрашиваемый продукт
        product_name = extract_product_from_link_request(message.text)
        
        if product_name:
            # Обрабатываем через контекстную систему
            link_result = contextual_integration.handle_link_request(
                user_id, product_name
            )
            
            # Отправляем ссылку
            await send_product_link(message, product_name)
            
            # Добавляем контекстные предложения
            if link_result.get('high_purchase_intent', False):
                await asyncio.sleep(1)
                await message.reply(
                    "🎯 Вижу, что вы готовы к покупке! "
                    "Нужна консультация по применению или дозировке?"
                )
            
            # Предлагаем дополнительные продукты
            if link_result.get('should_suggest_complementary', False):
                await asyncio.sleep(2)
                await message.reply(
                    "💡 Для усиления эффекта рекомендую также рассмотреть "
                    "дополнительные продукты. Интересно?"
                )
        
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_product_link_request: {e}")
        # Стандартная обработка как fallback
        await handle_standard_link_request(message)
```

## 📊 Аналитика и мониторинг

### Добавление команды для админа

```python
@dp.message_handler(commands=['user_insights'], user_id=ADMIN_ID)
async def show_user_insights(message: types.Message):
    """Показывает инсайты о пользователях для админа"""
    
    # Получаем статистику
    insights = contextual_integration.get_conversation_summary("all_users")
    
    response = "📊 **Аналитика диалогов:**\n\n"
    response += f"👥 Активных пользователей: {insights.get('total_users', 0)}\n"
    response += f"💬 Всего диалогов: {insights.get('total_conversations', 0)}\n"
    response += f"🛒 Высокое намерение покупки: {insights.get('high_intent_users', 0)}\n"
    response += f"🎯 Популярные продукты: {', '.join(insights.get('popular_products', []))}\n"
    
    await message.reply(response, parse_mode='Markdown')
```

## ⚙️ Конфигурация

### Настройки памяти

В `conversation_memory.py`:

```python
self.max_memory_hours = 1  # Сколько часов хранить историю
self.max_messages_per_user = 100  # Максимум сообщений на пользователя
self.cleanup_interval = 600  # Автоочистка каждые 10 минут
```

### Настройки персонализации

В `personalized_recommendations.py`:

```python
self.personalization_weights = {
    'previous_discussion': 0.3,      # Вес предыдущих обсуждений
    'health_focus_match': 0.4,       # Вес соответствия проблемам здоровья
    'synergy_bonus': 0.2,            # Вес синергии
    'conversation_stage': 0.1        # Вес стадии разговора
}
```

## 🎯 Преимущества интеграции

### Для пользователей:
- 🎪 **Персонализированный опыт** - рекомендации учитывают историю диалога
- 🧠 **Умный диалог** - бот помнит контекст и задает уточняющие вопросы
- 🎯 **Точные рекомендации** - система понимает связи между вопросами
- 🔄 **Естественное общение** - как с живым консультантом

### Для бизнеса:
- 📈 **Увеличение продаж** - лучшее понимание потребностей клиентов
- 🎯 **Повышение конверсии** - персонализированные рекомендации
- 📊 **Аналитика клиентов** - инсайты о предпочтениях и поведении
- 💰 **ROI** - более эффективные продажи через понимание контекста

## 🔧 Тестирование системы

### Запуск демонстрации

```bash
python enhanced_bot_with_context.py
```

### Тестовые сценарии

1. **Базовый диалог:**
   - "Мне нужно что-то для печени"
   - "А что лучше сочетается с этим?"
   - "1" (выбор продукта)
   - "Пришли ссылку"

2. **Персонализация:**
   - Повторный диалог с тем же пользователем
   - Система должна помнить предыдущие предпочтения

3. **Уточняющие вопросы:**
   - Неточный запрос: "Нужно что-то для здоровья"
   - Система должна задать уточняющие вопросы

## 🚀 Развертывание

1. **Убедитесь в наличии всех файлов:**
   ```
   conversation_memory.py
   context_analyzer.py
   personalized_recommendations.py
   conversation_flow.py
   contextual_bot_integration.py
   ```

2. **Обновите bot.py** согласно инструкциям выше

3. **Запустите бота** и протестируйте функциональность

4. **Мониторьте логи** для выявления ошибок интеграции

## 📈 Результаты

После интеграции вы получите:
- 🎯 **Умного бота-консультанта** вместо простого поисковика
- 📊 **Аналитику поведения** пользователей
- 💰 **Увеличение продаж** через персонализацию
- 🚀 **Конкурентное преимущество** в области AI

---

*Контекстная система превращает Aurora Bot в интеллектуального консультанта, который понимает клиентов и помогает им найти именно то, что нужно для их здоровья и благополучия.*
