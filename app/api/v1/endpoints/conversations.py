from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional

from app.core.database import get_async_session
from app.models.conversation import Conversation, ConversationChannel, ConversationStatus
from app.models.client import Client
from app.models.message import Message
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/")
async def get_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    channel: Optional[ConversationChannel] = Query(None),
    status: Optional[ConversationStatus] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get all conversations with filtering"""
    
    query = select(Conversation, Client).join(Client, Conversation.client_id == Client.id)
    
    if channel:
        query = query.where(Conversation.channel == channel)
    
    if status:
        query = query.where(Conversation.status == status)
    
    query = query.order_by(desc(Conversation.last_message_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    conversations_data = result.all()
    
    formatted_conversations = []
    for conversation, client in conversations_data:
        formatted_conversations.append({
            "id": conversation.id,
            "channel": conversation.channel.value,
            "status": conversation.status.value,
            "client": {
                "id": client.id,
                "name": client.full_name,
                "phone": client.phone
            },
            "message_count": conversation.message_count,
            "unread_count": conversation.unread_count,
            "ai_enabled": conversation.ai_enabled,
            "auto_response_enabled": conversation.auto_response_enabled,
            "priority": conversation.priority,
            "created_at": conversation.created_at.isoformat(),
            "last_message_at": conversation.last_message_at.isoformat() if conversation.last_message_at else None
        })
    
    return formatted_conversations


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get specific conversation details"""
    
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get client
    client_result = await db.execute(select(Client).where(Client.id == conversation.client_id))
    client = client_result.scalar_one()
    
    # Get recent messages
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .limit(100)
    )
    messages = messages_result.scalars().all()
    
    formatted_messages = []
    for message in messages:
        formatted_messages.append({
            "id": message.id,
            "direction": message.direction.value,
            "message_type": message.message_type.value,
            "content": message.content,
            "media_url": message.media_url,
            "ai_processed": message.ai_processed,
            "ai_intent": message.ai_intent,
            "ai_confidence": message.ai_confidence,
            "status": message.status.value,
            "created_at": message.created_at.isoformat(),
            "sent_at": message.sent_at.isoformat() if message.sent_at else None,
            "delivered_at": message.delivered_at.isoformat() if message.delivered_at else None,
            "read_at": message.read_at.isoformat() if message.read_at else None
        })
    
    return {
        "id": conversation.id,
        "channel": conversation.channel.value,
        "status": conversation.status.value,
        "client": {
            "id": client.id,
            "name": client.full_name,
            "phone": client.phone,
            "email": client.email,
            "whatsapp_id": client.whatsapp_id,
            "telegram_id": client.telegram_id,
            "instagram_handle": client.instagram_handle
        },
        "message_count": conversation.message_count,
        "unread_count": conversation.unread_count,
        "ai_enabled": conversation.ai_enabled,
        "auto_response_enabled": conversation.auto_response_enabled,
        "priority": conversation.priority,
        "title": conversation.title,
        "tags": conversation.tags,
        "external_id": conversation.external_id,
        "thread_id": conversation.thread_id,
        "created_at": conversation.created_at.isoformat(),
        "last_message_at": conversation.last_message_at.isoformat() if conversation.last_message_at else None,
        "messages": formatted_messages
    }


@router.put("/{conversation_id}/settings")
async def update_conversation_settings(
    conversation_id: int,
    ai_enabled: Optional[bool] = None,
    auto_response_enabled: Optional[bool] = None,
    priority: Optional[int] = None,
    status: Optional[ConversationStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Update conversation settings"""
    
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Update settings
    if ai_enabled is not None:
        conversation.ai_enabled = ai_enabled
    if auto_response_enabled is not None:
        conversation.auto_response_enabled = auto_response_enabled
    if priority is not None:
        conversation.priority = priority
    if status is not None:
        conversation.status = status
    
    await db.commit()
    
    return {"message": "Conversation settings updated successfully"}


@router.post("/{conversation_id}/messages/read")
async def mark_messages_as_read(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Mark all messages in conversation as read"""
    
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Update unread messages
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .where(Message.read_at.is_(None))
    )
    messages = messages_result.scalars().all()
    
    for message in messages:
        message.read_at = func.now()
    
    # Reset unread count
    conversation.unread_count = 0
    
    await db.commit()
    
    return {"message": f"Marked {len(messages)} messages as read"}


@router.get("/stats/summary")
async def get_conversation_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get conversation statistics summary"""
    
    # Total conversations
    total_result = await db.execute(select(func.count(Conversation.id)))
    total_conversations = total_result.scalar()
    
    # Active conversations
    active_result = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.status == ConversationStatus.ACTIVE)
    )
    active_conversations = active_result.scalar()
    
    # Conversations by channel
    channel_result = await db.execute(
        select(Conversation.channel, func.count(Conversation.id))
        .group_by(Conversation.channel)
    )
    channel_counts = dict(channel_result.all())
    
    # Total unread messages
    unread_result = await db.execute(
        select(func.sum(Conversation.unread_count))
    )
    total_unread = unread_result.scalar() or 0
    
    return {
        "total_conversations": total_conversations,
        "active_conversations": active_conversations,
        "total_unread_messages": total_unread,
        "channel_breakdown": {
            channel.value: channel_counts.get(channel, 0)
            for channel in ConversationChannel
        }
    } 