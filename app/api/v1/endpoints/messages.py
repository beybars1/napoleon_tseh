from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_session
from app.models.message import Message, MessageType
from app.services.message_processor import MessageProcessor
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/send")
async def send_message(
    conversation_id: int,
    content: str,
    message_type: MessageType = MessageType.TEXT,
    media_url: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Send a message to a conversation"""
    
    message_processor = MessageProcessor(db)
    
    message = await message_processor.send_message(
        conversation_id=conversation_id,
        message=content,
        message_type=message_type,
        media_url=media_url
    )
    
    if not message:
        raise HTTPException(status_code=400, detail="Failed to send message")
    
    return {
        "message": "Message sent successfully",
        "message_id": message.id,
        "external_id": message.external_id
    }


@router.get("/{message_id}")
async def get_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get specific message details"""
    
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "direction": message.direction.value,
        "message_type": message.message_type.value,
        "content": message.content,
        "media_url": message.media_url,
        "media_type": message.media_type,
        "media_size": message.media_size,
        "external_id": message.external_id,
        "ai_processed": message.ai_processed,
        "ai_response": message.ai_response,
        "ai_confidence": message.ai_confidence,
        "ai_intent": message.ai_intent,
        "ai_entities": message.ai_entities,
        "status": message.status.value,
        "created_at": message.created_at.isoformat(),
        "sent_at": message.sent_at.isoformat() if message.sent_at else None,
        "delivered_at": message.delivered_at.isoformat() if message.delivered_at else None,
        "read_at": message.read_at.isoformat() if message.read_at else None
    } 