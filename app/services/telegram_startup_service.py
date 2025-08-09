"""
Intelligent Telegram Bot Startup Service
Automatically detects and configures production vs development mode
"""

import asyncio
import structlog
import httpx
from typing import Optional, Dict, Any
from pathlib import Path

from app.core.config import settings
from app.services.telegram_bot_service import telegram_bot_service

logger = structlog.get_logger()


class TelegramStartupService:
    """Service to handle intelligent startup and mode detection"""
    
    def __init__(self):
        self.bot_service = telegram_bot_service
        
    async def start_bot(self, force_mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Intelligently start the bot in the appropriate mode
        
        Args:
            force_mode: "polling", "webhook", or None for auto-detection
            
        Returns:
            Dict with startup information
        """
        try:
            logger.info("🤖 Starting Telegram Bot...")
            
            # Determine the appropriate mode
            mode = await self._determine_mode(force_mode)
            
            if mode == "webhook":
                return await self._start_webhook_mode()
            else:
                return await self._start_polling_mode()
                
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            return {
                "success": False,
                "mode": "error",
                "error": str(e)
            }
    
    async def _determine_mode(self, force_mode: Optional[str] = None) -> str:
        """Determine the appropriate startup mode"""
        
        if force_mode:
            logger.info(f"🔧 Forced mode: {force_mode}")
            return force_mode
        
        # Check environment variables
        if settings.TELEGRAM_PRODUCTION_MODE:
            logger.info("🏭 Production mode enabled via environment")
            return "webhook"
        
        if settings.TELEGRAM_WEBHOOK_DOMAIN:
            logger.info("🌐 Webhook domain configured, attempting webhook mode")
            return "webhook"
        
        # Check if we're in a production-like environment
        if await self._detect_production_environment():
            logger.info("🔍 Production environment detected")
            return "webhook"
        
        # Default to polling for development
        logger.info("🛠️ Development environment, using polling mode")
        return "polling"
    
    async def _detect_production_environment(self) -> bool:
        """Detect if we're running in a production environment"""
        try:
            # Check for common production indicators
            production_indicators = [
                # Environment variables
                bool(settings.TELEGRAM_WEBHOOK_URL),
                bool(settings.TELEGRAM_WEBHOOK_DOMAIN),
                
                # Check if FastAPI is running on a public port
                await self._check_fastapi_accessible(),
                
                # Check for SSL/HTTPS availability
                await self._check_ssl_available(),
            ]
            
            # If any strong indicator is present, assume production
            return any(production_indicators)
            
        except Exception as e:
            logger.error(f"Error detecting environment: {e}")
            return False
    
    async def _check_fastapi_accessible(self) -> bool:
        """Check if FastAPI is accessible from external sources"""
        try:
            # Try to access the webhook info endpoint
            if settings.TELEGRAM_WEBHOOK_DOMAIN:
                test_url = f"https://{settings.TELEGRAM_WEBHOOK_DOMAIN}/api/v1/webhooks/telegram/webhook_info"
            elif settings.TELEGRAM_WEBHOOK_URL:
                # Extract domain from webhook URL
                domain = settings.TELEGRAM_WEBHOOK_URL.replace("https://", "").split("/")[0]
                test_url = f"https://{domain}/api/v1/webhooks/telegram/webhook_info"
            else:
                return False
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(test_url)
                return response.status_code == 200
                
        except Exception:
            return False
    
    async def _check_ssl_available(self) -> bool:
        """Check if SSL/HTTPS is available"""
        try:
            if settings.TELEGRAM_WEBHOOK_DOMAIN:
                test_url = f"https://{settings.TELEGRAM_WEBHOOK_DOMAIN}"
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(test_url)
                    return True  # If we can make HTTPS request, SSL is available
            return False
        except Exception:
            return False
    
    async def _start_webhook_mode(self) -> Dict[str, Any]:
        """Start bot in webhook mode"""
        try:
            logger.info("🚀 Starting in WEBHOOK mode (Production)")
            
            # Determine webhook URL
            webhook_url = await self._get_webhook_url()
            
            if not webhook_url:
                raise Exception("No webhook URL available for webhook mode")
            
            # Clear any existing webhook
            await self.bot_service.bot.delete_webhook()
            logger.info("✅ Cleared existing webhook")
            
            # Set new webhook
            await self.bot_service.set_webhook(webhook_url)
            logger.info(f"✅ Webhook set to: {webhook_url}")
            
            # Verify webhook
            webhook_info = await self.bot_service.bot.get_webhook_info()
            
            result = {
                "success": True,
                "mode": "webhook",
                "webhook_url": webhook_url,
                "webhook_active": bool(webhook_info.url),
                "pending_updates": webhook_info.pending_update_count,
                "last_error": webhook_info.last_error_message,
                "message": "Bot running in production webhook mode"
            }
            
            logger.info("🎉 Webhook mode started successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to start webhook mode: {e}")
            # Fallback to polling
            logger.info("🔄 Falling back to polling mode")
            return await self._start_polling_mode()
    
    async def _start_polling_mode(self) -> Dict[str, Any]:
        """Start bot in polling mode"""
        try:
            logger.info("🔄 Starting in POLLING mode (Development)")
            
            # Clear any existing webhook to ensure polling works
            await self.bot_service.bot.delete_webhook()
            logger.info("✅ Cleared webhook for polling mode")
            
            # Start polling in background and store the task
            polling_task = asyncio.create_task(self.bot_service.run_polling())
            self.polling_task = polling_task  # Store reference to manage later
            
            result = {
                "success": True,
                "mode": "polling",
                "message": "Bot running in development polling mode",
                "note": "This mode is suitable for development only"
            }
            
            logger.info("🎉 Polling mode started successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to start polling mode: {e}")
            raise
    
    async def stop_bot(self) -> Dict[str, Any]:
        """Stop the bot gracefully"""
        try:
            logger.info("🛑 Stopping Telegram bot...")
            
            # Cancel polling task if it exists
            if hasattr(self, 'polling_task') and not self.polling_task.done():
                self.polling_task.cancel()
                try:
                    await self.polling_task
                except asyncio.CancelledError:
                    logger.info("✅ Polling task cancelled successfully")
            
            # Stop the bot application
            if hasattr(self.bot_service, 'application'):
                await self.bot_service.application.stop()
                logger.info("✅ Bot application stopped")
            
            return {"success": True, "message": "Bot stopped successfully"}
            
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_webhook_url(self) -> Optional[str]:
        """Get the appropriate webhook URL"""
        
        # Priority order for webhook URL
        if settings.TELEGRAM_WEBHOOK_URL:
            return settings.TELEGRAM_WEBHOOK_URL
        
        if settings.TELEGRAM_WEBHOOK_DOMAIN:
            return f"https://{settings.TELEGRAM_WEBHOOK_DOMAIN}/api/v1/webhooks/telegram"
        
        return None
    
    async def get_bot_status(self) -> Dict[str, Any]:
        """Get current bot status and configuration"""
        try:
            webhook_info = await self.bot_service.bot.get_webhook_info()
            
            status = {
                "bot_token_configured": bool(settings.TELEGRAM_BOT_TOKEN),
                "webhook_url": webhook_info.url or None,
                "webhook_active": bool(webhook_info.url),
                "pending_updates": webhook_info.pending_update_count,
                "last_error": webhook_info.last_error_message,
                "last_error_date": webhook_info.last_error_date,
                "max_connections": webhook_info.max_connections,
                "production_mode": bool(webhook_info.url),
                "environment": {
                    "production_mode_env": settings.TELEGRAM_PRODUCTION_MODE,
                    "webhook_domain_env": settings.TELEGRAM_WEBHOOK_DOMAIN,
                    "webhook_url_env": bool(settings.TELEGRAM_WEBHOOK_URL)
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
            return {"error": str(e)}
    
    async def switch_mode(self, target_mode: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """Switch between polling and webhook modes"""
        try:
            logger.info(f"🔄 Switching to {target_mode} mode")
            
            if target_mode == "webhook":
                if domain:
                    # Temporarily set domain for this operation
                    original_domain = settings.TELEGRAM_WEBHOOK_DOMAIN
                    settings.TELEGRAM_WEBHOOK_DOMAIN = domain
                    
                result = await self._start_webhook_mode()
                
                if domain and 'original_domain' in locals():
                    settings.TELEGRAM_WEBHOOK_DOMAIN = original_domain
                    
                return result
            
            elif target_mode == "polling":
                return await self._start_polling_mode()
            
            else:
                raise ValueError(f"Invalid mode: {target_mode}")
                
        except Exception as e:
            logger.error(f"Error switching mode: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
telegram_startup_service = TelegramStartupService() 