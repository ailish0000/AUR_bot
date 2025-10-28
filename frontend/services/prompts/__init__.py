"""
Prompts package - System prompts for LLM
"""
from .prompt_manager import PromptManager, get_prompt_manager, IntentType

__all__ = ["PromptManager", "get_prompt_manager", "IntentType"]
