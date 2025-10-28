"""
Command handlers - /start, /help, /products, /categories with service integration
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import logging

# Импортируем сервисы
from frontend.services.search_service import search_service
from frontend.services.llm_service import llm_service
from frontend.services.conversation_service import conversation_service

logger = logging.getLogger(__name__)

# Создаем router для команд
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    user_id = message.from_user.id
    username = message.from_user.full_name
    
    logger.info(f"User {user_id} ({username}) started bot")
    
    # Очищаем предыдущий контекст разговора
    conversation_service.clear_context(user_id)
    
    welcome_text = (
        f"🌿 Привет, {username}! Я AI-помощник AURORA!\n\n"
        "Я помогу вам найти подходящие продукты для здоровья.\n"
        "Просто напишите, что вас интересует, например:\n\n"
        "• Витамины для иммунитета\n"
        "• Омега-3 для сердца\n"
        "• Магний для сна\n"
        "• Пробиотики для пищеварения\n"
        "• Коллаген для кожи и волос\n\n"
        "💡 Используйте /help для получения подробной справки"
    )
    
    await message.answer(welcome_text)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    logger.info(f"User {message.from_user.id} requested help")
    
    help_text = (
        "🔍 **Как пользоваться ботом:**\n\n"
        "1️⃣ Напишите ваш вопрос или потребность\n"
        "2️⃣ Я найду подходящие продукты\n"
        "3️⃣ Расскажу подробности о каждом\n\n"
        "**Примеры запросов:**\n"
        "• 'Нужны витамины для иммунитета'\n"
        "• 'Что поможет с бессонницей?'\n"
        "• 'Омега-3 для сердца'\n"
        "• 'Продукты для кожи и волос'\n"
        "• 'Противовирусное средство'\n"
        "• 'Для печени'\n\n"
        "**Доступные команды:**\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n"
        "/products - Показать все продукты\n"
        "/categories - Показать категории\n"
        "/stats - Статистика использования\n"
        "/clear - Очистить историю разговора\n\n"
        "💬 Просто напишите ваш вопрос, и я помогу!"
    )
    
    await message.answer(help_text)


@router.message(Command("products"))
async def cmd_products(message: Message):
    """Handle /products command - показать все продукты"""
    user_id = message.from_user.id
    logger.info(f"User {user_id} requested products list")
    
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    try:
        # Получаем все продукты (локальный поиск со звездочкой)
        search_results = await search_service.search_products(
            query="",  # Пустой запрос вернет все или большинство
            limit=20
        )
        
        if not search_results:
            await message.answer(
                "📦 Список продуктов временно недоступен.\n"
                "Попробуйте задать конкретный вопрос о продуктах."
            )
            return
        
        # Группируем по категориям
        products_by_category = {}
        for result in search_results[:20]:  # Ограничиваем 20 продуктами
            product = result.product
            category = product.get('category', 'Разное')
            
            if category not in products_by_category:
                products_by_category[category] = []
            
            products_by_category[category].append(product.get('product', 'Без названия'))
        
        # Формируем ответ
        response_parts = ["📦 **Наши продукты:**\n"]
        
        for category, products in sorted(products_by_category.items()):
            response_parts.append(f"\n**{category}:**")
            for product_name in products[:10]:  # Макс 10 продуктов на категорию
                response_parts.append(f"  • {product_name}")
        
        response_parts.append("\n\n💡 Напишите название продукта для подробной информации")
        
        response_text = "\n".join(response_parts)
        
        await message.answer(response_text)
        
    except Exception as e:
        logger.error(f"Error in /products command: {e}", exc_info=True)
        await message.answer(
            "😔 Произошла ошибка при загрузке списка продуктов.\n"
            "Попробуйте позже или напишите конкретный запрос."
        )


@router.message(Command("categories"))
async def cmd_categories(message: Message):
    """Handle /categories command - показать категории"""
    user_id = message.from_user.id
    logger.info(f"User {user_id} requested categories")
    
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    try:
        # Получаем категории через search service
        categories = await search_service.get_categories()
        
        if not categories:
            await message.answer(
                "📂 Список категорий временно недоступен.\n"
                "Попробуйте задать вопрос о конкретной потребности."
            )
            return
        
        response_parts = [
            "📂 **Категории продуктов:**\n",
            "Выберите интересующую категорию или напишите свой запрос:\n"
        ]
        
        for i, category in enumerate(categories, 1):
            response_parts.append(f"{i}. {category}")
        
        response_parts.append(
            "\n💡 Напишите название категории или свой вопрос"
        )
        
        response_text = "\n".join(response_parts)
        
        await message.answer(response_text)
        
    except Exception as e:
        logger.error(f"Error in /categories command: {e}", exc_info=True)
        await message.answer(
            "😔 Произошла ошибка при загрузке категорий.\n"
            "Попробуйте позже."
        )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Handle /stats command - статистика"""
    user_id = message.from_user.id
    logger.info(f"User {user_id} requested stats")
    
    try:
        # Статистика кэша
        cache_stats = llm_service.get_cache_stats()
        
        # Статистика разговора
        conv_stats = conversation_service.get_stats()
        
        response_text = (
            "📊 **Статистика:**\n\n"
            f"**Кэш LLM:**\n"
            f"• Размер: {cache_stats['size']}/{cache_stats['max_size']}\n"
            f"• Попаданий: {cache_stats['total_hits']}\n"
            f"• Среднее: {cache_stats['avg_hits']:.1f}\n\n"
            f"**Разговоры:**\n"
            f"• Активных: {conv_stats['total_conversations']}\n"
            f"• Сообщений: {conv_stats['total_messages']}\n"
        )
        
        await message.answer(response_text)
        
    except Exception as e:
        logger.error(f"Error in /stats command: {e}", exc_info=True)
        await message.answer("😔 Ошибка получения статистики")


@router.message(Command("clear"))
async def cmd_clear(message: Message):
    """Handle /clear command - очистить историю"""
    user_id = message.from_user.id
    logger.info(f"User {user_id} requested clear history")
    
    conversation_service.clear_context(user_id)
    
    await message.answer(
        "🗑️ История разговора очищена!\n\n"
        "Можете начать новый разговор."
    )