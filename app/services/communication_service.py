import structlog
from typing import Dict, Any, Optional
from twilio.rest import Client as TwilioClient
from telegram import Bot
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
import json
import time
from datetime import datetime

from app.core.config import settings
from app.models.conversation import ConversationChannel
from app.models.message import MessageType

logger = structlog.get_logger()


class CommunicationService:
    """Service for handling multi-channel communication"""
    
    def __init__(self):
        # Initialize Twilio client
        self.twilio_client = TwilioClient(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        
        # Initialize Telegram bot
        self.telegram_bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        
        # HTTP client for API calls
        self.http_client = httpx.AsyncClient()
    
    async def send_message(
        self,
        channel: ConversationChannel,
        recipient: str,
        message: str,
        message_type: MessageType = MessageType.TEXT,
        media_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message through the specified channel
        
        Args:
            channel: The communication channel
            recipient: The recipient identifier (phone, chat_id, etc.)
            message: The message content
            message_type: Type of message (text, image, etc.)
            media_url: URL for media content
            
        Returns:
            Dict with success status and external_id
        """
        try:
            if channel == ConversationChannel.WHATSAPP:
                return await self._send_whatsapp_message(recipient, message, message_type, media_url)
            elif channel == ConversationChannel.TELEGRAM:
                return await self._send_telegram_message(recipient, message, message_type, media_url)
            elif channel == ConversationChannel.SMS:
                return await self._send_sms_message(recipient, message)
            elif channel == ConversationChannel.EMAIL:
                return await self._send_email_message(recipient, message)
            elif channel == ConversationChannel.INSTAGRAM:
                return await self._send_instagram_message(recipient, message)
            else:
                logger.error(f"Unsupported channel: {channel}")
                return {"success": False, "error": "Unsupported channel"}
                
        except Exception as e:
            logger.error(f"Error sending message via {channel}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_whatsapp_message(
        self,
        recipient: str,
        message: str,
        message_type: MessageType,
        media_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send WhatsApp message via Twilio"""
        try:
            # Format phone number for WhatsApp
            whatsapp_number = f"whatsapp:{recipient}"
            from_number = f"whatsapp:{settings.TWILIO_PHONE_NUMBER}"
            
            if message_type == MessageType.TEXT:
                # Send text message
                message_obj = self.twilio_client.messages.create(
                    body=message,
                    from_=from_number,
                    to=whatsapp_number
                )
            elif message_type == MessageType.IMAGE and media_url:
                # Send image message
                message_obj = self.twilio_client.messages.create(
                    body=message,
                    from_=from_number,
                    to=whatsapp_number,
                    media_url=[media_url]
                )
            else:
                # Fallback to text
                message_obj = self.twilio_client.messages.create(
                    body=message,
                    from_=from_number,
                    to=whatsapp_number
                )
            
            return {
                "success": True,
                "external_id": message_obj.sid,
                "status": message_obj.status
            }
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_telegram_message(
        self,
        recipient: str,
        message: str,
        message_type: MessageType,
        media_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send Telegram message"""
        try:
            chat_id = recipient
            
            if message_type == MessageType.TEXT:
                # Send text message
                sent_message = await self.telegram_bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='HTML'
                )
            elif message_type == MessageType.IMAGE and media_url:
                # Send photo
                sent_message = await self.telegram_bot.send_photo(
                    chat_id=chat_id,
                    photo=media_url,
                    caption=message
                )
            else:
                # Fallback to text
                sent_message = await self.telegram_bot.send_message(
                    chat_id=chat_id,
                    text=message
                )
            
            return {
                "success": True,
                "external_id": str(sent_message.message_id),
                "status": "sent"
            }
            
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_sms_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """Send SMS message via Twilio"""
        try:
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=recipient
            )
            
            return {
                "success": True,
                "external_id": message_obj.sid,
                "status": message_obj.status
            }
            
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_email_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """Send email message"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_USERNAME
            msg['To'] = recipient
            msg['Subject'] = f"Message from {settings.BUSINESS_NAME}"
            
            # Add body
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                start_tls=True,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD
            )
            
            return {
                "success": True,
                "external_id": f"email_{recipient}_{int(time.time())}",
                "status": "sent"
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_instagram_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """Send Instagram message (placeholder - requires Instagram Basic Display API)"""
        try:
            # This is a placeholder implementation
            # In production, you would use Instagram's messaging API
            logger.info(f"Instagram message would be sent to {recipient}: {message}")
            
            return {
                "success": True,
                "external_id": f"instagram_{recipient}_{int(time.time())}",
                "status": "sent"
            }
            
        except Exception as e:
            logger.error(f"Error sending Instagram message: {e}")
            return {"success": False, "error": str(e)}
    
    async def process_webhook_data(
        self,
        channel: ConversationChannel,
        webhook_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process incoming webhook data from different channels
        
        Args:
            channel: The communication channel
            webhook_data: Raw webhook data
            
        Returns:
            Processed message data or None if invalid
        """
        try:
            if channel == ConversationChannel.WHATSAPP:
                return self._process_whatsapp_webhook(webhook_data)
            elif channel == ConversationChannel.TELEGRAM:
                return self._process_telegram_webhook(webhook_data)
            elif channel == ConversationChannel.SMS:
                return self._process_sms_webhook(webhook_data)
            elif channel == ConversationChannel.INSTAGRAM:
                return self._process_instagram_webhook(webhook_data)
            else:
                logger.error(f"Unsupported webhook channel: {channel}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing webhook for {channel}: {e}")
            return None
    
    def _process_whatsapp_webhook(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process WhatsApp webhook data"""
        try:
            # Twilio WhatsApp webhook format
            return {
                "sender": data.get("From", "").replace("whatsapp:", ""),
                "content": data.get("Body", ""),
                "message_type": MessageType.IMAGE if data.get("MediaUrl0") else MessageType.TEXT,
                "media_url": data.get("MediaUrl0"),
                "external_id": data.get("MessageSid"),
                "raw_data": data
            }
        except Exception as e:
            logger.error(f"Error processing WhatsApp webhook: {e}")
            return None
    
    def _process_telegram_webhook(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process Telegram webhook data"""
        try:
            # Check if this is a message update
            if "message" in data:
                message = data["message"]
                
                # Extract basic message info
                sender = message.get("from", {})
                sender_id = str(sender.get("id", ""))
                sender_name = f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip()
                username = sender.get("username", "")
                
                # Extract message content
                message_text = message.get("text", "")
                message_type = "text"
                
                # Handle different message types
                if "photo" in message:
                    message_type = "photo"
                    # Get the largest photo
                    photos = message["photo"]
                    if photos:
                        largest_photo = max(photos, key=lambda x: x.get("file_size", 0))
                        message_text = message.get("caption", "") or "Photo"
                elif "document" in message:
                    message_type = "document"
                    message_text = message.get("caption", "") or "Document"
                elif "voice" in message:
                    message_type = "voice"
                    message_text = "Voice message"
                elif "location" in message:
                    message_type = "location"
                    location = message["location"]
                    message_text = f"Location: {location.get('latitude')}, {location.get('longitude')}"
                elif "contact" in message:
                    message_type = "contact"
                    contact = message["contact"]
                    message_text = f"Contact: {contact.get('first_name')} {contact.get('phone_number')}"
                
                return {
                    "sender_id": sender_id,
                    "sender_name": sender_name or f"User {sender_id}",
                    "username": username,
                    "message_text": message_text,
                    "message_type": message_type,
                    "timestamp": datetime.fromtimestamp(message.get("date", 0)).isoformat(),
                    "telegram_user_id": sender.get("id"),
                    "telegram_username": f"@{username}" if username else f"user_{sender_id}",
                    "telegram_message_id": message.get("message_id"),
                    "chat_id": message.get("chat", {}).get("id")
                }
            
            # Handle callback queries (inline keyboard button presses)
            elif "callback_query" in data:
                callback = data["callback_query"]
                sender = callback.get("from", {})
                
                return {
                    "sender_id": str(sender.get("id", "")),
                    "sender_name": f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip(),
                    "username": sender.get("username", ""),
                    "message_text": f"Button pressed: {callback.get('data', '')}",
                    "message_type": "callback",
                    "timestamp": datetime.now().isoformat(),
                    "telegram_user_id": sender.get("id"),
                    "telegram_username": f"@{sender.get('username')}" if sender.get("username") else f"user_{sender.get('id')}",
                    "callback_data": callback.get("data"),
                    "chat_id": callback.get("message", {}).get("chat", {}).get("id")
                }
            
            logger.warning(f"Unhandled Telegram webhook type: {list(data.keys())}")
            return None
            
        except Exception as e:
            logger.error(f"Error processing Telegram webhook: {e}")
            return None
    
    def _process_sms_webhook(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process SMS webhook data"""
        try:
            # Twilio SMS webhook format
            return {
                "sender": data.get("From", ""),
                "content": data.get("Body", ""),
                "message_type": MessageType.TEXT,
                "external_id": data.get("MessageSid"),
                "raw_data": data
            }
        except Exception as e:
            logger.error(f"Error processing SMS webhook: {e}")
            return None
    
    def _process_instagram_webhook(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process Instagram webhook data"""
        try:
            # Instagram webhook format (placeholder)
            return {
                "sender": data.get("sender_id", ""),
                "content": data.get("message", ""),
                "message_type": MessageType.TEXT,
                "external_id": data.get("message_id"),
                "raw_data": data
            }
        except Exception as e:
            logger.error(f"Error processing Instagram webhook: {e}")
            return None
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose() 