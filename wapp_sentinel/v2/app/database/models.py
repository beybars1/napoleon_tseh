from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class WhatsAppNotification(Base):
    """SQLAlchemy model for WhatsApp notifications"""
    __tablename__ = "whatsapp_notifications"

    id = Column(Integer, primary_key=True)
    receipt_id = Column(String, nullable=False)
    message_type = Column(String, nullable=True)
    chat_id = Column(String, nullable=True)
    sender_id = Column(String, nullable=True)
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
        Универсальный парсер для разных типов сообщений Green API
        """
        body = notification_data.get('body', {})
        message_data = body.get('messageData', {})
        type_message = message_data.get('typeMessage')
        type_webhook = body.get('typeWebhook')

        message_text = None
        if type_message == "textMessage":
            message_text = message_data.get('textMessageData', {}).get('textMessage')
        elif type_message == "extendedTextMessage":
            message_text = message_data.get('extendedTextMessageData', {}).get('text')
        elif type_message == "quotedMessage":
            message_text = message_data.get('extendedTextMessageData', {}).get('text') \
                or message_data.get('quotedMessage', {}).get('textMessage')
        elif type_webhook == "outgoingAPIMessageReceived":
            message_text = message_data.get('extendedTextMessageData', {}).get('text')
        elif type_webhook == "outgoingMessageReceived":
            # Для outgoingMessageReceived, если есть extendedTextMessageData.text, берем его, иначе quotedMessage.textMessage
            message_text = message_data.get('extendedTextMessageData', {}).get('text') \
                or message_data.get('quotedMessage', {}).get('textMessage')
        # Можно добавить другие типы по необходимости

        return cls(
            receipt_id=str(notification_data.get('receiptId')),
            message_type=type_webhook,
            chat_id=body.get('senderData', {}).get('chatId'),
            sender_id=body.get('senderData', {}).get('sender'),
            sender_name=body.get('senderData', {}).get('senderName'),
            message_text=message_text,
            media_url=message_data.get('fileMessageData', {}).get('downloadUrl'),
            message_timestamp=datetime.fromtimestamp(body.get('timestamp')),
            raw_data=notification_data
        )

class OutgoingAPIMessage(Base):
    __tablename__ = "outgoing_api_message"
    id = Column(Integer, primary_key=True)
    receipt_id = Column(Integer)
    id_message = Column(String)
    timestamp = Column(DateTime(timezone=True))
    chat_id = Column(String)
    sender = Column(String)
    chat_name = Column(String)
    sender_name = Column(String)
    text = Column(Text)
    raw_data = Column(JSONB)

class IncomingMessage(Base):
    __tablename__ = "incoming_message"
    id = Column(Integer, primary_key=True)
    receipt_id = Column(Integer)
    id_message = Column(String)
    timestamp = Column(DateTime(timezone=True))
    chat_id = Column(String)
    sender = Column(String)
    chat_name = Column(String)
    sender_name = Column(String)
    sender_contact_name = Column(String)
    type_message = Column(String)
    text_message = Column(Text)
    type_webhook = Column(String)
    deleted_message_type = Column(String)
    deleted_message_stanza_id = Column(String)
    raw_data = Column(JSONB)

class IncomingCall(Base):
    __tablename__ = "incoming_call"
    id = Column(Integer, primary_key=True)
    receipt_id = Column(Integer)
    from_id = Column(String)
    status = Column(String)
    id_message = Column(String)
    timestamp = Column(DateTime(timezone=True))
    raw_data = Column(JSONB)

class OutgoingMessage(Base):
    __tablename__ = "outgoing_message"
    id = Column(Integer, primary_key=True)
    receipt_id = Column(Integer)
    id_message = Column(String)
    timestamp = Column(DateTime(timezone=True))
    chat_id = Column(String)
    sender = Column(String)
    chat_name = Column(String)
    sender_name = Column(String)
    text = Column(Text)
    raw_data = Column(JSONB)

class OutgoingMessageStatus(Base):
    __tablename__ = "outgoing_message_status"
    id = Column(Integer, primary_key=True)
    receipt_id = Column(Integer)
    chat_id = Column(String)
    status = Column(String)
    id_message = Column(String)
    send_by_api = Column(Boolean)
    timestamp = Column(DateTime(timezone=True))
    raw_data = Column(JSONB)
