#!/usr/bin/env python3
"""
Telegram Bot Troubleshooting Script

This script tests your Telegram bot configuration and helps diagnose issues.

Usage:
    python app/scripts/test_telegram_bot.py
"""

import asyncio
import sys
import os
import json
import httpx
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from app.core.config import settings
    from app.services.telegram_bot_service import telegram_bot_service
    from app.services.ai_service import AIService
    from app.core.database import get_async_session
    import structlog
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the project root directory and dependencies are installed")
    sys.exit(1)

logger = structlog.get_logger()


class TelegramBotTester:
    """Comprehensive Telegram bot testing utility"""
    
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.api_base = "https://api.telegram.org/bot"
        self.http_client = httpx.AsyncClient()
    
    async def test_all(self):
        """Run all tests"""
        print("🔍 TELEGRAM BOT DIAGNOSTIC TESTS")
        print("=" * 60)
        
        # Test 1: Environment Variables
        await self.test_environment_variables()
        print()
        
        # Test 2: Bot Token Validation
        await self.test_bot_token()
        print()
        
        # Test 3: Bot Info
        await self.test_bot_info()
        print()
        
        # Test 4: OpenAI Connection
        await self.test_openai_connection()
        print()
        
        # Test 5: Database Connection
        await self.test_database_connection()
        print()
        
        # Test 6: Bot Service Initialization
        await self.test_bot_service()
        print()
        
        # Test 7: Webhook Status
        await self.test_webhook_status()
        print()
        
        # Test 8: Send Test Message (if bot username provided)
        bot_info = await self.get_bot_info()
        if bot_info and bot_info.get('username'):
            print("💡 NEXT STEPS:")
            print(f"1. Open Telegram and search for @{bot_info['username']}")
            print("2. Send /start to test the bot")
            print("3. If no response, run the bot in polling mode:")
            print("   python app/scripts/run_telegram_bot.py")
        
        await self.http_client.aclose()
    
    async def test_environment_variables(self):
        """Test environment variable configuration"""
        print("📋 1. Environment Variables Check")
        
        # Check required variables
        required_vars = {
            'TELEGRAM_BOT_TOKEN': self.token,
            'OPENAI_API_KEY': getattr(settings, 'OPENAI_API_KEY', None),
            'BUSINESS_NAME': getattr(settings, 'BUSINESS_NAME', None),
            'BUSINESS_PHONE': getattr(settings, 'BUSINESS_PHONE', None),
            'BUSINESS_EMAIL': getattr(settings, 'BUSINESS_EMAIL', None),
        }
        
        for var_name, var_value in required_vars.items():
            if var_value:
                if var_name in ['TELEGRAM_BOT_TOKEN', 'OPENAI_API_KEY']:
                    print(f"   ✅ {var_name}: {var_value[:10]}...{var_value[-4:]}")
                else:
                    print(f"   ✅ {var_name}: {var_value}")
            else:
                print(f"   ❌ {var_name}: Not set")
    
    async def test_bot_token(self):
        """Test if bot token is valid"""
        print("🔑 2. Bot Token Validation")
        
        if not self.token:
            print("   ❌ TELEGRAM_BOT_TOKEN not configured!")
            print("   💡 Add TELEGRAM_BOT_TOKEN=your_token_here to your .env file")
            return False
        
        try:
            response = await self.http_client.get(f"{self.api_base}{self.token}/getMe")
            if response.status_code == 200:
                print("   ✅ Bot token is valid")
                return True
            else:
                print(f"   ❌ Invalid bot token (HTTP {response.status_code})")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Error testing bot token: {e}")
            return False
    
    async def test_bot_info(self):
        """Get and display bot information"""
        print("🤖 3. Bot Information")
        
        bot_info = await self.get_bot_info()
        if bot_info:
            print(f"   ✅ Bot Name: {bot_info.get('first_name', 'Unknown')}")
            print(f"   ✅ Bot Username: @{bot_info.get('username', 'Unknown')}")
            print(f"   ✅ Bot ID: {bot_info.get('id', 'Unknown')}")
            print(f"   ✅ Can Join Groups: {bot_info.get('can_join_groups', False)}")
            print(f"   ✅ Can Read All Group Messages: {bot_info.get('can_read_all_group_messages', False)}")
        else:
            print("   ❌ Could not retrieve bot information")
    
    async def get_bot_info(self):
        """Helper to get bot info"""
        try:
            response = await self.http_client.get(f"{self.api_base}{self.token}/getMe")
            if response.status_code == 200:
                return response.json()['result']
            return None
        except:
            return None
    
    async def test_openai_connection(self):
        """Test OpenAI API connection"""
        print("🧠 4. OpenAI API Connection")
        
        try:
            ai_service = AIService()
            print("   ✅ AI Service initialized")
            
            if not settings.OPENAI_API_KEY:
                print("   ⚠️  OpenAI API key not configured - AI features will be limited")
            else:
                print("   ✅ OpenAI API key configured")
                
        except Exception as e:
            print(f"   ❌ Error initializing AI service: {e}")
    
    async def test_database_connection(self):
        """Test database connection"""
        print("🗄️  5. Database Connection")
        
        try:
            async for db in get_async_session():
                print("   ✅ Database connection successful")
                break
        except Exception as e:
            print(f"   ❌ Database connection failed: {e}")
            print("   💡 Make sure PostgreSQL is running and DATABASE_URL is correct")
    
    async def test_bot_service(self):
        """Test bot service initialization"""
        print("⚙️  6. Bot Service Initialization")
        
        try:
            # Test if bot service initializes without errors
            bot_service = telegram_bot_service
            print("   ✅ Telegram bot service initialized")
            
            # Test if handlers are set up
            if hasattr(bot_service, 'application') and bot_service.application.handlers:
                print(f"   ✅ Bot handlers configured ({len(bot_service.application.handlers)} handlers)")
            else:
                print("   ⚠️  Bot handlers not properly configured")
                
        except Exception as e:
            print(f"   ❌ Error initializing bot service: {e}")
    
    async def test_webhook_status(self):
        """Check webhook status"""
        print("🔗 7. Webhook Status")
        
        try:
            response = await self.http_client.get(f"{self.api_base}{self.token}/getWebhookInfo")
            if response.status_code == 200:
                webhook_info = response.json()['result']
                
                if webhook_info.get('url'):
                    print(f"   ℹ️  Webhook URL: {webhook_info['url']}")
                    print(f"   ℹ️  Pending Updates: {webhook_info.get('pending_update_count', 0)}")
                    
                    if webhook_info.get('last_error_message'):
                        print(f"   ⚠️  Last Error: {webhook_info['last_error_message']}")
                    else:
                        print("   ✅ No webhook errors")
                else:
                    print("   ℹ️  No webhook configured (using polling mode)")
                    print("   💡 This is fine for development - use run_telegram_bot.py")
                    
        except Exception as e:
            print(f"   ❌ Error checking webhook status: {e}")
    
    async def delete_webhook(self):
        """Delete existing webhook (for development)"""
        print("🗑️  Deleting webhook for development mode...")
        
        try:
            response = await self.http_client.post(f"{self.api_base}{self.token}/deleteWebhook")
            if response.status_code == 200:
                print("   ✅ Webhook deleted successfully")
                return True
            else:
                print(f"   ❌ Failed to delete webhook: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Error deleting webhook: {e}")
            return False


async def main():
    """Main testing function"""
    tester = TelegramBotTester()
    
    # Check if we should delete webhook
    if len(sys.argv) > 1 and sys.argv[1] == '--delete-webhook':
        await tester.delete_webhook()
        print("\n💡 Now you can run: python app/scripts/run_telegram_bot.py")
        return
    
    await tester.test_all()
    
    print("\n" + "=" * 60)
    print("🛠️  TROUBLESHOOTING GUIDE:")
    print()
    print("If bot not responding to /start:")
    print("1. Make sure bot token is valid (check test results above)")
    print("2. Delete any existing webhook: python app/scripts/test_telegram_bot.py --delete-webhook")
    print("3. Run bot in polling mode: python app/scripts/run_telegram_bot.py")
    print("4. Open Telegram, search for your bot, and send /start")
    print()
    print("If still not working:")
    print("- Check if bot is blocked or restricted")
    print("- Verify bot username is correct")
    print("- Make sure you're messaging the right bot")
    print("- Check bot privacy settings with @BotFather")


if __name__ == "__main__":
    asyncio.run(main()) 