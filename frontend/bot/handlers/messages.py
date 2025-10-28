"""
Message handlers - Handle user messages with full LLM integration
"""
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import StateFilter
import logging

# Импортируем сервисы
from frontend.services.llm_service import llm_service
from frontend.services.search_service import search_service
from frontend.services.conversation_service import conversation_service

logger = logging.getLogger(__name__)

# Создаем router для сообщений
router = Router()


@router.message(StateFilter(None))
async def handle_message(message: Message):
    """
    Обработка всех пользовательских сообщений
    
    Процесс:
    1. Сохранение сообщения в историю
    2. Поиск продуктов через search_service
    3. Обработка через LLM (с кэшем, промптами, special handlers)
    4. Сохранение ответа в историю
    5. Отправка ответа пользователю
    """
    user_id = message.from_user.id
    user_text = message.text
    
    logger.info(f"User {user_id} sent message: {user_text[:50]}...")
    
    try:
        # ==========================================
        # 1. СОХРАНЕНИЕ СООБЩЕНИЯ В ИСТОРИЮ
        # ==========================================
        conversation_service.add_message(
            user_id=user_id,
            role="user",
            content=user_text
        )
        
        # ==========================================
        # 2. ПОИСК ПРОДУКТОВ
        # ==========================================
        # Показываем индикатор "печатает..."
        await message.bot.send_chat_action(message.chat.id, "typing")
        
        logger.info(f"Searching products for query: {user_text[:50]}...")
        search_results = await search_service.search_products(
            query=user_text,
            limit=8  # Ищем до 8 продуктов
        )
        
        # Извлекаем продукты из результатов поиска
        products = [result.product for result in search_results]
        
        logger.info(f"Found {len(products)} products")
        
        # ==========================================
        # 3. ОБРАБОТКА ЧЕРЕЗ LLM
        # ==========================================
        logger.info("Processing through LLM service...")
        llm_response = await llm_service.process_query(
            user_query=user_text,
            products=products
        )
        
        response_text = llm_response.text
        
        # Добавляем информацию о кэше если ответ из кэша
        if llm_response.cached:
            logger.info("Response from cache")
        
        # ==========================================
        # 4. СОХРАНЕНИЕ ОТВЕТА В ИСТОРИЮ
        # ==========================================
        conversation_service.add_message(
            user_id=user_id,
            role="assistant",
            content=response_text,
            metadata={
                "products_count": len(products),
                "intent": llm_response.intent,
                "confidence": llm_response.confidence,
                "cached": llm_response.cached
            }
        )
        
        # Сохраняем продукты для возможного follow-up
        if products:
            conversation_service.set_last_products(user_id, products)
        
        # ==========================================
        # 5. ОТПРАВКА ОТВЕТА
        # ==========================================
        # Разбиваем длинный ответ на части (Telegram limit: 4096 символов)
        max_length = 4000
        
        if len(response_text) <= max_length:
            await message.answer(response_text)
        else:
            # Разбиваем на части
            parts = []
            current_part = ""
            
            for line in response_text.split('\n'):
                if len(current_part) + len(line) + 1 <= max_length:
                    current_part += line + '\n'
                else:
                    if current_part:
                        parts.append(current_part.strip())
                    current_part = line + '\n'
            
            if current_part:
                parts.append(current_part.strip())
            
            # Отправляем части
            for i, part in enumerate(parts, 1):
                if i > 1:
                    await message.bot.send_chat_action(message.chat.id, "typing")
                await message.answer(part)
        
        logger.info(f"Response sent to user {user_id}")
        
    except Exception as e:
        import time
        error_id = f"ERR-{int(time.time())}-{user_id}"
        logger.error(f"Error {error_id}: {e}", exc_info=True)
        
        # Отправляем сообщение об ошибке с ID
        await message.answer(
            f"😔 Извините, произошла ошибка при обработке вашего запроса.\n\n"
            f"🆔 Код ошибки: `{error_id}`\n\n"
            "Попробуйте:\n"
            "• Переформулировать вопрос\n"
            "• Написать /help для справки\n"
            "• Написать /start для начала\n\n"
            "💬 Если проблема повторяется, сообщите администратору код ошибки."
        )