from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class WhatsAppNotification(Base):
    """SQLAlchemy model for WhatsApp notifications"""
    __tablename__ = "whatsapp_notifications"

    id = Column(Integer, primary_key=True)
    receipt_id = Column(String, nullable=False)
    message_type = Column(String, nullable=True)
    chat_id = Column(String, nullable=False)
    sender_id = Column(String, nullable=False)
    sender_name = Column(String, nullable=True)
    message_text = Column(Text, nullable=True)
    media_url = Column(String, nullable=True)
    raw_data = Column(JSONB, nullable=False)
    processing_status = Column(String, nullable=False, server_default='new')
    message_timestamp = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), server_default='now()')
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Индексы для оптимизации запросов
    __table_args__ = (
        Index('ix_whatsapp_notifications_chat_id', 'chat_id'),
        Index('ix_whatsapp_notifications_sender_id', 'sender_id'),
        Index('ix_whatsapp_notifications_message_timestamp', 'message_timestamp'),
        Index('ix_whatsapp_notifications_processing_status', 'processing_status'),
    )

    def __repr__(self):
        return f"<WhatsAppNotification(id={self.id}, receipt_id={self.receipt_id}, type={self.message_type})>"

    @classmethod
    def from_green_api(cls, notification_data: Dict[str, Any]) -> "WhatsAppNotification":
        """
        Создает объект уведомления из данных Green API
        """
        body = notification_data.get('body', {})
        message_data = body.get('messageData', {})
        
        return cls(
            receipt_id=str(notification_data.get('receiptId')),
            message_type=body.get('typeWebhook'),
            chat_id=body.get('senderData', {}).get('chatId'),
            sender_id=body.get('senderData', {}).get('sender'),
            sender_name=body.get('senderData', {}).get('senderName'),
            message_text=message_data.get('textMessageData', {}).get('textMessage'),
            media_url=message_data.get('fileMessageData', {}).get('downloadUrl'),
            message_timestamp=datetime.fromtimestamp(body.get('timestamp')),
            raw_data=notification_data
        )
