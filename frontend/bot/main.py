"""
Main bot file - Entry point for Telegram bot
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from frontend.config.settings import settings

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=settings.LOG_FILE if settings.LOG_FILE else None
)

logger = logging.getLogger(__name__)


# Инициализация бота и диспетчера
bot = Bot(token=settings.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def on_startup():
    """Actions on bot startup"""
    logger.info("Bot starting...")
    logger.info(f"Bot name: {settings.BOT_NAME}")
    logger.info(f"Backend API: {settings.BACKEND_API_URL}")
    logger.info(f"Smart search: {settings.ENABLE_SMART_SEARCH}")
    logger.info(f"Recommendations: {settings.ENABLE_RECOMMENDATIONS}")


async def on_shutdown():
    """Actions on bot shutdown"""
    logger.info("Bot shutting down...")
    await bot.session.close()


async def main():
    """Main function"""
    try:
        # Регистрируем обработчики startup/shutdown
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        # Регистрируем handlers
        from frontend.bot.handlers import register_handlers
        register_handlers(dp)
        
        # Получаем информацию о боте для проверки токена
        try:
            me = await bot.get_me()
            logger.info(f"Bot authenticated: {me.full_name} (@{me.username})")
        except Exception as e:
            logger.error(f"Failed to authenticate bot: {e}")
            logger.error("Please check your BOT_TOKEN in .env file")
            return
        
        # Удаляем webhook если был установлен
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook deleted successfully")
        except Exception as e:
            logger.warning(f"Could not delete webhook: {e}")
            logger.warning("Continuing anyway...")
        
        # Запускаем polling
        logger.info("Starting polling...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
    finally:
        await on_shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
