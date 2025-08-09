import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.client import Client
from app.models.conversation import Conversation, ConversationChannel, ConversationStatus
from app.models.message import Message, MessageDirection, MessageType, MessageStatus
from app.models.product import Product, ProductStatus
from app.services.ai_service import AIService
from app.services.communication_service import CommunicationService

logger = structlog.get_logger()


class MessageProcessor:
    """Service for processing incoming messages and generating AI responses"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIService()
        self.comm_service = CommunicationService()
    
    async def process_incoming_message(
        self,
        channel: ConversationChannel,
        message_data: Dict[str, Any]
    ) -> Optional[Message]:
        """
        Process an incoming message from any channel
        
        Args:
            channel: The communication channel
            message_data: Processed message data from webhook
            
        Returns:
            The created Message object or None if processing failed
        """
        try:
            # Get sender ID - handle different field names
            sender_id = message_data.get("sender_id") or message_data.get("sender", "")
            
            # Get or create client
            client = await self._get_or_create_client(
                channel=channel,
                sender_id=sender_id
            )
            
            # Get or create conversation
            conversation = await self._get_or_create_conversation(
                client=client,
                channel=channel,
                external_id=message_data.get("external_id")
            )
            
            # Create incoming message record
            incoming_message = await self._create_message(
                conversation=conversation,
                direction=MessageDirection.INCOMING,
                content=message_data.get("content") or message_data.get("message_text", ""),
                message_type=self._convert_message_type(message_data.get("message_type", "text")),
                external_id=message_data.get("external_id") or message_data.get("telegram_message_id"),
                external_data=message_data.get("raw_data") or message_data
            )
            
            # Process with AI if enabled
            if conversation.ai_enabled and incoming_message.content:
                await self._process_with_ai(conversation, incoming_message)
            
            # Update conversation statistics
            await self._update_conversation_stats(conversation)
            
            return incoming_message
            
        except Exception as e:
            logger.error(f"Error processing incoming message: {e}")
            return None
    
    async def _get_or_create_client(
        self,
        channel: ConversationChannel,
        sender_id: str
    ) -> Client:
        """Get existing client or create new one"""
        
        # Try to find existing client based on channel
        client = None
        
        if channel == ConversationChannel.WHATSAPP:
            # WhatsApp sender_id is usually a phone number
            phone = sender_id.replace("+", "").replace("-", "").replace(" ", "")
            result = await self.db.execute(
                select(Client).where(Client.phone == phone)
            )
            client = result.scalar_one_or_none()
            
            if not client:
                # Create new client
                client = Client(
                    phone=phone,
                    whatsapp_id=sender_id
                )
                
        elif channel == ConversationChannel.TELEGRAM:
            # Telegram sender_id is chat_id
            result = await self.db.execute(
                select(Client).where(Client.telegram_id == sender_id)
            )
            client = result.scalar_one_or_none()
            
            if not client:
                # Create new client with placeholder phone
                client = Client(
                    phone=f"telegram_{sender_id}",
                    telegram_id=sender_id
                )
                
        elif channel == ConversationChannel.SMS:
            # SMS sender_id is phone number
            phone = sender_id.replace("+", "").replace("-", "").replace(" ", "")
            result = await self.db.execute(
                select(Client).where(Client.phone == phone)
            )
            client = result.scalar_one_or_none()
            
            if not client:
                # Create new client
                client = Client(phone=phone)
        
        if not client:
            # Fallback: create client with sender_id as phone
            client = Client(phone=sender_id)
        
        if client.id is None:  # New client
            self.db.add(client)
            await self.db.commit()
            await self.db.refresh(client)
        
        return client
    
    async def _get_or_create_conversation(
        self,
        client: Client,
        channel: ConversationChannel,
        external_id: Optional[str] = None
    ) -> Conversation:
        """Get existing conversation or create new one"""
        
        # Try to find existing active conversation
        result = await self.db.execute(
            select(Conversation).where(
                and_(
                    Conversation.client_id == client.id,
                    Conversation.channel == channel,
                    Conversation.status == ConversationStatus.ACTIVE
                )
            )
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            # Create new conversation
            conversation = Conversation(
                client_id=client.id,
                channel=channel,
                external_id=external_id,
                status=ConversationStatus.ACTIVE
            )
            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)
        
        return conversation
    
    async def _create_message(
        self,
        conversation: Conversation,
        direction: MessageDirection,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        external_id: Optional[str] = None,
        external_data: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Create a new message record"""
        
        message = Message(
            conversation_id=conversation.id,
            direction=direction,
            message_type=message_type,
            content=content,
            external_id=external_id,
            external_data=external_data,
            status=MessageStatus.SENT if direction == MessageDirection.OUTGOING else MessageStatus.DELIVERED
        )
        
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        
        return message
    
    async def _process_with_ai(
        self,
        conversation: Conversation,
        incoming_message: Message
    ) -> Optional[Message]:
        """Process message with AI and send response"""
        
        try:
            # Get client
            result = await self.db.execute(
                select(Client).where(Client.id == conversation.client_id)
            )
            client = result.scalar_one()
            
            # Get recent message history
            result = await self.db.execute(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.created_at.desc())
                .limit(20)
            )
            message_history = list(reversed(result.scalars().all()))
            
            # Get available products
            result = await self.db.execute(
                select(Product).where(Product.status == ProductStatus.ACTIVE)
            )
            products = result.scalars().all()
            
            # Process with AI
            ai_response = await self.ai_service.process_message(
                message=incoming_message.content,
                client=client,
                conversation=conversation,
                message_history=message_history,
                products=list(products)
            )
            
            # Update incoming message with AI analysis
            incoming_message.ai_processed = True
            incoming_message.ai_intent = ai_response.get("intent")
            incoming_message.ai_entities = ai_response.get("entities")
            incoming_message.ai_confidence = ai_response.get("confidence")
            
            # Send AI response if available and auto-response is enabled
            if (ai_response.get("response") and 
                conversation.auto_response_enabled and 
                not ai_response.get("should_escalate")):
                
                # Send response through communication service
                send_result = await self.comm_service.send_message(
                    channel=conversation.channel,
                    recipient=self._get_recipient_id(client, conversation.channel),
                    message=ai_response["response"]
                )
                
                if send_result.get("success"):
                    # Create outgoing message record
                    outgoing_message = await self._create_message(
                        conversation=conversation,
                        direction=MessageDirection.OUTGOING,
                        content=ai_response["response"],
                        external_id=send_result.get("external_id")
                    )
                    
                    outgoing_message.ai_response = ai_response["response"]
                    outgoing_message.ai_confidence = ai_response.get("confidence")
                    
                    await self.db.commit()
                    return outgoing_message
            
            await self.db.commit()
            return None
            
        except Exception as e:
            logger.error(f"Error processing message with AI: {e}")
            await self.db.rollback()
            return None
    
    async def _store_message_only(
        self,
        channel: ConversationChannel,
        message_data: Dict[str, Any]
    ) -> Optional[Message]:
        """
        Store an incoming message without AI processing (for logging only)
        Used to avoid duplicate responses when telegram bot service already handled AI
        """
        try:
            # Get sender ID - handle different field names
            sender_id = message_data.get("sender_id") or message_data.get("sender", "")
            
            # Get or create client
            client = await self._get_or_create_client(
                channel=channel,
                sender_id=sender_id
            )
            
            # Get or create conversation
            conversation = await self._get_or_create_conversation(
                client=client,
                channel=channel,
                external_id=message_data.get("external_id")
            )
            
            # Create incoming message record (NO AI PROCESSING)
            incoming_message = await self._create_message(
                conversation=conversation,
                direction=MessageDirection.INCOMING,
                content=message_data.get("content") or message_data.get("message_text", ""),
                message_type=self._convert_message_type(message_data.get("message_type", "text")),
                external_id=message_data.get("external_id") or message_data.get("telegram_message_id"),
                external_data=message_data.get("raw_data") or message_data
            )
            
            # Update conversation statistics only
            await self._update_conversation_stats(conversation)
            
            return incoming_message
            
        except Exception as e:
            logger.error(f"Error storing message: {e}")
            return None
    
    def _convert_message_type(self, message_type_str: str) -> MessageType:
        """Convert string message type to MessageType enum"""
        try:
            # Handle common string formats
            type_mapping = {
                "text": MessageType.TEXT,
                "image": MessageType.IMAGE,
                "photo": MessageType.IMAGE,  # Telegram uses "photo"
                "video": MessageType.VIDEO,
                "audio": MessageType.AUDIO,
                "voice": MessageType.VOICE,
                "document": MessageType.DOCUMENT,
                "location": MessageType.LOCATION,
                "contact": MessageType.CONTACT,
                "sticker": MessageType.STICKER,
                "system": MessageType.SYSTEM,
                "callback": MessageType.TEXT,  # Treat callback queries as text
            }
            
            return type_mapping.get(message_type_str.lower(), MessageType.TEXT)
        except (AttributeError, KeyError):
            return MessageType.TEXT
    
    def _get_recipient_id(self, client: Client, channel: ConversationChannel) -> str:
        """Get recipient ID for sending messages"""
        
        if channel == ConversationChannel.WHATSAPP:
            return client.whatsapp_id or client.phone
        elif channel == ConversationChannel.TELEGRAM:
            return client.telegram_id
        elif channel == ConversationChannel.SMS:
            return client.phone
        elif channel == ConversationChannel.EMAIL:
            return client.email
        else:
            return client.phone
    
    async def _update_conversation_stats(self, conversation: Conversation):
        """Update conversation statistics"""
        
        try:
            # Count total messages
            result = await self.db.execute(
                select(Message).where(Message.conversation_id == conversation.id)
            )
            messages = result.scalars().all()
            
            conversation.message_count = len(messages)
            conversation.last_message_at = datetime.now()
            
            # Count unread messages (incoming messages that haven't been read)
            unread_count = sum(
                1 for msg in messages 
                if msg.direction == MessageDirection.INCOMING and msg.read_at is None
            )
            conversation.unread_count = unread_count
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating conversation stats: {e}")
            await self.db.rollback()
    
    async def send_message(
        self,
        conversation_id: int,
        message: str,
        message_type: MessageType = MessageType.TEXT,
        media_url: Optional[str] = None
    ) -> Optional[Message]:
        """Send a message manually (from staff/admin)"""
        
        try:
            # Get conversation and client
            result = await self.db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                return None
            
            result = await self.db.execute(
                select(Client).where(Client.id == conversation.client_id)
            )
            client = result.scalar_one()
            
            # Send message through communication service
            send_result = await self.comm_service.send_message(
                channel=conversation.channel,
                recipient=self._get_recipient_id(client, conversation.channel),
                message=message,
                message_type=message_type,
                media_url=media_url
            )
            
            if send_result.get("success"):
                # Create outgoing message record
                outgoing_message = await self._create_message(
                    conversation=conversation,
                    direction=MessageDirection.OUTGOING,
                    content=message,
                    message_type=message_type,
                    external_id=send_result.get("external_id")
                )
                
                # Update conversation stats
                await self._update_conversation_stats(conversation)
                
                return outgoing_message
            
            return None
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None 