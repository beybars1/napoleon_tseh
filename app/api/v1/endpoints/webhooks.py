from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from typing import Dict, Any
from datetime import datetime

from app.core.database import get_async_session
from app.models.conversation import ConversationChannel
from app.services.message_processor import MessageProcessor
from app.services.communication_service import CommunicationService
from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger()


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
):
    """Handle WhatsApp webhook from Twilio"""
    try:
        # Get form data from Twilio
        form_data = await request.form()
        webhook_data = dict(form_data)
        
        logger.info(f"WhatsApp webhook received: {webhook_data}")
        
        # Process webhook data
        comm_service = CommunicationService()
        message_data = comm_service.process_webhook_data(
            ConversationChannel.WHATSAPP,
            webhook_data
        )
        
        if message_data:
            # Process the message
            message_processor = MessageProcessor(db)
            await message_processor.process_incoming_message(
                ConversationChannel.WHATSAPP,
                message_data
            )
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/whatsapp")
async def whatsapp_webhook_verify(
    request: Request
):
    """Verify WhatsApp webhook (for Twilio setup)"""
    try:
        # This is for webhook verification during setup
        return {"status": "verified"}
        
    except Exception as e:
        logger.error(f"Error verifying WhatsApp webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/telegram")
async def telegram_webhook(
    webhook_data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_session)
):
    """Handle Telegram webhook"""
    try:
        logger.info(f"Telegram webhook received: {webhook_data}")
        
        # Process webhook through our Telegram bot service
        from app.services.telegram_bot_service import telegram_bot_service
        
        # Handle the update through the bot service (this includes AI response)
        await telegram_bot_service.handle_webhook_update(webhook_data)
        
        # Log the conversation for tracking purposes only (no AI response)
        comm_service = CommunicationService()
        message_data = comm_service.process_webhook_data(
            ConversationChannel.TELEGRAM,
            webhook_data
        )
        
        if message_data:
            # Only log the message, don't process with AI (to avoid duplicates)
            message_processor = MessageProcessor(db)
            # Store message without AI processing
            await message_processor._store_message_only(
                ConversationChannel.TELEGRAM,
                message_data
            )
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {e}")
        # Don't return 500 error to Telegram as it might retry indefinitely
        return {"status": "error", "message": str(e)}


@router.post("/telegram/set_webhook")
async def set_telegram_webhook(
    request: Dict[str, str],
    db: AsyncSession = Depends(get_async_session)
):
    """Set Telegram webhook URL (for production deployment)"""
    try:
        webhook_url = request.get("webhook_url")
        if not webhook_url:
            raise HTTPException(status_code=400, detail="webhook_url is required")
        
        from app.services.telegram_bot_service import telegram_bot_service
        
        # Validate URL format
        if not webhook_url.startswith("https://"):
            raise HTTPException(status_code=400, detail="Webhook URL must use HTTPS")
        
        # Set the webhook
        await telegram_bot_service.set_webhook(webhook_url)
        
        logger.info(f"Telegram webhook set to: {webhook_url}")
        return {
            "status": "success", 
            "webhook_url": webhook_url,
            "message": "Webhook successfully configured for production"
        }
        
    except Exception as e:
        logger.error(f"Error setting Telegram webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set webhook: {str(e)}")


@router.post("/telegram/setup_production")
async def setup_telegram_production(
    request: Dict[str, str],
    db: AsyncSession = Depends(get_async_session)
):
    """Complete production setup for Telegram bot with domain"""
    try:
        domain = request.get("domain")
        if not domain:
            raise HTTPException(status_code=400, detail="domain is required")
        
        # Construct webhook URL
        webhook_url = f"https://{domain}/api/v1/webhooks/telegram"
        
        from app.services.telegram_bot_service import telegram_bot_service
        
        # Delete any existing webhook first
        await telegram_bot_service.bot.delete_webhook()
        logger.info("Deleted existing webhook")
        
        # Set new webhook
        await telegram_bot_service.set_webhook(webhook_url)
        
        # Get webhook info to verify
        webhook_info = await telegram_bot_service.bot.get_webhook_info()
        
        logger.info(f"Production setup complete for domain: {domain}")
        
        return {
            "status": "success",
            "domain": domain,
            "webhook_url": webhook_url,
            "webhook_active": bool(webhook_info.url),
            "pending_updates": webhook_info.pending_update_count,
            "message": "Telegram bot successfully configured for production",
            "next_steps": [
                "Bot is now ready for production use",
                "Webhook will receive all incoming messages",
                "Polling mode is automatically disabled",
                "Monitor webhook status via /api/v1/webhooks/telegram/webhook_info"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error setting up production: {e}")
        raise HTTPException(status_code=500, detail=f"Production setup failed: {str(e)}")


@router.delete("/telegram/webhook")
async def delete_telegram_webhook():
    """Delete Telegram webhook (for admin use)"""
    try:
        from app.services.telegram_bot_service import telegram_bot_service
        
        # Delete the webhook by setting it to empty
        await telegram_bot_service.bot.delete_webhook()
        
        logger.info("Telegram webhook deleted")
        return {"status": "success", "message": "Webhook deleted"}
        
    except Exception as e:
        logger.error(f"Error deleting Telegram webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete webhook: {str(e)}")


@router.get("/telegram/webhook_info")
async def get_telegram_webhook_info():
    """Get Telegram webhook information (for admin use)"""
    try:
        from app.services.telegram_bot_service import telegram_bot_service
        
        # Get webhook info
        webhook_info = await telegram_bot_service.bot.get_webhook_info()
        
        return {
            "url": webhook_info.url,
            "has_custom_certificate": webhook_info.has_custom_certificate,
            "pending_update_count": webhook_info.pending_update_count,
            "last_error_date": webhook_info.last_error_date,
            "last_error_message": webhook_info.last_error_message,
            "max_connections": webhook_info.max_connections,
            "allowed_updates": webhook_info.allowed_updates
        }
        
    except Exception as e:
        logger.error(f"Error getting Telegram webhook info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get webhook info: {str(e)}")


@router.post("/telegram/start_bot")
async def start_telegram_bot(
    request: Dict[str, Any] = None,
    db: AsyncSession = Depends(get_async_session)
):
    """Start Telegram bot with intelligent mode detection"""
    try:
        from app.services.telegram_startup_service import telegram_startup_service
        
        force_mode = None
        if request:
            force_mode = request.get("mode")  # "polling", "webhook", or None
        
        result = await telegram_startup_service.start_bot(force_mode)
        
        logger.info(f"Bot startup completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error starting Telegram bot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start bot: {str(e)}")


@router.post("/telegram/switch_mode")
async def switch_telegram_mode(
    request: Dict[str, str],
    db: AsyncSession = Depends(get_async_session)
):
    """Switch Telegram bot between polling and webhook modes"""
    try:
        from app.services.telegram_startup_service import telegram_startup_service
        
        target_mode = request.get("mode")
        domain = request.get("domain")
        
        if not target_mode or target_mode not in ["polling", "webhook"]:
            raise HTTPException(status_code=400, detail="mode must be 'polling' or 'webhook'")
        
        if target_mode == "webhook" and not domain:
            raise HTTPException(status_code=400, detail="domain is required for webhook mode")
        
        result = await telegram_startup_service.switch_mode(target_mode, domain)
        
        logger.info(f"Mode switch completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error switching bot mode: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to switch mode: {str(e)}")


@router.get("/telegram/status")
async def get_telegram_bot_status():
    """Get comprehensive Telegram bot status"""
    try:
        from app.services.telegram_startup_service import telegram_startup_service
        
        status = await telegram_startup_service.get_bot_status()
        
        return {
            "bot_status": status,
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "production_mode": settings.TELEGRAM_PRODUCTION_MODE,
                "webhook_domain": settings.TELEGRAM_WEBHOOK_DOMAIN,
                "webhook_url_configured": bool(settings.TELEGRAM_WEBHOOK_URL)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/sms")
async def sms_webhook(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
):
    """Handle SMS webhook from Twilio"""
    try:
        # Get form data from Twilio
        form_data = await request.form()
        webhook_data = dict(form_data)
        
        logger.info(f"SMS webhook received: {webhook_data}")
        
        # Process webhook data
        comm_service = CommunicationService()
        message_data = comm_service.process_webhook_data(
            ConversationChannel.SMS,
            webhook_data
        )
        
        if message_data:
            # Process the message
            message_processor = MessageProcessor(db)
            await message_processor.process_incoming_message(
                ConversationChannel.SMS,
                message_data
            )
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing SMS webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/instagram")
async def instagram_webhook(
    webhook_data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_session)
):
    """Handle Instagram webhook"""
    try:
        logger.info(f"Instagram webhook received: {webhook_data}")
        
        # Process webhook data
        comm_service = CommunicationService()
        message_data = comm_service.process_webhook_data(
            ConversationChannel.INSTAGRAM,
            webhook_data
        )
        
        if message_data:
            # Process the message
            message_processor = MessageProcessor(db)
            await message_processor.process_incoming_message(
                ConversationChannel.INSTAGRAM,
                message_data
            )
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing Instagram webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/instagram")
async def instagram_webhook_verify(
    request: Request
):
    """Verify Instagram webhook"""
    try:
        # Instagram webhook verification
        hub_mode = request.query_params.get("hub.mode")
        hub_verify_token = request.query_params.get("hub.verify_token")
        hub_challenge = request.query_params.get("hub.challenge")
        
        # Verify the token (you should set this in your environment)
        if hub_mode == "subscribe" and hub_verify_token == "your_verify_token":
            return int(hub_challenge)
        else:
            raise HTTPException(status_code=403, detail="Forbidden")
            
    except Exception as e:
        logger.error(f"Error verifying Instagram webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 