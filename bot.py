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
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_natalya")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
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
        [InlineKeyboardButton(text="Другой город", callback_data="city_other")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
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
    
    # Проверяем, выбирает ли пользователь продукт по номеру или названию
    # Только если это короткий ответ (номер или название продукта)
    if user_id in user_product_context and len(text) < 50:
        # Проверяем, что это действительно выбор продукта, а не новый вопрос
        if text.isdigit() or any(word.lower() in text.lower() for word in [
            "аргент", "гепосин", "симбион", "еломил", "bwl", "черного ореха", "солберри", "битерон"
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
    
    # Очищаем контекст продуктов при новых вопросах (если это не короткий ответ)
    if len(text) > 20 and user_id in user_product_context:
        # Если это новый вопрос, а не ответ на выбор продукта
        question_indicators = ["что", "какие", "как", "где", "когда", "почему", "зачем", "расскажи", "покажи", "есть ли"]
        if any(indicator in text.lower() for indicator in question_indicators):
            del user_product_context[user_id]
    
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
            
            # ОТКЛЮЧЕНО: Проверяем, нужно ли использовать пошаговые рекомендации
            # Теперь всегда используем обычный текстовый ответ через LLM
            # if processed_message.intent == Intent.PRODUCT_SELECTION:
            #     # Получаем рекомендации продуктов
            #     recommendations = recommendation_manager.get_recommendations(
            #         processed_message.expanded_query, limit=3
            #     )
            #     
            #     if recommendations:
            #         # Сохраняем рекомендации для пользователя
            #         user_recommendations[user_id] = recommendations
            #         
            #         # Отправляем первую рекомендацию
            #         await send_recommendation(message, user_id, 1)
            #         return
            
            # Обработка запросов о регистрации
            if processed_message.intent == Intent.REGISTRATION:
                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="🔗 Регистрация на сайте", 
                        url="https://aur-ora.com/auth/registration/666282189484/"
                    )],
                    [InlineKeyboardButton(
                        text="◀️ Главное меню", 
                        callback_data="back_to_main"
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
                    "Если нужна помощь с регистрацией, обратитесь к Наталье.",
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
            
            answer = enhanced_llm.process_query(text)
            
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
                
                # Обрезаем ответ для первого сообщения
                answer = answer[:999]
                last_space = answer.rfind(' ')
                if last_space > 800:
                    answer = answer[:last_space]
            
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
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
            ])
            
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
                [InlineKeyboardButton(text="✉️ Написать ещё", callback_data="write_to_natalya")],
                [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
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
            
            # Находим где обрезали текст (первые 999 символов)
            first_part_length = 999
            last_space = full_answer[:999].rfind(' ')
            if last_space > 800:
                first_part_length = last_space
            
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

async def handle_product_link_request(message: types.Message, processed_message):
    """Обрабатывает запросы ссылок на конкретные продукты"""
    user_id = message.from_user.id
    
    try:
        # Ищем продукт в базе знаний
        import json
        
        # Извлекаем название продукта из сущностей или текста
        product_name = ""
        if processed_message.entities:
            for entity in processed_message.entities:
                if entity.label == "PRODUCT":
                    product_name = entity.text
                    break
        
        # Если не нашли в сущностях, пытаемся найти в тексте
        if not product_name:
            text_words = processed_message.text.lower().split()
            # Ищем в обеих базах знаний
            found_products = []
            
            for kb_file in ["knowledge_base.json", "knowledge_base_new.json"]:
                try:
                    with open(kb_file, "r", encoding="utf-8") as f:
                        kb_data = json.load(f)
                    
                    for item in kb_data:
                        product = item.get("product", "").lower()
                        # Проверяем вхождение слов из запроса в название продукта
                        for word in text_words:
                            if len(word) > 2 and word in product:
                                found_products.append(item)
                                break
                                
                except Exception as e:
                    print(f"Ошибка чтения {kb_file}: {e}")
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
        
        # Эффект печатания
        await send_typing_action(user_id, 2.0)
        
        if found_products:
            # Берем первый найденный продукт
            product = found_products[0]
            product_name = product.get("product", "")
            url = product.get("url", "")
            image_id = product.get("image_id", "")
            short_desc = product.get("short_description", "")
            
            # Создаем кнопку с ссылкой
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="📖 Подробнее на сайте", 
                    url=url
                )]
            ])
            
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
            # Продукт не найден
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="✉️ Написать консультанту", 
                    callback_data="write_to_natalya"
                )],
                [InlineKeyboardButton(
                    text="◀️ Главное меню", 
                    callback_data="back_to_main"
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

def extract_products_from_answer(answer: str) -> list:
    """Извлекает названия продуктов из ответа бота"""
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
        
        # Ищем упоминания продуктов в ответе
        for product in all_products:
            product_name = product.get("product", "")
            if not product_name:
                continue
                
            # Проверяем различные варианты названия
            name_variants = [
                product_name,
                product_name.replace("-", " "),
                product_name.replace("-", ""),
                product_name.split()[0] if " " in product_name else product_name
            ]
            
            # Более точный поиск - ищем полные слова
            answer_lower = answer.lower()
            for variant in name_variants:
                variant_lower = variant.lower()
                # Ищем точное вхождение слова
                if re.search(r'\b' + re.escape(variant_lower) + r'\b', answer_lower):
                    products.append({
                        "name": product_name,
                        "url": product.get("url", ""),
                        "image_id": product.get("image_id", ""),
                        "short_description": product.get("short_description", "")
                    })
                    break
        
        # Убираем дубликаты
        unique_products = []
        seen_names = set()
        for product in products:
            if product["name"] not in seen_names:
                unique_products.append(product)
                seen_names.add(product["name"])
        
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
            products_list += f"{i}. {product['name']}\n"
        
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
            if text_lower in product['name'].lower() or product['name'].lower() in text_lower:
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
            products_list += f"{i}. {product['name']}\n"
        
        await message.reply(
            f"🤔 Не могу понять, какой продукт вы выбрали.\n\n"
            f"📋 **Доступные варианты:**\n{products_list}\n"
            f"💬 Напишите номер или точное название"
        )

async def send_product_link(message: types.Message, product: dict):
    """Отправляет ссылку на продукт с изображением"""
    try:
        product_name = product.get("name", "")
        url = product.get("url", "")
        image_id = product.get("image_id", "")
        short_desc = product.get("short_description", "")
        
        # Создаем кнопку с ссылкой
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📖 Подробнее на сайте", 
                url=url
            )]
        ])
        
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