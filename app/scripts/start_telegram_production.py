#!/usr/bin/env python3
"""
Production startup script for Telegram bot with webhook configuration
"""

import asyncio
import sys
import os
import httpx
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.services.telegram_bot_service import telegram_bot_service
import structlog

logger = structlog.get_logger()


async def setup_production_webhook(domain: str):
    """Setup webhook for production deployment"""
    try:
        # Construct webhook URL
        webhook_url = f"https://{domain}/api/v1/webhooks/telegram"
        
        print(f"🔧 Setting up Telegram webhook for production...")
        print(f"📡 Domain: {domain}")
        print(f"🔗 Webhook URL: {webhook_url}")
        
        # Delete any existing webhook
        await telegram_bot_service.bot.delete_webhook()
        print("✅ Cleared existing webhook")
        
        # Set new webhook
        await telegram_bot_service.set_webhook(webhook_url)
        print("✅ Webhook configured")
        
        # Verify webhook
        webhook_info = await telegram_bot_service.bot.get_webhook_info()
        
        if webhook_info.url:
            print(f"🎉 SUCCESS! Webhook is active")
            print(f"📊 Pending updates: {webhook_info.pending_update_count}")
            print(f"🔗 Active URL: {webhook_info.url}")
            
            if webhook_info.last_error_message:
                print(f"⚠️  Last error: {webhook_info.last_error_message}")
            
            return True
        else:
            print("❌ ERROR: Webhook not set properly")
            return False
            
    except Exception as e:
        print(f"❌ ERROR setting up webhook: {e}")
        return False


async def test_fastapi_endpoint(domain: str):
    """Test if the FastAPI webhook endpoint is accessible"""
    try:
        test_url = f"https://{domain}/api/v1/webhooks/telegram/webhook_info"
        
        print(f"🧪 Testing FastAPI endpoint: {test_url}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(test_url)
            
        if response.status_code == 200:
            print("✅ FastAPI webhook endpoint is accessible")
            return True
        else:
            print(f"⚠️  FastAPI endpoint returned status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Cannot reach FastAPI endpoint: {e}")
        return False


async def main():
    """Main function for production setup"""
    print("🤖 TELEGRAM BOT PRODUCTION SETUP")
    print("=" * 50)
    
    # Check if domain is provided
    if len(sys.argv) < 2:
        print("""
❌ ERROR: Domain not provided

USAGE:
    python app/scripts/start_telegram_production.py your-domain.com

EXAMPLES:
    python app/scripts/start_telegram_production.py napoleon-tseh.com
    python app/scripts/start_telegram_production.py api.yourbakery.com
    python app/scripts/start_telegram_production.py 123.45.67.89:8000

REQUIREMENTS:
    - Domain must be accessible via HTTPS
    - FastAPI server must be running on the domain
    - SSL certificate must be valid
    - Port 443 (HTTPS) must be open

DEVELOPMENT MODE:
    For local development, use: python app/scripts/run_telegram_bot.py
        """)
        sys.exit(1)
    
    domain = sys.argv[1].strip()
    
    # Validate domain format
    if not domain:
        print("❌ ERROR: Empty domain provided")
        sys.exit(1)
    
    # Remove protocol if provided
    domain = domain.replace("https://", "").replace("http://", "")
    
    print(f"🌐 Target domain: {domain}")
    print(f"🔑 Bot token: {settings.TELEGRAM_BOT_TOKEN[:10]}...")
    print()
    
    # Test FastAPI endpoint first
    print("STEP 1: Testing FastAPI endpoint...")
    endpoint_ok = await test_fastapi_endpoint(domain)
    
    if not endpoint_ok:
        print("""
⚠️  WARNING: FastAPI endpoint is not accessible!

Make sure:
1. FastAPI server is running: uvicorn app.main:app --host 0.0.0.0 --port 8000
2. Nginx is configured with SSL
3. Domain points to your server
4. Port 443 is open and forwarding to FastAPI

You can still continue, but the webhook may not work.
        """)
        
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            sys.exit(1)
    
    print()
    print("STEP 2: Configuring Telegram webhook...")
    
    # Setup webhook
    webhook_ok = await setup_production_webhook(domain)
    
    if webhook_ok:
        print()
        print("🎉 PRODUCTION SETUP COMPLETE!")
        print("=" * 50)
        print("✅ Telegram webhook is active")
        print("✅ Bot will receive messages via FastAPI")
        print("✅ Polling mode is disabled")
        print()
        print("📱 TEST YOUR BOT:")
        print("   Send a message to your bot on Telegram")
        print("   Check FastAPI logs for incoming webhooks")
        print()
        print("🔧 MONITORING:")
        print(f"   Webhook status: https://{domain}/api/v1/webhooks/telegram/webhook_info")
        print("   Bot logs: Check FastAPI server logs")
        print()
        print("⚡ SCALING:")
        print("   The bot now scales with your FastAPI deployment")
        print("   No need to run separate polling processes")
        
    else:
        print()
        print("❌ SETUP FAILED!")
        print("=" * 50)
        print("Please check:")
        print("1. Domain is accessible via HTTPS")
        print("2. FastAPI server is running")
        print("3. SSL certificate is valid")
        print("4. Bot token is correct")
        print()
        print("For development mode, use:")
        print("   python app/scripts/run_telegram_bot.py")
        
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 