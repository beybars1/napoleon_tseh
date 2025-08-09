#!/usr/bin/env python3
"""
Script to run Telegram bot in development mode with polling.

Usage:
    python app/scripts/run_telegram_bot.py

This script runs the bot with polling instead of webhooks, which is perfect for development.
For production, use webhooks through the FastAPI webhook endpoints.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.telegram_bot_service import telegram_bot_service
from app.core.config import settings
import structlog

logger = structlog.get_logger()


async def main():
    """Main function to run the Telegram bot"""
    
    print("🤖 Starting Napoleon-Tseh Telegram Bot...")
    print(f"📋 Business: {settings.BUSINESS_NAME}")
    print(f"🔧 Mode: Development (Polling)")
    print(f"🌐 Backend: http://localhost:8000")
    print(f"📞 Phone: {settings.BUSINESS_PHONE}")
    print(f"📧 Email: {settings.BUSINESS_EMAIL}")
    print("=" * 60)
    
    try:
        # Check if bot token is configured
        if not settings.TELEGRAM_BOT_TOKEN:
            print("❌ TELEGRAM_BOT_TOKEN not configured in environment variables!")
            print("   Please set TELEGRAM_BOT_TOKEN in your .env file")
            return
        
        print("✅ Bot token configured")
        
        # Check if OpenAI API key is configured
        if not settings.OPENAI_API_KEY:
            print("⚠️  OPENAI_API_KEY not configured - AI features will be limited")
        else:
            print("✅ OpenAI API key configured")
        
        print("\n🚀 Starting bot with polling...")
        print("💬 Send /start to your bot to begin!")
        print("⏹️  Press Ctrl+C to stop the bot")
        print("=" * 60)
        
        # Run the bot
        await telegram_bot_service.run_polling()
        
    except KeyboardInterrupt:
        print("\n⏹️  Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        print(f"❌ Error: {e}")
    
    print("\n👋 Goodbye!")


if __name__ == "__main__":
    # Run the bot
    asyncio.run(main()) 