from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func, text
from sqlalchemy.orm import selectinload
import structlog

from app.core.database import get_async_session
from app.models.conversation import Conversation, ConversationChannel, ConversationStatus
from app.models.message import Message, MessageDirection, MessageType
from app.models.client import Client
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()
logger = structlog.get_logger()


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


@router.get("/conversations/chat-data")
async def get_chat_data_overview(
    channel: Optional[ConversationChannel] = None,
    days: int = Query(default=7, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_async_session)
):
    """Get overview of chat data and statistics"""
    try:
        # Base query for date filtering
        date_filter = datetime.now() - timedelta(days=days)
        
        # Get total conversations
        conv_query = select(func.count(Conversation.id))
        if channel:
            conv_query = conv_query.where(Conversation.channel == channel)
        conv_query = conv_query.where(Conversation.created_at >= date_filter)
        
        total_conversations = await db.execute(conv_query)
        total_conversations = total_conversations.scalar()
        
        # Get total messages
        msg_query = select(func.count(Message.id)).join(Conversation)
        if channel:
            msg_query = msg_query.where(Conversation.channel == channel)
        msg_query = msg_query.where(Message.created_at >= date_filter)
        
        total_messages = await db.execute(msg_query)
        total_messages = total_messages.scalar()
        
        # Get messages by direction
        incoming_query = msg_query.where(Message.direction == MessageDirection.INCOMING)
        outgoing_query = msg_query.where(Message.direction == MessageDirection.OUTGOING)
        
        incoming_count = await db.execute(incoming_query)
        incoming_count = incoming_count.scalar()
        
        outgoing_count = await db.execute(outgoing_query)
        outgoing_count = outgoing_count.scalar()
        
        # Get messages by channel
        channel_stats = await db.execute(
            select(
                Conversation.channel,
                func.count(Message.id).label('message_count'),
                func.count(func.distinct(Conversation.client_id)).label('unique_clients')
            )
            .join(Conversation)
            .where(Message.created_at >= date_filter)
            .group_by(Conversation.channel)
        )
        
        # Get AI processing stats
        ai_stats = await db.execute(
            select(
                func.count(Message.id).label('total'),
                func.sum(func.cast(Message.ai_processed, "integer")).label('ai_processed'),
                func.avg(Message.ai_confidence).label('avg_confidence')
            )
            .join(Conversation)
            .where(Message.created_at >= date_filter)
        )
        ai_result = ai_stats.first()
        
        return {
            "period": f"Last {days} days",
            "overview": {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "incoming_messages": incoming_count,
                "outgoing_messages": outgoing_count,
                "response_rate": f"{(outgoing_count/incoming_count*100) if incoming_count > 0 else 0:.1f}%"
            },
            "by_channel": [
                {
                    "channel": row.channel.value,
                    "messages": row.message_count,
                    "unique_clients": row.unique_clients
                }
                for row in channel_stats
            ],
            "ai_stats": {
                "total_messages": ai_result.total if ai_result else 0,
                "ai_processed": ai_result.ai_processed if ai_result else 0,
                "processing_rate": f"{(ai_result.ai_processed/ai_result.total*100) if ai_result and ai_result.total > 0 else 0:.1f}%",
                "avg_confidence": f"{ai_result.avg_confidence:.1f}%" if ai_result and ai_result.avg_confidence else "N/A"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting chat data overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/telegram/chats")
async def get_telegram_chats(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_async_session)
):
    """Get all Telegram chat conversations with recent message info"""
    try:
        # Get conversations with related data
        query = (
            select(Conversation)
            .options(
                selectinload(Conversation.client),
                selectinload(Conversation.messages).selectinload(Message.conversation)
            )
            .where(Conversation.channel == ConversationChannel.TELEGRAM)
            .order_by(desc(Conversation.last_message_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(query)
        conversations = result.scalars().all()
        
        # Format the response
        chats = []
        for conv in conversations:
            # Get last message
            last_message = None
            if conv.messages:
                last_msg = max(conv.messages, key=lambda m: m.created_at)
                last_message = {
                    "content": last_msg.content,
                    "direction": last_msg.direction.value,
                    "message_type": last_msg.message_type.value,
                    "created_at": last_msg.created_at.isoformat(),
                    "ai_intent": last_msg.ai_intent
                }
            
            chats.append({
                "conversation_id": conv.id,
                "client": {
                    "id": conv.client.id,
                    "name": f"{conv.client.first_name} {conv.client.last_name}".strip(),
                    "telegram_id": conv.client.telegram_id,
                    "phone": conv.client.phone
                },
                "stats": {
                    "message_count": conv.message_count,
                    "unread_count": conv.unread_count,
                    "ai_enabled": conv.ai_enabled
                },
                "last_message": last_message,
                "created_at": conv.created_at.isoformat(),
                "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None
            })
        
        return {
            "chats": chats,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(chats)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting Telegram chats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_async_session)
):
    """Get all messages in a conversation (full chat history)"""
    try:
        # Get conversation with client info
        conv_query = (
            select(Conversation)
            .options(selectinload(Conversation.client))
            .where(Conversation.id == conversation_id)
        )
        conv_result = await db.execute(conv_query)
        conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get messages
        messages_query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(messages_query)
        messages = result.scalars().all()
        
        # Format messages
        formatted_messages = []
        for msg in reversed(messages):  # Reverse to show chronological order
            formatted_messages.append({
                "id": msg.id,
                "direction": msg.direction.value,
                "content": msg.content,
                "message_type": msg.message_type.value,
                "created_at": msg.created_at.isoformat(),
                "external_id": msg.external_id,
                "ai_data": {
                    "processed": msg.ai_processed,
                    "intent": msg.ai_intent,
                    "entities": msg.ai_entities,
                    "confidence": msg.ai_confidence,
                    "response": msg.ai_response
                } if msg.ai_processed else None,
                "raw_data": msg.external_data
            })
        
        return {
            "conversation": {
                "id": conversation.id,
                "channel": conversation.channel.value,
                "client": {
                    "name": f"{conversation.client.first_name} {conversation.client.last_name}".strip(),
                    "telegram_id": conversation.client.telegram_id,
                    "phone": conversation.client.phone
                },
                "stats": {
                    "total_messages": conversation.message_count,
                    "unread_count": conversation.unread_count
                }
            },
            "messages": formatted_messages,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "showing": len(formatted_messages)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/export/csv")
async def export_chat_data_csv(
    channel: Optional[ConversationChannel] = None,
    days: int = Query(default=30, description="Number of days to export"),
    db: AsyncSession = Depends(get_async_session)
):
    """Export chat data to CSV format"""
    try:
        from io import StringIO
        import csv
        from fastapi.responses import StreamingResponse
        
        # Date filter
        date_filter = datetime.now() - timedelta(days=days)
        
        # Query messages with conversation and client data
        query = (
            select(
                Message.id,
                Message.content,
                Message.direction,
                Message.message_type,
                Message.created_at,
                Message.ai_intent,
                Message.ai_confidence,
                Conversation.channel,
                Client.first_name,
                Client.last_name,
                Client.telegram_id,
                Client.phone
            )
            .join(Conversation)
            .join(Client)
            .where(Message.created_at >= date_filter)
        )
        
        if channel:
            query = query.where(Conversation.channel == channel)
        
        query = query.order_by(desc(Message.created_at))
        
        result = await db.execute(query)
        rows = result.all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Message ID", "Content", "Direction", "Type", "Created At",
            "AI Intent", "AI Confidence", "Channel", "Client Name",
            "Telegram ID", "Phone"
        ])
        
        # Data rows
        for row in rows:
            writer.writerow([
                row.id,
                row.content,
                row.direction.value,
                row.message_type.value,
                row.created_at.isoformat(),
                row.ai_intent or "",
                row.ai_confidence or "",
                row.channel.value,
                f"{row.first_name} {row.last_name}".strip(),
                row.telegram_id or "",
                row.phone or ""
            ])
        
        output.seek(0)
        
        def generate():
            yield output.getvalue()
        
        return StreamingResponse(
            generate(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=chat_data_{days}days.csv"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting chat data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/analytics/daily")
async def get_daily_chat_analytics(
    days: int = Query(default=30, le=365),
    channel: Optional[ConversationChannel] = None,
    db: AsyncSession = Depends(get_async_session)
):
    """Get daily chat analytics (messages per day, response times, etc.)"""
    try:
        # Date filter
        date_filter = datetime.now() - timedelta(days=days)
        
        # Daily message counts
        daily_query = text("""
            SELECT 
                DATE(m.created_at) as date,
                COUNT(*) as total_messages,
                COUNT(CASE WHEN m.direction = 'incoming' THEN 1 END) as incoming,
                COUNT(CASE WHEN m.direction = 'outgoing' THEN 1 END) as outgoing,
                COUNT(CASE WHEN m.ai_processed = true THEN 1 END) as ai_processed,
                AVG(m.ai_confidence) as avg_confidence
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE m.created_at >= :date_filter
            """ + (f" AND c.channel = '{channel.value}'" if channel else "") + """
            GROUP BY DATE(m.created_at)
            ORDER BY date DESC
        """)
        
        result = await db.execute(daily_query, {"date_filter": date_filter})
        daily_stats = result.all()
        
        return {
            "period": f"Last {days} days",
            "daily_analytics": [
                {
                    "date": row.date.isoformat(),
                    "total_messages": row.total_messages,
                    "incoming": row.incoming,
                    "outgoing": row.outgoing,
                    "response_rate": f"{(row.outgoing/row.incoming*100) if row.incoming > 0 else 0:.1f}%",
                    "ai_processed": row.ai_processed,
                    "avg_confidence": f"{row.avg_confidence:.1f}%" if row.avg_confidence else "N/A"
                }
                for row in daily_stats
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting daily analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 