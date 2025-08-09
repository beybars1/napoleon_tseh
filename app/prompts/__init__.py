"""
Prompts package for Napoleon-Tseh AI services

This package contains all AI prompts, templates, and response configurations
used throughout the application.
"""

from .telegram_bot_prompts import TelegramBotPrompts, TelegramBotTemplates

__all__ = ['TelegramBotPrompts', 'TelegramBotTemplates'] 