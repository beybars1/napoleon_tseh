from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from typing import Dict, Any

from app.core.database import get_async_session
from app.models.conversation import ConversationChannel
from app.services.message_processor import MessageProcessor
from app.services.communication_service import CommunicationService

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
        
        # Process webhook data
        comm_service = CommunicationService()
        message_data = comm_service.process_webhook_data(
            ConversationChannel.TELEGRAM,
            webhook_data
        )
        
        if message_data:
            # Process the message
            message_processor = MessageProcessor(db)
            await message_processor.process_incoming_message(
                ConversationChannel.TELEGRAM,
                message_data
            )
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


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