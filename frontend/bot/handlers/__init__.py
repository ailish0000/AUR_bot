"""
Handlers package - Register all handlers
"""
from aiogram import Dispatcher
from . import commands, messages


def register_handlers(dp: Dispatcher):
    """Register all bot handlers"""
    
    # Регистрируем handlers
    dp.include_router(commands.router)
    dp.include_router(messages.router)
    
    print("✓ Handlers registered successfully")