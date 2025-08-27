# bot.py
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ChatAction
import json

from dotenv import load_dotenv

# Константы для изображений
WELCOME_PHOTO_ID = "AgACAgIAAxkBAAID2Gike91mECS1PIS7qfib1Fc7LwdOAAIy_DEbyo8gSRO7zGsoAaAFAQADAgADeAADNgQ"
MENU_PHOTO_ID = "AgACAgIAAxkBAAID1mike8kt0PGUNNoU9U4abT45A8nhAAIx_DEbyo8gSX4-GaO4NzKhAQADAgADeAADNgQ"

# Импортируем только если файлы существуют
try:
    from database import init_db, add_user, log_user_action, get_all_user_ids
except ImportError:
    print("⚠️ Модуль database недоступен, используем заглушки")
    def init_db(): pass
    def add_user(user_id, username, full_name): pass
    def log_user_action(user_id, action): pass
    def get_all_user_ids(): return []

# Импорт локального логгера
try:
    from local_logger import log_user_question_local
    LOCAL_LOGGING_ENABLED = True
    print("✅ Локальное логирование подключено")
except ImportError:
    print("⚠️ Модуль local_logger недоступен")
    def log_user_question_local(user_id, username, question): pass
    LOCAL_LOGGING_ENABLED = False

try:
    # Новые улучшенные модули
    from enhanced_vector_db import enhanced_vector_db
    from enhanced_llm import enhanced_llm
    from nlp_processor import nlp_processor, Intent
    from product_recommendations import recommendation_manager
    AI_ENABLED = True
    
    # Старые модули для совместимости
    try:
        from vector_db import client, model, start_auto_update as old_start_auto_update
        from llm import ask_llm as old_ask_llm
    except ImportError:
        pass
        
except ImportError:
    print("⚠️ AI модули недоступны, работаем без ИИ")
    AI_ENABLED = False
    def enhanced_llm_process_query(question): return "AI временно недоступен"

load_dotenv()

def smart_truncate_text(text: str, max_length: int) -> str:
    """Умное обрезание текста с учетом границ предложений и абзацев"""
    if len(text) <= max_length:
        return text
    
    # Обрезаем до максимальной длины
    truncated = text[:max_length]
    
    # Пытаемся найти хорошее место для обрезки в порядке приоритета:
    # 1. Конец абзаца (двойной перенос строки)
    # 2. Конец предложения (точка, восклицательный, вопросительный знак)
    # 3. Конец слова (пробел)
    
    # Ищем последний абзац
    last_paragraph = truncated.rfind('\n\n')
    if last_paragraph > max_length * 0.6:  # Если абзац не слишком короткий
        return truncated[:last_paragraph].strip()
    
    # Ищем последнее предложение
    sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
    best_sentence_end = -1
    for ending in sentence_endings:
        pos = truncated.rfind(ending)
        if pos > best_sentence_end:
            best_sentence_end = pos
    
    if best_sentence_end > max_length * 0.7:  # Если предложение не слишком короткое
        return truncated[:best_sentence_end + 1].strip()
    
    # Ищем последнее слово
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.8:  # Если не обрезаем слишком много
        return truncated[:last_space].strip()
    
    # В крайнем случае обрезаем как есть
    return truncated.strip()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище пользователей
users = set()

# Хранилище для пошаговых рекомендаций
user_recommendations = {}

# Хранилище для полных ответов (для кнопки "Читать дальше")
user_full_answers = {}  # user_id: full_answer_text

# Хранилище контекста рекомендованных продуктов
user_product_context = {}  # user_id: [{"name": "Аргент Макс", "url": "...", "image_id": "..."}, ...]

# Хранилище для режима "Написать консультанту"
users_waiting_for_natalya = set()  # Пользователи, которые ждут ответа от Наталии
admin_replying_to = {}  # admin_message_id: user_id - для связи ответов админа с пользователями

# Хранилище для карусели продуктов
user_product_carousels = {}  # user_id: {"products": [...], "current_index": 0, "message_id": ...}

# Запуск автообновления базы
if AI_ENABLED:
    # Первичная индексация перед стартом автообновления
    try:
        enhanced_vector_db.index_knowledge()
    except Exception as e:
        print(f"Инициализация индекса не удалась: {e}")
    enhanced_vector_db.start_auto_update()

async def send_typing_action(chat_id: int, duration: float = 1.0):
    """Отправляет эффект печатания на указанное время"""
    try:
        await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(duration)
    except Exception as e:
        print(f"Ошибка отправки typing action: {e}")

def main_menu():
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Регистрация 💚", url="https://aur-ora.com/auth/registration/666282189484")],
        [InlineKeyboardButton(text="📋 Каталог всех продуктов", url="https://aur-ora.com/catalog/vse_produkty")],
        [InlineKeyboardButton(text="📍 Адреса магазинов", callback_data="check_city")],
        [InlineKeyboardButton(text="✉️ Написать консультанту", callback_data="write_to_natalya")]
    ])
    return markup

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    users.add(user_id)
    add_user(user_id, message.from_user.username, message.from_user.full_name)
    log_user_action(user_id, "start")
    
    await message.answer_photo(
        photo=WELCOME_PHOTO_ID,
        caption="Привет! Меня зовут Наталья Кумасинская. Я являюсь консультантом компании Аврора и давно использую продукцию Авроры. "
                "Хочу поделиться опытом и помочь выбрать самые лучшие продукты этой фирмы"
    )
    
    await asyncio.sleep(2)
    
    await message.answer_photo(
        photo=MENU_PHOTO_ID,
        caption="Выбери, что тебе подходит 👇",
        reply_markup=main_menu()
    )

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    log_user_action(message.from_user.id, "open_menu")
    await message.answer_photo(
        photo=MENU_PHOTO_ID,
        caption="Выбери, что тебе подходит 👇",
        reply_markup=main_menu()
    )

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав администратора")
        return
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📤 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")]
    ])
    
    await message.answer("🔐 Админ-панель", reply_markup=markup)



@dp.callback_query(lambda c: c.data == "write_to_natalya")
async def write_to_natalya(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    log_user_action(user_id, "write_to_natalya")
    
    # Включаем режим ожидания сообщения для Наталии
    users_waiting_for_natalya.add(user_id)
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_natalya")]
    ])
    
    # Удаляем сообщение с фото и отправляем новое текстовое
    await callback_query.message.delete()
    await callback_query.message.answer(
        "✉️ Написать консультанту\n\n"
        "Напишите ваше сообщение, и я передам его Наталье.\n"
        "Она лично ответит вам в ближайшее время!\n\n"
        "💬 Ожидаю ваше сообщение...",
        reply_markup=markup
    )
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "cancel_natalya")
async def cancel_natalya(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    # Убираем пользователя из режима ожидания
    users_waiting_for_natalya.discard(user_id)
    
    # Удаляем сообщение и показываем главное меню с картинкой
    await callback_query.message.delete()
    await callback_query.message.answer_photo(
        photo=MENU_PHOTO_ID,
        caption="❌ Отправка сообщения Наталье отменена.\n\n"
                "Выберите, что вас интересует:",
        reply_markup=main_menu()
    )
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "check_city")
async def check_city(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    log_user_action(user_id, "check_city")
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Москва", callback_data="city_moscow"), 
         InlineKeyboardButton(text="СПб", callback_data="city_spb")],
        [InlineKeyboardButton(text="Другой город", callback_data="city_other")]
    ])
    
    # Удаляем сообщение с фото и отправляем новое текстовое
    await callback_query.message.delete()
    await callback_query.message.answer(
        "🏪 Выберите город для поиска магазинов:",
        reply_markup=markup
    )
    await callback_query.answer()



@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Снимаем режим ожидания сообщения для Наталии, если он был включен
    users_waiting_for_natalya.discard(user_id)
    
    # Удаляем старое сообщение и отправляем главное меню с картинкой
    await callback_query.message.delete()
    await callback_query.message.answer_photo(
        photo=MENU_PHOTO_ID,
        caption="Выбери, что тебе подходит 👇",
        reply_markup=main_menu()
    )
    await callback_query.answer()

@dp.message(lambda message: message.photo)
async def handle_photo(message: types.Message):
    """Обработчик фотографий для получения file_id"""
    if message.from_user.id != ADMIN_ID:
        return
    
    # Получаем file_id самого большого размера фото
    photo = message.photo[-1]
    file_id = photo.file_id
    
    await message.reply(
        f"📷 File ID фотографии:\n\n<code>{file_id}</code>\n\n"
        f"Скопируйте этот ID и добавьте в knowledge_base.json "
        f"в поле image_id нужного продукта.",
        parse_mode="HTML"
    )

@dp.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("❌ Нет прав", show_alert=True)
        return
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
    ])
    
    await callback_query.message.edit_text(
        f"📊 Статистика\n\n👥 Всего пользователей: {len(users)}",
        reply_markup=markup
    )
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "admin_back")
async def admin_back(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("❌ Нет прав", show_alert=True)
        return
        
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📤 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")]
    ])
    
    await callback_query.message.edit_text("🔐 Админ-панель", reply_markup=markup)
    await callback_query.answer()

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Проверяем, ждет ли пользователь отправки сообщения Наталье
    if user_id in users_waiting_for_natalya:
        await handle_message_to_natalya(message)
        return
    
    # Проверяем, отвечает ли пользователь на вопрос о ссылке
    if text.lower() in ["да", "да нужна", "нужна", "да, нужна"]:
        await handle_link_request_confirmation(message)
        return
    
    # Проверяем запросы на дополнительные рекомендации в контексте темы
    additional_request_patterns = [
        "что посоветуешь еще", "что еще", "еще что", "что-то еще", "еще продукты",
        "что посоветуешь ещё", "что ещё", "ещё что", "что-то ещё", "ещё продукты",
        "дополнительно что", "дополнительные", "другие варианты"
    ]
    if any(pattern in text.lower() for pattern in additional_request_patterns):
        await handle_additional_recommendations(message)
        return
    
    # Проверяем запрос на ссылку
    link_indicators = ["ссылка", "ссылки", "ссылочку", "пришли ссылку", "дай ссылку", "покажи ссылку", "где купить", "купить"]
    if any(indicator in text.lower() for indicator in link_indicators):
        await handle_product_link_request(message, None)
        return
    
    # Сначала проверяем, является ли это новым вопросом
    # Очищаем контекст продуктов при новых вопросах
    if user_id in user_product_context:
        # Определяем новые вопросы по ключевым словам
        question_indicators = ["что", "какие", "как", "где", "когда", "почему", "зачем", "расскажи", "покажи", "есть ли", "посоветуй", "нужно", "хочу", "для"]
        is_new_question = any(indicator in text.lower() for indicator in question_indicators)
        
        # Если это длинный текст с вопросительными словами - это новый вопрос
        if len(text) > 15 and is_new_question:
            del user_product_context[user_id]
        # Иначе проверяем, выбирает ли пользователь продукт
        elif len(text) < 50:
            # Проверяем, что это действительно выбор продукта
            if text.isdigit() or any(word.lower() in text.lower() for word in [
                "аргент", "гепосин", "симбион", "еломил", "bwl", "черного ореха", "солберри", "битерон",
                "кошачий", "коготь", "ин-аурин", "барс", "bars", "си-энержи", "витамин", "оранж"
            ]):
                await handle_product_selection(message)
                return
    
    # Проверяем, отвечает ли админ на сообщение пользователя
    if user_id == ADMIN_ID and message.reply_to_message:
        await handle_admin_reply(message)
        return
    
    # Обработка коротких сообщений и приветствий
    if len(text) < 3:
        return
    
    # Контекст уже обработан выше
    
    # Обработка приветствий
    greetings = ["привет", "здравствуй", "здравствуйте", "хай", "hello", "hi", "добрый день", "добрый вечер", "доброе утро"]
    if any(greeting in text.lower() for greeting in greetings):
        
        # Эффект печатания
        await send_typing_action(user_id, 2.0)
        
        await message.reply(
            "🌿 **Добро пожаловать в мир AURORA!** 👋\n\n"
            "Я ваш персональный AI-консультант по натуральным продуктам здоровья. "
            "За считанные секунды найду идеальное решение для вашего здоровья!\n\n"
            
            "🧠 **Моя уникальность:**\n"
            "• **База знаний AURORA** — анализирую 98+ продуктов из официальных данных\n"
            "• **Комплексный подход** — рекомендую синергичные решения\n"
            "• **100% достоверность** — только проверенная информация с сайта компании\n"
            "• **Прямые ссылки** — отправлю фото и ссылку на любой товар\n"
            "• **Индивидуальность** — учитываю именно ваши потребности\n\n"
            
            "💎 **Ваши преимущества:**\n"
            "✅ **Экономия времени** — мгновенные ответы вместо часов поиска\n"
            "✅ **Экспертность** — знания уровня специалиста в кармане\n"
            "✅ **Точность** — никаких противоречивых советов из интернета\n"
            "✅ **Доступность** — консультации 24/7 бесплатно\n\n"
            
            "🎯 **Решаю реальные задачи:**\n"
            "🔸 **Здоровье:** \"*У ребенка бронхит, что поможет?*\"\n"
            "🔸 **Профилактика:** \"*Что принимать для крепкого иммунитета?*\"\n"
            "🔸 **Проблемы:** \"*Печень после праздников, нужна помощь*\"\n"
            "🔸 **Сравнение:** \"*Хлорофилл или Детокс — что эффективнее?*\"\n"
            "🔸 **Красота:** \"*Хочу здоровую кожу и волосы изнутри*\"\n"
            "🔸 **Энергия:** \"*Постоянная усталость, что посоветуешь?*\"\n"
            "🔸 **Ссылки:** \"*Дай ссылку на Солберри*\" или \"*Где купить Хлорофилл?*\"\n\n"
            
            "🚀 **Начните прямо сейчас!**\n"
            "Просто опишите свою задачу обычными словами — я пойму и подберу идеальное решение с объяснением, почему именно это вам подходит!\n\n"
            
            "💬 *Например: \"Нужно что-то натуральное от стресса\" или \"Витамины для женщин после 40\"*\n\n"
            
            "💡 **Забыли мои возможности?** Просто напишите *\"Привет\"* — я напомню обо всем, что умею!",
            parse_mode="Markdown"
        )
        return
    
    log_user_action(user_id, f"asked: {text[:50]}...")
    
    # Логируем вопрос локально для анализа
    if LOCAL_LOGGING_ENABLED:
        username = message.from_user.username or message.from_user.full_name or "Unknown"
        log_user_question_local(user_id, username, text)
    
    # Если AI доступен, используем улучшенную обработку
    if AI_ENABLED:
        try:
            # Обрабатываем сообщение через новый NLP процессор
            processed_message = nlp_processor.process_message(text)
            
            # Логируем распознанные намерения и сущности для анализа
            intent_info = f"Intent: {processed_message.intent.value}, Sentiment: {processed_message.sentiment}"
            if processed_message.entities:
                entities_info = ", ".join([f"{e.label}: {e.text}" for e in processed_message.entities])
                intent_info += f", Entities: {entities_info}"
            log_user_action(user_id, intent_info)
            
            # Проверяем, нужно ли использовать пошаговые рекомендации
            # ТОЛЬКО если пользователь отвечает на сообщение бота (Reply)
            if processed_message.intent == Intent.PRODUCT_SELECTION and message.reply_to_message:
                # Проверяем, запрашивает ли пользователь весь ассортимент
                text_lower = text.lower()
                is_full_assortment_request = any(phrase in text_lower for phrase in [
                    "весь", "все", "весь ассортимент", "все продукты", "полный список"
                ])
                
                if is_full_assortment_request:
                    # Получаем все продукты по запросу
                    all_products = recommendation_manager.get_recommendations(
                        processed_message.expanded_query, limit=10
                    )
                    
                    if all_products:
                        # Сохраняем все продукты для пользователя
                        user_product_context[user_id] = all_products
                        
                        # Отправляем список всех продуктов
                        await send_all_products_list(message, all_products)
                        return
                
                # Для обычных запросов используем LLM
            
            # Обработка запросов о регистрации
            if processed_message.intent == Intent.REGISTRATION:
                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="🔗 Регистрация на сайте", 
                        url="https://aur-ora.com/auth/registration/666282189484/"
                    )],
                    [InlineKeyboardButton(
                        text="✉️ Написать консультанту", 
                        callback_data="write_to_natalya"
                    )]
                ])
                
                # Эффект печатания
                await send_typing_action(user_id, 2.0)
                
                await message.reply(
                    "📝 Регистрация в компании АВРОРА\n\n"
                    "Для регистрации на сайте и получения персональных скидок "
                    "воспользуйтесь кнопкой ниже.\n\n"
                    "После регистрации вам будут доступны:\n"
                    "• 💰 Персональные скидки\n"
                    "• 📦 Отслеживание заказов\n"
                    "• 👤 Личный кабинет\n"
                    "• 🎯 Возможности представителя\n\n"
                    "Если нужна помощь с регистрацией, обратитесь к консультанту.",
                    reply_markup=markup
                )
                return
            
            # Обработка запросов ссылок на продукты
            if processed_message.intent == Intent.PRODUCT_LINK:
                await handle_product_link_request(message, processed_message)
                return
            
            # Для остальных типов запросов используем обычный LLM ответ
            # Эффект печатания
            await send_typing_action(user_id, 1.5)
            
            llm_result = enhanced_llm.process_query(text)
            
            # Проверяем, вернул ли LLM кортеж (ответ + контекст) или просто ответ
            if isinstance(llm_result, tuple) and len(llm_result) == 2:
                answer, products_context = llm_result
                # Устанавливаем контекст напрямую (для запросов об иммунитете)
                user_product_context[user_id] = products_context
            else:
                answer = llm_result
                # Извлекаем продукты из ответа для сохранения в контексте
                extracted_products = extract_products_from_answer(answer)
                if extracted_products:
                    user_product_context[user_id] = extracted_products
                else:
                    # Если продукты не найдены, очищаем контекст
                    user_product_context.pop(user_id, None)
            
            # Проверяем, содержит ли ответ информацию об отсутствии данных
            has_no_info_phrases = any(phrase in answer.lower() for phrase in [
                "нет информации", "не смогла найти", "извините", "обратитесь к консультанту", "напишите наталье"
            ])
            
            # Определяем нужно ли обрезать ответ
            full_answer = answer
            is_truncated = len(answer) > 999
            
            if is_truncated:
                # Сохраняем полный ответ для кнопки "Читать дальше"
                user_full_answers[user_id] = full_answer
                
                # Умное обрезание ответа по границам предложений
                answer = smart_truncate_text(answer, 999)
            
            # Создаем клавиатуру в зависимости от ответа
            markup_buttons = []
            
            if is_truncated:
                # Добавляем кнопку "Читать дальше"
                markup_buttons.append([InlineKeyboardButton(
                    text="📖 Читать дальше", 
                    callback_data=f"read_more_{user_id}"
                )])
            
            if has_no_info_phrases:
                # Добавляем кнопку консультанта только при отсутствии информации
                markup_buttons.append([InlineKeyboardButton(
                    text="✉️ Написать консультанту", 
                    callback_data="write_to_natalya"
                )])
            
            # Создаем разметку (может быть пустой для обычных ответов)
            markup = InlineKeyboardMarkup(inline_keyboard=markup_buttons) if markup_buttons else None
            
            # Отправляем ответ пользователю
            await message.reply(answer, reply_markup=markup)
            
            # Если это жалоба или негативная тональность, уведомляем админа с приоритетом
            if (processed_message.intent == Intent.COMPLAINT or 
                processed_message.sentiment == "negative"):
                
                if ADMIN_ID:
                    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
                    await bot.send_message(
                        ADMIN_ID,
                        f"🚨 ПРИОРИТЕТ - Жалоба от {username} (ID: {user_id}):\n\n"
                        f"Оригинал: {text}\n\n"
                        f"Анализ: {intent_info}\n\n"
                        f"Ответ бота: {answer[:200]}..."
                    )
            
            return
            
        except Exception as e:
            print(f"Enhanced AI ошибка: {e}")
            
            # Fallback к старому методу если новый не работает
            try:
                if hasattr(globals(), 'client') and hasattr(globals(), 'model'):
                    query_vector = model.encode(text).tolist()
                    results = client.search("aurora_knowledge", query_vector, limit=2)

                    if results:
                        context = "\n\n---\n\n".join([
                            f"Продукт: {hit.payload['product']}\n"
                            f"Описание: {hit.payload['description']}\n"
                            f"Польза: {', '.join(hit.payload['benefits'])}\n"
                            f"Состав: {hit.payload['composition']}\n"
                            f"Рекомендации: {hit.payload['dosage']}\n"
                            f"Противопоказания: {hit.payload['contraindications']}"
                            for hit in results
                        ])

                        if hasattr(globals(), 'old_ask_llm'):
                            answer = old_ask_llm(text, context)
                            await message.reply(answer)
                            return
            except Exception as fallback_error:
                print(f"Fallback AI ошибка: {fallback_error}")
    
    # Простой ответ без AI
    await message.reply(
        "Спасибо за ваш вопрос! Ваше сообщение передано Наталье, она обязательно ответит."
    )
    
    # Уведомляем админа
    if ADMIN_ID:
        username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
        await bot.send_message(
            ADMIN_ID,
            f"📩 Сообщение от {username} (ID: {user_id}):\n\n{text}"
        )

async def handle_message_to_natalya(message: types.Message):
    """Обрабатывает сообщение пользователя для отправки Наталье"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Убираем пользователя из режима ожидания
    users_waiting_for_natalya.discard(user_id)
    
    if not text:
        await message.reply("❌ Пустое сообщение не может быть отправлено.")
        return
    
    # Получаем информацию о пользователе
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
    user_info = f"{message.from_user.full_name}"
    if message.from_user.username:
        user_info += f" (@{message.from_user.username})"
    
    # Отправляем сообщение админу
    if ADMIN_ID:
        try:
            # Эффект печатания
            await send_typing_action(user_id, 1.0)
            
            admin_message = await bot.send_message(
                ADMIN_ID,
                f"💌 <b>Сообщение от пользователя</b>\n\n"
                f"👤 <b>От:</b> {user_info}\n"
                f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
                f"📝 <b>Сообщение:</b>\n{text}\n\n"
                f"💡 _Ответьте на это сообщение (Reply), чтобы отправить ответ пользователю_",
                parse_mode="HTML"
            )
            
            # Сохраняем связь между сообщением админа и пользователем
            admin_replying_to[admin_message.message_id] = user_id
            
            # Подтверждаем пользователю
            markup = None
            
            await message.reply(
                "✅ <b>Сообщение отправлено консультанту!</b>\n\n"
                "Она получила ваш вопрос и ответит в ближайшее время.\n"
                "Ответ придет вам в этот чат.",
                reply_markup=markup,
                parse_mode="HTML"
            )
            
            log_user_action(user_id, f"sent_to_natalya: {text[:50]}...")
            
        except Exception as e:
            print(f"Ошибка отправки сообщения админу: {e}")
            await message.reply(
                "❌ Произошла ошибка при отправке сообщения.\n"
                "Попробуйте позже или обратитесь через главное меню."
            )
    else:
        await message.reply(
            "❌ Наталья временно недоступна.\n"
            "Попробуйте задать вопрос боту или обратитесь позже."
        )

async def handle_admin_reply(message: types.Message):
    """Обрабатывает ответ админа пользователю"""
    if not message.reply_to_message:
        return
    
    replied_message_id = message.reply_to_message.message_id
    
    # Находим, кому предназначен ответ
    if replied_message_id in admin_replying_to:
        target_user_id = admin_replying_to[replied_message_id]
        admin_response = message.text.strip()
        
        if not admin_response:
            await message.reply("❌ Пустой ответ не может быть отправлен.")
            return
        
        try:
            # Отправляем ответ пользователю
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✉️ Написать ещё", callback_data="write_to_natalya")]
            ])
            
            await bot.send_message(
                target_user_id,
                f"💬 <b>Ответ от Наталии:</b>\n\n{admin_response}",
                reply_markup=markup,
                parse_mode="HTML"
            )
            
            # Подтверждаем админу
            await message.reply("✅ Ответ отправлен пользователю!")
            
            # Убираем связь, так как диалог завершен
            del admin_replying_to[replied_message_id]
            
            log_user_action(target_user_id, f"received_reply_from_natalya: {admin_response[:50]}...")
            
        except Exception as e:
            print(f"Ошибка отправки ответа пользователю {target_user_id}: {e}")
            await message.reply(f"❌ Ошибка отправки ответа пользователю {target_user_id}")
    else:
        # Это обычное сообщение от админа, не ответ
        pass

async def send_recommendation(message: types.Message, user_id: int, recommendation_index: int):
    """Отправляет рекомендацию продукта пользователю"""
    if user_id not in user_recommendations:
        await message.reply("Рекомендации не найдены. Попробуйте задать вопрос заново.")
        return
    
    recommendations = user_recommendations[user_id]
    
    if recommendation_index < 1 or recommendation_index > len(recommendations):
        await message.reply("Рекомендация не найдена.")
        return
    
    # Эффект печатания
    await send_typing_action(user_id, 2.0)
    
    recommendation = recommendations[recommendation_index - 1]
    current = recommendation_index
    total = len(recommendations)
    
    # Форматируем сообщение
    text, image_id = recommendation_manager.format_recommendation_message(
        recommendation, current, total
    )
    
    # Создаем клавиатуру
    keyboard = recommendation_manager.create_recommendation_keyboard(
        user_id, current, total, recommendation.url
    )
    
    # Отправляем с картинкой если есть
    if image_id and image_id.strip():
        try:
            await message.answer_photo(
                photo=image_id,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Ошибка отправки фото {image_id}: {e}")
            # Fallback без картинки
            await message.reply(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    else:
        await message.reply(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

async def send_recommendation_edit(callback_query: types.CallbackQuery, user_id: int, recommendation_index: int):
    """Редактирует сообщение с рекомендацией (для навигации)"""
    if user_id not in user_recommendations:
        await callback_query.answer("Рекомендации не найдены", show_alert=True)
        return
    
    recommendations = user_recommendations[user_id]
    
    if recommendation_index < 1 or recommendation_index > len(recommendations):
        await callback_query.answer("Рекомендация не найдена", show_alert=True)
        return
    
    recommendation = recommendations[recommendation_index - 1]
    current = recommendation_index
    total = len(recommendations)
    
    # Форматируем сообщение
    text, image_id = recommendation_manager.format_recommendation_message(
        recommendation, current, total
    )
    
    # Создаем клавиатуру
    keyboard = recommendation_manager.create_recommendation_keyboard(
        user_id, current, total, recommendation.url
    )
    
    # Редактируем сообщение
    try:
        # Если в сообщении есть фото, отправляем новое сообщение
        if callback_query.message.photo and image_id and image_id.strip():
            await callback_query.message.answer_photo(
                photo=image_id,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            # Удаляем старое сообщение
            await callback_query.message.delete()
        elif image_id and image_id.strip():
            # Если нужно добавить фото к текстовому сообщению
            await callback_query.message.answer_photo(
                photo=image_id,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            await callback_query.message.delete()
        else:
            # Просто редактируем текст
            await callback_query.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    except Exception as e:
        print(f"Ошибка редактирования рекомендации: {e}")
        await callback_query.answer("Ошибка обновления", show_alert=True)

# Обработчики навигации по рекомендациям
@dp.callback_query(lambda c: c.data.startswith("rec_next_"))
async def handle_next_recommendation(callback_query: types.CallbackQuery):
    """Обработчик кнопки 'Следующий'"""
    try:
        _, _, user_id_str, index_str = callback_query.data.split("_")
        user_id = int(user_id_str)
        index = int(index_str)
        
        if callback_query.from_user.id != user_id:
            await callback_query.answer("Это не ваши рекомендации", show_alert=True)
            return
        
        await send_recommendation_edit(callback_query, user_id, index)
        await callback_query.answer()
        
    except Exception as e:
        print(f"Ошибка в handle_next_recommendation: {e}")
        await callback_query.answer("Ошибка навигации", show_alert=True)

@dp.callback_query(lambda c: c.data.startswith("rec_prev_"))
async def handle_prev_recommendation(callback_query: types.CallbackQuery):
    """Обработчик кнопки 'Предыдущий'"""
    try:
        _, _, user_id_str, index_str = callback_query.data.split("_")
        user_id = int(user_id_str)
        index = int(index_str)
        
        if callback_query.from_user.id != user_id:
            await callback_query.answer("Это не ваши рекомендации", show_alert=True)
            return
        
        await send_recommendation_edit(callback_query, user_id, index)
        await callback_query.answer()
        
    except Exception as e:
        print(f"Ошибка в handle_prev_recommendation: {e}")
        await callback_query.answer("Ошибка навигации", show_alert=True)

@dp.callback_query(lambda c: c.data.startswith("read_more_"))
async def handle_read_more(callback_query: types.CallbackQuery):
    """Обработчик кнопки 'Читать дальше'"""
    try:
        # Извлекаем user_id из callback_data
        user_id_str = callback_query.data.replace("read_more_", "")
        user_id = int(user_id_str)
        
        # Проверяем что пользователь запрашивает свой ответ
        if callback_query.from_user.id != user_id:
            await callback_query.answer("Это не ваше сообщение", show_alert=True)
            return
        
        # Получаем полный ответ
        if user_id in user_full_answers:
            full_answer = user_full_answers[user_id]
            
            # Находим где обрезали текст, используя ту же умную логику
            first_part = smart_truncate_text(full_answer, 999)
            first_part_length = len(first_part)
            
            # Получаем оставшуюся часть
            remaining_text = full_answer[first_part_length:].strip()
            
            if remaining_text:
                # Отправляем продолжение
                await callback_query.message.reply(remaining_text)
                
                # Удаляем из хранилища, так как уже показали
                del user_full_answers[user_id]
                
                await callback_query.answer("Продолжение отправлено!")
            else:
                await callback_query.answer("Нет дополнительного текста", show_alert=True)
        else:
            await callback_query.answer("Полный ответ не найден", show_alert=True)
            
    except Exception as e:
        print(f"Ошибка в handle_read_more: {e}")
        await callback_query.answer("Произошла ошибка", show_alert=True)

@dp.callback_query(lambda c: c.data.startswith("carousel_prev_"))
async def handle_carousel_prev(callback_query: types.CallbackQuery):
    """Обработчик кнопки 'Назад' в карусели"""
    try:
        # Извлекаем user_id и index из callback_data
        parts = callback_query.data.split("_")
        user_id = int(parts[2])
        new_index = int(parts[3])
        
        # Проверяем что пользователь запрашивает свою карусель
        if callback_query.from_user.id != user_id:
            await callback_query.answer("Это не ваша карусель", show_alert=True)
            return
        
        await update_product_carousel(callback_query, user_id, new_index)
        
    except Exception as e:
        print(f"Ошибка в handle_carousel_prev: {e}")
        await callback_query.answer("Произошла ошибка", show_alert=True)

@dp.callback_query(lambda c: c.data.startswith("carousel_next_"))
async def handle_carousel_next(callback_query: types.CallbackQuery):
    """Обработчик кнопки 'Вперед' в карусели"""
    try:
        # Извлекаем user_id и index из callback_data
        parts = callback_query.data.split("_")
        user_id = int(parts[2])
        new_index = int(parts[3])
        
        # Проверяем что пользователь запрашивает свою карусель
        if callback_query.from_user.id != user_id:
            await callback_query.answer("Это не ваша карусель", show_alert=True)
            return
        
        await update_product_carousel(callback_query, user_id, new_index)
        
    except Exception as e:
        print(f"Ошибка в handle_carousel_next: {e}")
        await callback_query.answer("Произошла ошибка", show_alert=True)

@dp.callback_query(lambda c: c.data == "carousel_info")
async def handle_carousel_info(callback_query: types.CallbackQuery):
    """Обработчик кнопки информации о позиции в карусели"""
    await callback_query.answer("Информация о позиции", show_alert=False)

async def handle_product_link_request(message: types.Message, processed_message=None):
    """Обрабатывает запросы ссылок на конкретные продукты"""
    user_id = message.from_user.id
    
    try:
        # Ищем продукт в базе знаний
        import json
        
        # Сначала проверяем контекст пользователя - был ли упомянут продукт ранее
        context_product = None
        if user_id in user_product_context:
            context_products = user_product_context[user_id]
            # Если контекст - список, берем первый продукт
            if isinstance(context_products, list) and context_products:
                context_product = context_products[0]
            elif isinstance(context_products, dict):
                context_product = context_products
        
        # Извлекаем название продукта из сущностей или текста
        product_name = ""
        if processed_message is not None and hasattr(processed_message, 'entities') and processed_message.entities:
            for entity in processed_message.entities:
                if entity.label == "PRODUCT":
                    product_name = entity.text
                    break
        
        # Если не нашли в сущностях, пытаемся найти в тексте
        if not product_name:
            text_words = message.text.lower().split()
            # Фильтруем служебные слова
            meaningful_words = [word for word in text_words if len(word) > 2 and word not in 
                               ["ссылку", "пришли", "дай", "покажи", "нужна", "хочу", "где", "как", "можно", "есть", "на", "вашем", "сайте"]]
            
            # Добавляем базовые формы слов для лучшего поиска
            base_forms = []
            for word in meaningful_words:
                base_forms.append(word)
                # Убираем окончания для поиска базовой формы
                if word.endswith('у'):
                    base_forms.append(word[:-1])  # спирулину -> спирулин
                if word.endswith('ы'):
                    base_forms.append(word[:-1] + 'а')  # спирулины -> спирулина
                if word.endswith('ой'):
                    base_forms.append(word[:-2] + 'а')  # спирулиной -> спирулина
            
            meaningful_words = list(set(base_forms))  # Убираем дубликаты
            
            print(f"🔍 DEBUG: Исходные слова: {text_words}")
            print(f"🔍 DEBUG: Значимые слова: {meaningful_words}")
            
            # Ищем в обеих базах знаний
            found_products = []
            best_matches = []
            
            # Универсальный поиск с улучшенной логикой
            print("🔍 Универсальный поиск продуктов")
            for kb_file in ["knowledge_base.json", "knowledge_base_new.json"]:
                try:
                    with open(kb_file, "r", encoding="utf-8") as f:
                        kb_data = json.load(f)
                    
                    for item in kb_data:
                        product = item.get("product", "").lower()
                        description = item.get("short_description", "").lower()
                        category = item.get("category", "").lower()
                        
                        # Считаем количество совпадений слов в названии и описании
                        matches = 0
                        for word in meaningful_words:
                            if word in product:
                                matches += 3  # Высокий вес для названия
                                print(f"🔍 DEBUG: Слово '{word}' найдено в названии '{product}'")
                            if word in description:
                                matches += 1  # Меньший вес для описания
                                print(f"🔍 DEBUG: Слово '{word}' найдено в описании")
                            if word in category:
                                matches += 2  # Средний вес для категории
                                print(f"🔍 DEBUG: Слово '{word}' найдено в категории '{category}'")
                        
                        # Специальная логика для точных совпадений
                        query_lower = message.text.lower()
                        
                        # Для витамина С - приоритет продуктам с витамином С
                        if "витамин с" in query_lower or "витамин c" in query_lower:
                            if "витамин с" in product or "витамин c" in product or "оранж" in product:
                                matches += 10  # Очень высокий приоритет
                                print(f"🔍 DEBUG: Точное совпадение витамина С в продукте '{product}'")
                            elif "витамин д" in product or "витамин d" in product:
                                matches = 0  # Исключаем витамин Д
                                print(f"🔍 DEBUG: Исключаем витамин Д из результатов")
                        
                        # Для витамина Д - приоритет продуктам с витамином Д
                        elif "витамин д" in query_lower or "витамин d" in query_lower:
                            if "витамин д" in product or "витамин d" in product:
                                matches += 10  # Очень высокий приоритет
                                print(f"🔍 DEBUG: Точное совпадение витамина Д в продукте '{product}'")
                            else:
                                matches = 0  # Исключаем все остальные продукты
                                print(f"🔍 DEBUG: Исключаем продукт '{product}' из результатов витамина Д")
                        
                        if matches > 0:
                            found_products.append((item, matches))
                            print(f"🔍 DEBUG: Найден продукт '{product}' с {matches} совпадениями")
                                
                except Exception as e:
                    print(f"Ошибка чтения {kb_file}: {e}")
            

            
            # Сортируем по количеству совпадений
            found_products.sort(key=lambda x: x[1], reverse=True)
            found_products = [item[0] for item in found_products]
        else:
            # Ищем по точному названию
            found_products = []
            for kb_file in ["knowledge_base.json", "knowledge_base_new.json"]:
                try:
                    with open(kb_file, "r", encoding="utf-8") as f:
                        kb_data = json.load(f)
                    
                    for item in kb_data:
                        if product_name.lower() in item.get("product", "").lower():
                            found_products.append(item)
                            
                except Exception as e:
                    print(f"Ошибка чтения {kb_file}: {e}")
        
        # Специальная обработка для запросов о серебре
        if not found_products and any(word in message.text.lower() for word in ["серебро", "серебряный", "аргент"]):
            print("🔍 Специальный поиск для серебра")
            for kb_file in ["knowledge_base.json", "knowledge_base_new.json"]:
                try:
                    with open(kb_file, "r", encoding="utf-8") as f:
                        kb_data = json.load(f)
                    
                    for item in kb_data:
                        product = item.get("product", "").lower()
                        description = item.get("short_description", "").lower()
                        
                        # Ищем Аргент-Макс или продукты со серебром
                        if "аргент" in product or "серебро" in description or "argent" in product:
                            found_products.append(item)
                            print(f"🔍 DEBUG: Специальный поиск - найдено совпадение в продукте '{product}'")
                            
                except Exception as e:
                    print(f"Ошибка чтения {kb_file}: {e}")
        
        # Специальная обработка для запросов о витамине С
        if not found_products and any(word in message.text.lower() for word in ["витамин с", "витамин c", "витаминс"]):
            print("🔍 Специальный поиск для витамина С")
            for kb_file in ["knowledge_base.json", "knowledge_base_new.json"]:
                try:
                    with open(kb_file, "r", encoding="utf-8") as f:
                        kb_data = json.load(f)
                    
                    for item in kb_data:
                        product = item.get("product", "").lower()
                        category = item.get("category", "").lower()
                        
                        # Ищем продукты с витамином С в названии или категории
                        if "витамин с" in product or "витамин c" in product or "витамин с" in category or "оранж" in product:
                            found_products.append(item)
                            print(f"🔍 DEBUG: Специальный поиск - найдено совпадение витамина С в продукте '{product}'")
                            
                except Exception as e:
                    print(f"Ошибка чтения {kb_file}: {e}")
        
        # Если не нашли продукты в тексте, но есть контекст - используем его
        if not found_products and context_product:
            # Если контекст - список продуктов, используем все
            if isinstance(context_products, list) and len(context_products) > 1:
                found_products = context_products
                print(f"Используем контекстные продукты: {len(context_products)} продуктов")
            else:
                found_products = [context_product]
                print(f"Используем контекстный продукт: {context_product.get('product', '')}")
        

        

        
        # Эффект печатания
        await send_typing_action(user_id, 2.0)
        
        if found_products:
            # Если найден только один продукт
            if len(found_products) == 1:
                product = found_products[0]
                product_name = product.get("product", "")
                url = product.get("url", "")
                image_id = product.get("image_id", "")
                short_desc = product.get("short_description", "")
                
                # Создаем кнопку с ссылкой только если URL не пустой
                markup_buttons = []
                if url and url.strip():
                    markup_buttons.append([InlineKeyboardButton(
                        text="📖 Подробнее на сайте", 
                        url=url
                    )])
                else:
                    # Если URL пустой, добавляем кнопку консультанта
                    markup_buttons.append([InlineKeyboardButton(
                        text="✉️ Написать консультанту", 
                        callback_data="write_to_natalya"
                    )])
                
                markup = InlineKeyboardMarkup(inline_keyboard=markup_buttons)
                
                caption = f"🌿 **{product_name}**\n\n📝 {short_desc}"
                
                # Отправляем с картинкой если есть
                if image_id and image_id.strip():
                    try:
                        await message.answer_photo(
                            photo=image_id,
                            caption=caption,
                            reply_markup=markup,
                            parse_mode="Markdown"
                        )
                        return
                    except Exception as e:
                        print(f"Ошибка отправки фото {image_id}: {e}")
                
                # Fallback без картинки
                await message.reply(
                    caption,
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            else:
                # Если найдено несколько продуктов - создаем карусель
                await send_product_carousel(message, found_products, user_id)
        else:
            # Продукт не найден
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="✉️ Написать консультанту", 
                    callback_data="write_to_natalya"
                )]
            ])
            
            await message.reply(
                "😔 К сожалению, я не смог найти продукт, о котором вы спрашиваете.\n\n"
                "💡 Попробуйте:\n"
                "• Уточнить название продукта\n"
                "• Написать консультанту Наталье\n\n"
                "✉️ Наталья поможет найти нужный продукт и отправит ссылку!",
                reply_markup=markup
            )
            
    except Exception as e:
        print(f"Ошибка в handle_product_link_request: {e}")
        await message.reply(
            "❌ Произошла ошибка при поиске продукта. "
            "Попробуйте еще раз или обратитесь к консультанту."
        )

async def send_product_carousel(message: types.Message, products: list, user_id: int, start_index: int = 0):
    """Отправляет карусель продуктов с кнопками навигации"""
    try:
        if not products:
            return
        
        current_index = start_index % len(products)
        product = products[current_index]
        
        product_name = product.get("product", "")
        url = product.get("url", "")
        image_id = product.get("image_id", "")
        short_desc = product.get("short_description", "")
        
        # Создаем кнопки навигации
        markup_buttons = []
        
        # Кнопка "Подробнее на сайте" только если URL не пустой
        if url and url.strip():
            markup_buttons.append([InlineKeyboardButton(
                text="📖 Подробнее на сайте", 
                url=url
            )])
        else:
            # Если URL пустой, добавляем кнопку консультанта
            markup_buttons.append([InlineKeyboardButton(
                text="✉️ Написать консультанту", 
                callback_data="write_to_natalya"
            )])
        
        # Кнопки навигации
        nav_buttons = []
        
        # Кнопка "Назад"
        if len(products) > 1:
            prev_index = (current_index - 1) % len(products)
            nav_buttons.append(InlineKeyboardButton(
                text="⬅️ Назад", 
                callback_data=f"carousel_prev_{user_id}_{prev_index}"
            ))
        
        # Индикатор позиции
        nav_buttons.append(InlineKeyboardButton(
            text=f"{current_index + 1}/{len(products)}", 
            callback_data="carousel_info"
        ))
        
        # Кнопка "Вперед"
        if len(products) > 1:
            next_index = (current_index + 1) % len(products)
            nav_buttons.append(InlineKeyboardButton(
                text="Вперед ➡️", 
                callback_data=f"carousel_next_{user_id}_{next_index}"
            ))
        
        if nav_buttons:
            markup_buttons.append(nav_buttons)
        
        markup = InlineKeyboardMarkup(inline_keyboard=markup_buttons)
        
        caption = f"🌿 **{product_name}**\n\n📝 {short_desc}"
        
        # Сохраняем информацию о карусели
        user_product_carousels[user_id] = {
            "products": products,
            "current_index": current_index,
            "message_id": None
        }
        
        # Отправляем с картинкой если есть
        if image_id and image_id.strip():
            try:
                sent_message = await message.answer_photo(
                    photo=image_id,
                    caption=caption,
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
                user_product_carousels[user_id]["message_id"] = sent_message.message_id
                return
            except Exception as e:
                print(f"Ошибка отправки фото {image_id}: {e}")
        
        # Fallback без картинки
        sent_message = await message.reply(
            caption,
            reply_markup=markup,
            parse_mode="Markdown"
        )
        user_product_carousels[user_id]["message_id"] = sent_message.message_id
        
    except Exception as e:
        print(f"Ошибка в send_product_carousel: {e}")
        await message.reply("❌ Произошла ошибка при отправке карусели продуктов.")

async def update_product_carousel(callback_query: types.CallbackQuery, user_id: int, new_index: int):
    """Обновляет карусель продуктов"""
    try:
        if user_id not in user_product_carousels:
            await callback_query.answer("Карусель не найдена", show_alert=True)
            return
        
        carousel_data = user_product_carousels[user_id]
        products = carousel_data["products"]
        
        if new_index >= len(products):
            await callback_query.answer("Индекс вне диапазона", show_alert=True)
            return
        
        product = products[new_index]
        product_name = product.get("product", "")
        url = product.get("url", "")
        image_id = product.get("image_id", "")
        short_desc = product.get("short_description", "")
        
        # Создаем кнопки навигации
        markup_buttons = []
        
        # Кнопка "Подробнее на сайте" только если URL не пустой
        if url and url.strip():
            markup_buttons.append([InlineKeyboardButton(
                text="📖 Подробнее на сайте", 
                url=url
            )])
        else:
            # Если URL пустой, добавляем кнопку консультанта
            markup_buttons.append([InlineKeyboardButton(
                text="✉️ Написать консультанту", 
                callback_data="write_to_natalya"
            )])
        
        # Кнопки навигации
        nav_buttons = []
        
        # Кнопка "Назад"
        if len(products) > 1:
            prev_index = (new_index - 1) % len(products)
            nav_buttons.append(InlineKeyboardButton(
                text="⬅️ Назад", 
                callback_data=f"carousel_prev_{user_id}_{prev_index}"
            ))
        
        # Индикатор позиции
        nav_buttons.append(InlineKeyboardButton(
            text=f"{new_index + 1}/{len(products)}", 
            callback_data="carousel_info"
        ))
        
        # Кнопка "Вперед"
        if len(products) > 1:
            next_index = (new_index + 1) % len(products)
            nav_buttons.append(InlineKeyboardButton(
                text="Вперед ➡️", 
                callback_data=f"carousel_next_{user_id}_{next_index}"
            ))
        
        if nav_buttons:
            markup_buttons.append(nav_buttons)
        
        markup = InlineKeyboardMarkup(inline_keyboard=markup_buttons)
        
        caption = f"🌿 **{product_name}**\n\n📝 {short_desc}"
        
        # Обновляем индекс
        carousel_data["current_index"] = new_index
        
        # Обновляем сообщение
        if image_id and image_id.strip():
            try:
                await callback_query.message.edit_media(
                    types.InputMediaPhoto(
                        media=image_id,
                        caption=caption,
                        parse_mode="Markdown"
                    ),
                    reply_markup=markup
                )
            except Exception as e:
                print(f"Ошибка обновления фото {image_id}: {e}")
                # Fallback - обновляем только текст
                await callback_query.message.edit_caption(
                    caption=caption,
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
        else:
            await callback_query.message.edit_caption(
                caption=caption,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        
        await callback_query.answer()
        
    except Exception as e:
        print(f"Ошибка в update_product_carousel: {e}")
        await callback_query.answer("❌ Ошибка обновления карусели", show_alert=True)

def extract_products_from_answer(answer: str) -> list:
    """Извлекает названия продуктов из ответа бота (только рекомендованные)"""
    try:
        import json
        import re
        
        products = []
        
        # Загружаем базы знаний для сопоставления
        all_products = []
        for kb_file in ["knowledge_base.json", "knowledge_base_new.json"]:
            try:
                with open(kb_file, "r", encoding="utf-8") as f:
                    kb_data = json.load(f)
                    all_products.extend(kb_data)
            except:
                continue
        
        # Разбиваем ответ на пронумерованные пункты рекомендаций
        # Ищем паттерны типа "1. Название продукта", "2. Название", etc.
        recommendation_pattern = r'(\d+)\.\s*\*?\*?([^-\n]+?)(?:\s*-|\s*\*\*|\n|$)'
        recommendations = re.findall(recommendation_pattern, answer, re.MULTILINE)
        
        recommended_products_text = []
        for number, product_text in recommendations:
            # Очищаем от форматирования Markdown
            clean_text = re.sub(r'\*\*?', '', product_text).strip()
            recommended_products_text.append(clean_text)
            print(f"🔍 Найдена рекомендация {number}: '{clean_text}'")
        
        # Если не найдены пронумерованные рекомендации, ищем в начале предложений
        if not recommended_products_text:
            # Ищем продукты, упомянутые в начале предложений после "рекомендую"
            sentences = re.split(r'[.!?]\s+', answer)
            for sentence in sentences:
                if any(word in sentence.lower() for word in ['рекомендую', 'советую', 'подойдет']):
                    recommended_products_text.append(sentence)
        
        # Ищем соответствие в базе знаний только для рекомендованных продуктов
        for product in all_products:
            product_name = product.get("product", "")
            if not product_name:
                continue
                
            # Проверяем различные варианты названия
            name_variants = [
                product_name,  # Полное название
                product_name.replace("-", " "),  # Без дефисов
                product_name.replace("-", "")   # Слитно
            ]
            
            # Добавляем сокращения только если они достаточно специфичны
            first_word = product_name.split()[0] if " " in product_name else product_name
            if len(first_word) > 3 and first_word.lower() not in ["витамин", "магний", "кальций"]:
                name_variants.append(first_word)
            
            # Ищем только в тексте рекомендаций, а не во всем ответе
            found_in_recommendations = False
            for rec_text in recommended_products_text:
                rec_text_lower = rec_text.lower()
                for variant in name_variants:
                    variant_lower = variant.lower()
                    # Ищем точное вхождение слова в рекомендациях
                    if re.search(r'\b' + re.escape(variant_lower) + r'\b', rec_text_lower):
                        found_in_recommendations = True
                        print(f"✅ Продукт '{product_name}' найден в рекомендации: '{rec_text}'")
                        break
                if found_in_recommendations:
                    break
            
            if found_in_recommendations:
                products.append({
                    "product": product_name,
                    "url": product.get("url", ""),
                    "image_id": product.get("image_id", ""),
                    "short_description": product.get("short_description", "")
                })
        
        # Убираем дубликаты
        unique_products = []
        seen_names = set()
        for product in products:
            product_name = product.get("product", "")
            if product_name not in seen_names:
                unique_products.append(product)
                seen_names.add(product_name)
        
        print(f"🎯 Извлечено {len(unique_products)} рекомендованных продуктов")
        return unique_products[:5]  # Максимум 5 продуктов
        
    except Exception as e:
        print(f"Ошибка извлечения продуктов: {e}")
        return []

async def handle_link_request_confirmation(message: types.Message):
    """Обрабатывает подтверждение запроса ссылки"""
    user_id = message.from_user.id
    
    if user_id not in user_product_context:
        await message.reply("🤔 Я не помню, о каких продуктах мы говорили. Задайте вопрос заново.")
        return
    
    products = user_product_context[user_id]
    
    if len(products) == 1:
        # Если продукт один - сразу отправляем ссылку
        await send_product_link(message, products[0])
        # Очищаем контекст
        del user_product_context[user_id]
    else:
        # Если продуктов несколько - просим уточнить
        products_list = ""
        for i, product in enumerate(products, 1):
            product_name = product.get("product", "")
            products_list += f"{i}. {product_name}\n"
        
        await message.reply(
            f"📋 **На какой продукт нужна ссылка?**\n\n{products_list}\n"
            f"💬 Напишите номер (например: 1) или название продукта (например: Аргент Макс)"
        )

async def handle_product_selection(message: types.Message):
    """Обрабатывает выбор продукта пользователем"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if user_id not in user_product_context:
        return  # Контекст утерян, продолжаем обычную обработку
    
    products = user_product_context[user_id]
    selected_product = None
    
    # Пытаемся определить выбранный продукт
    # 1. По номеру
    if text.isdigit():
        index = int(text) - 1
        if 0 <= index < len(products):
            selected_product = products[index]
    
    # 2. По названию (частичное совпадение)
    if not selected_product:
        text_lower = text.lower()
        for product in products:
            product_name = product.get("product", "")
            if text_lower in product_name.lower() or product_name.lower() in text_lower:
                selected_product = product
                break
    
    if selected_product:
        # Отправляем ссылку на выбранный продукт
        await send_product_link(message, selected_product)
        # Очищаем контекст
        del user_product_context[user_id]
    else:
        # Не смогли определить продукт
        products_list = ""
        for i, product in enumerate(products, 1):
            product_name = product.get("product", "")
            products_list += f"{i}. {product_name}\n"
        
        await message.reply(
            f"🤔 Не могу понять, какой продукт вы выбрали.\n\n"
            f"📋 **Доступные варианты:**\n{products_list}\n"
            f"💬 Напишите номер или точное название"
        )

async def send_all_products_list(message: types.Message, products: list):
    """Отправляет список всех продуктов с кнопками для выбора"""
    try:
        products_list = ""
        for i, product in enumerate(products, 1):
            product_name = product.get("product", "")
            products_list += f"{i}. **{product_name}**\n"
            if product.get('short_description'):
                products_list += f"   {product['short_description'][:100]}...\n"
            products_list += "\n"
        
        await message.reply(
            f"🌿 **Все доступные продукты:**\n\n{products_list}\n"
            f"💬 **Выберите продукт:**\n"
            f"• Напишите номер (например: 1)\n"
            f"• Или название продукта (например: Магний Плюс)\n\n"
            f"📋 *Ответьте на это сообщение, чтобы получить ссылку на выбранный продукт*",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"Ошибка отправки списка продуктов: {e}")
        await message.reply("❌ Произошла ошибка при отправке списка продуктов")

async def handle_additional_recommendations(message: types.Message):
    """Обрабатывает запросы на дополнительные рекомендации в контексте темы"""
    user_id = message.from_user.id
    
    try:
        # Определяем тему предыдущего разговора из контекста продуктов
        last_topic = None
        if user_id in user_product_context:
            context_products = user_product_context[user_id]
            
            # Анализируем продукты для определения темы
            if context_products:
                # Берем первый продукт для анализа темы
                first_product = context_products[0]
                product_name = first_product.get("product", "").lower()
                
                # Определяем тему по типам продуктов
                if any(keyword in product_name for keyword in ["аргент", "кошачий коготь", "ин-аурин", "барс"]):
                    last_topic = "иммунитет"
                elif any(keyword in product_name for keyword in ["витамин с", "оранж"]):
                    last_topic = "витамины"
                elif any(keyword in product_name for keyword in ["омега", "рыбий жир"]):
                    last_topic = "жирные кислоты"
                elif any(keyword in product_name for keyword in ["магний", "кальций"]):
                    last_topic = "минералы"
                elif any(keyword in product_name for keyword in ["bwl", "гепосин", "черного ореха"]):
                    last_topic = "антипаразитарные"
        
        print(f"🔍 Определена тема последнего разговора: {last_topic}")
        
        # Эффект печатания
        await send_typing_action(user_id, 2.0)
        
        # Если тема определена, ищем дополнительные продукты по той же теме
        if last_topic == "иммунитет":
            await handle_additional_immunity_products(message, user_id)
        elif last_topic in ["витамины", "жирные кислоты", "минералы"]:
            await handle_additional_supplements(message, user_id, last_topic)
        else:
            # Общий ответ если тема не определена или завершена
            await handle_general_additional_request(message, user_id, last_topic)
            
    except Exception as e:
        print(f"Ошибка обработки дополнительных рекомендаций: {e}")
        await message.reply(
            "❌ Произошла ошибка. Попробуйте уточнить запрос или обратитесь к консультанту."
        )

async def handle_additional_immunity_products(message: types.Message, user_id: int):
    """Обрабатывает запрос дополнительных продуктов для иммунитета"""
    from immunity_recommendations import IMMUNITY_SUPPORTING_PRODUCTS, IMMUNITY_INDIRECT_SUPPORT
    
    # Получаем уже рекомендованные продукты
    recommended_products = []
    if user_id in user_product_context:
        recommended_products = [p.get("product", "") for p in user_product_context[user_id]]
    
    # Ищем дополнительные продукты, которые еще не были рекомендованы
    additional_products = []
    
    # Сначала проверяем поддерживающие продукты (прямое действие)
    for product_info in IMMUNITY_SUPPORTING_PRODUCTS:
        if not any(product_info["name"] in rec for rec in recommended_products):
            additional_products.append(product_info)
    
    # Потом косвенного действия
    for product_info in IMMUNITY_INDIRECT_SUPPORT:
        if not any(product_info["name"] in rec for rec in recommended_products):
            additional_products.append(product_info)
    
    if additional_products:
        # Ограничиваем до 3-4 дополнительных продуктов
        additional_products = additional_products[:4]
        
        response = "Дополнительно для поддержки иммунитета можно рассмотреть:\n\n"
        
        new_context = []
        for i, product_info in enumerate(additional_products, 1):
            response += f"{i}. **{product_info['name']}** - {product_info['description']}\n\n"
            new_context.append({
                "product": product_info["name"],
                "url": "",  # Будет найден при запросе ссылки
                "image_id": "",
                "short_description": product_info["description"]
            })
        
        response += "Нужна ссылка на какой-то из продуктов?\n\n*📚 Рекомендация на основе данных с сайта Aurora*"
        
        # Обновляем контекст дополнительными продуктами
        user_product_context[user_id] = new_context
        
        await message.reply(response, parse_mode="Markdown")
    else:
        # Больше нет подходящих продуктов для иммунитета
        await message.reply(
            "🤔 Я уже рекомендовал основные продукты для иммунитета из нашего ассортимента.\n\n"
            "💡 Можете рассмотреть:\n"
            "• Комбинирование уже рекомендованных продуктов\n"
            "• Продукты для других аспектов здоровья\n"
            "• Обратиться к консультанту для индивидуального подбора\n\n"
            "Или спросите о продуктах для другой цели! 😊"
        )

async def handle_additional_supplements(message: types.Message, user_id: int, topic: str):
    """Обрабатывает запрос дополнительных БАДов по теме"""
    topic_names = {
        "витамины": "витаминов",
        "жирные кислоты": "жирных кислот", 
        "минералы": "минералов"
    }
    
    await message.reply(
        f"🤔 Я уже предложил основные варианты {topic_names.get(topic, 'по данной теме')} из нашего ассортимента.\n\n"
        f"💡 Рекомендую:\n"
        f"• Выбрать один из уже предложенных продуктов\n"
        f"• Уточнить конкретную потребность или цель\n"
        f"• Обратиться к консультанту за индивидуальным подбором\n\n"
        f"Или расскажите о другой цели - я подберу подходящие продукты! 😊"
    )

async def handle_general_additional_request(message: types.Message, user_id: int, last_topic: str):
    """Обрабатывает общий запрос дополнительных рекомендаций"""
    if last_topic == "антипаразитарные":
        await message.reply(
            "⚠️ Кажется, произошла ошибка - вы спрашивали о продуктах для иммунитета, "
            "а я перешел к антипаразитарным средствам.\n\n"
            "🔄 Давайте вернемся к вашему первоначальному запросу об иммунитете!\n\n"
            "Уточните, пожалуйста: какие именно продукты для иммунитета вас интересуют?"
        )
    else:
        await message.reply(
            "🤔 Чтобы дать точные рекомендации, уточните, пожалуйста:\n\n"
            "• Какая у вас цель? (иммунитет, печень, кожа, энергия...)\n"
            "• Есть ли конкретные предпочтения?\n\n"
            "💬 Например: \"Что для укрепления иммунитета?\" или \"Продукты для печени\"\n\n"
            "Так я смогу подобрать наиболее подходящие варианты! 😊"
        )

async def find_product_in_knowledge_base(product_name: str) -> dict:
    """Ищет полную информацию о продукте во всех базах знаний"""
    import json
    import os
    
    # Список файлов для поиска
    kb_files = [
        "knowledge_base.json",
        "knowledge_base_new.json", 
        "knowledge_base_fixed.json"
    ]
    
    for kb_file in kb_files:
        try:
            if os.path.exists(kb_file):
                with open(kb_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    for item in data:
                        if 'product' in item:
                            item_name = item['product']
                            # Проверяем различные варианты совпадения
                            if (product_name.lower() in item_name.lower() or 
                                item_name.lower() in product_name.lower() or
                                # Проверяем без скобок
                                product_name.split('(')[0].strip().lower() in item_name.lower() or
                                item_name.split('(')[0].strip().lower() in product_name.lower()):
                                print(f"🎯 Найден продукт в {kb_file}: {item_name}")
                                return item
        except Exception as e:
            print(f"⚠️ Ошибка чтения {kb_file}: {e}")
    
    print(f"❌ Продукт '{product_name}' не найден в базах данных")
    return None

async def send_product_link(message: types.Message, product: dict):
    """Отправляет ссылку на продукт с изображением"""
    try:
        # Поддерживаем оба варианта ключей для совместимости
        product_name = product.get("name", "") or product.get("product", "")
        url = product.get("url", "")
        image_id = product.get("image_id", "")
        short_desc = product.get("short_description", "")
        
        # Если URL или изображение отсутствуют, пытаемся найти полную информацию в базе данных
        if not url or not image_id:
            print(f"🔍 Поиск полной информации для продукта: {product_name}")
            full_product = await find_product_in_knowledge_base(product_name)
            if full_product:
                url = full_product.get("url", url)
                image_id = full_product.get("image_id", image_id)
                short_desc = full_product.get("short_description", short_desc)
                print(f"✅ Найдена полная информация: URL={bool(url)}, Image={bool(image_id)}")
        
        # Проверяем, что название продукта не пустое
        if not product_name:
            print(f"⚠️ Пустое название продукта: {product}")
            await message.reply("❌ Не удалось определить название продукта. Попробуйте еще раз.")
            return
        
        # Создаем кнопку с ссылкой только если URL не пустой
        markup_buttons = []
        if url and url.strip():
            markup_buttons.append([InlineKeyboardButton(
                text="📖 Подробнее на сайте", 
                url=url
            )])
        else:
            # Если URL пустой, добавляем кнопку консультанта
            markup_buttons.append([InlineKeyboardButton(
                text="✉️ Написать консультанту", 
                callback_data="write_to_natalya"
            )])
        
        markup = InlineKeyboardMarkup(inline_keyboard=markup_buttons)
        
        caption = f"🌿 **{product_name}**\n\n📝 {short_desc}"
        
        # Отправляем с картинкой если есть
        if image_id and image_id.strip():
            try:
                await message.answer_photo(
                    photo=image_id,
                    caption=caption,
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
                return
            except Exception as e:
                print(f"Ошибка отправки фото {image_id}: {e}")
        
        # Fallback без картинки
        await message.reply(
            caption,
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"Ошибка отправки ссылки на продукт: {e}")
        await message.reply("❌ Произошла ошибка при отправке ссылки")

async def main():
    print("🚀 Запуск бота...")
    print(f"🤖 BOT_TOKEN: {'✅ настроен' if BOT_TOKEN and BOT_TOKEN != 'your_bot_token_here' else '❌ не настроен'}")
    print(f"👤 ADMIN_ID: {'✅ настроен' if ADMIN_ID and ADMIN_ID != 0 else '❌ не настроен'}")
    print(f"🧠 AI функции: {'✅ активны' if AI_ENABLED else '❌ отключены'}")
    
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())