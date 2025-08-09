#!/usr/bin/env python3
"""
Script to check and display chat data stored in the database
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_async_session
from app.models.conversation import Conversation, ConversationChannel
from app.models.message import Message, MessageDirection
from app.models.client import Client
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
import structlog

logger = structlog.get_logger()


async def check_chat_data():
    """Check and display current chat data"""
    
    print("🔍 CHECKING CHAT DATA IN DATABASE")
    print("=" * 50)
    
    async for db in get_async_session():
        try:
            # Get total counts
            print("📊 OVERVIEW:")
            
            # Count conversations
            conv_result = await db.execute(select(func.count(Conversation.id)))
            total_conversations = conv_result.scalar()
            print(f"   Total Conversations: {total_conversations}")
            
            # Count messages
            msg_result = await db.execute(select(func.count(Message.id)))
            total_messages = msg_result.scalar()
            print(f"   Total Messages: {total_messages}")
            
            # Count clients
            client_result = await db.execute(select(func.count(Client.id)))
            total_clients = client_result.scalar()
            print(f"   Total Clients: {total_clients}")
            
            if total_messages == 0:
                print("\n❌ No messages found in database!")
                print("   This is normal if you haven't sent any messages to the bot yet.")
                print("   Try sending a message to your Telegram bot to test data storage.")
                return
            
            print(f"\n📱 BY CHANNEL:")
            
            # Get stats by channel
            channel_stats = await db.execute(
                select(
                    Conversation.channel,
                    func.count(Message.id).label('message_count'),
                    func.count(func.distinct(Conversation.client_id)).label('unique_clients')
                )
                .join(Message)
                .group_by(Conversation.channel)
            )
            
            for row in channel_stats:
                print(f"   {row.channel.value.upper()}: {row.message_count} messages, {row.unique_clients} clients")
            
            print(f"\n💬 MESSAGE BREAKDOWN:")
            
            # Get message direction stats
            direction_stats = await db.execute(
                select(
                    Message.direction,
                    func.count(Message.id).label('count')
                )
                .group_by(Message.direction)
            )
            
            for row in direction_stats:
                print(f"   {row.direction.value.title()}: {row.count} messages")
            
            print(f"\n🤖 AI PROCESSING:")
            
            # Get AI stats
            ai_stats = await db.execute(
                select(
                    func.count(Message.id).label('total'),
                    func.sum(func.cast(Message.ai_processed, "integer")).label('ai_processed'),
                    func.avg(Message.ai_confidence).label('avg_confidence')
                )
            )
            ai_result = ai_stats.first()
            
            if ai_result:
                ai_processed = ai_result.ai_processed or 0
                processing_rate = (ai_processed / ai_result.total * 100) if ai_result.total > 0 else 0
                print(f"   Processed by AI: {ai_processed}/{ai_result.total} ({processing_rate:.1f}%)")
                if ai_result.avg_confidence:
                    print(f"   Average Confidence: {ai_result.avg_confidence:.1f}%")
            
            print(f"\n🕐 RECENT ACTIVITY:")
            
            # Get recent messages
            recent_messages = await db.execute(
                select(Message)
                .options(
                    selectinload(Message.conversation).selectinload(Conversation.client)
                )
                .order_by(desc(Message.created_at))
                .limit(5)
            )
            
            messages = recent_messages.scalars().all()
            
            if messages:
                for msg in messages:
                    client_name = f"{msg.conversation.client.first_name} {msg.conversation.client.last_name}".strip()
                    direction_emoji = "📤" if msg.direction == MessageDirection.OUTGOING else "📥"
                    channel_emoji = {"telegram": "📱", "whatsapp": "💬", "sms": "📨", "email": "📧"}.get(
                        msg.conversation.channel.value, "💭"
                    )
                    
                    print(f"   {direction_emoji} {client_name} ({channel_emoji} {msg.conversation.channel.value})")
                    content_display = msg.content[:50] + ('...' if len(msg.content) > 50 else '')
                    print(f"      '{content_display}'")
                    print(f"      {msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    if msg.ai_intent:
                        print(f"      🎯 Intent: {msg.ai_intent}")
                    print()
            
            print("🎯 TELEGRAM SPECIFIC DATA:")
            
            # Get Telegram conversations
            telegram_convs = await db.execute(
                select(Conversation)
                .options(selectinload(Conversation.client))
                .where(Conversation.channel == ConversationChannel.TELEGRAM)
                .order_by(desc(Conversation.last_message_at))
                .limit(5)
            )
            
            telegram_conversations = telegram_convs.scalars().all()
            
            if telegram_conversations:
                print(f"   Recent Telegram Chats:")
                for conv in telegram_conversations:
                    client_name = f"{conv.client.first_name} {conv.client.last_name}".strip()
                    print(f"   📱 {client_name} (ID: {conv.client.telegram_id})")
                    print(f"      Messages: {conv.message_count}, Unread: {conv.unread_count}")
                    if conv.last_message_at:
                        print(f"      Last: {conv.last_message_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    print()
            else:
                print("   No Telegram conversations found")
            
            print("✅ CHAT DATA CHECK COMPLETE!")
            print("\n💡 API ENDPOINTS TO ACCESS DATA:")
            print("   📊 Overview: GET /api/v1/conversations/chat-data")
            print("   📱 Telegram Chats: GET /api/v1/conversations/telegram/chats")
            print("   💬 Chat Messages: GET /api/v1/conversations/{id}/messages")
            print("   📈 Analytics: GET /api/v1/conversations/analytics/daily")
            print("   📁 Export CSV: GET /api/v1/conversations/export/csv")
            
        except Exception as e:
            print(f"❌ Error checking chat data: {e}")
        
        break  # Exit the async generator


if __name__ == "__main__":
    asyncio.run(check_chat_data()) 