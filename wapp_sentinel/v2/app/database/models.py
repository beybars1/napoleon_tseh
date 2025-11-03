from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, Index, Boolean, Date, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class Order(Base):
    """SQLAlchemy model for parsed orders"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    
    # Связь с исходным сообщением
    message_id = Column(Integer, nullable=False)
    message_table = Column(String(50), nullable=False)  # 'incoming_message', 'outgoing_message', 'outgoing_api_message'
    chat_id = Column(String, nullable=False)
    
    # Даты
    order_accepted_date = Column(DateTime(timezone=False), nullable=False)
    estimated_delivery_datetime = Column(DateTime(timezone=False))
    
    # Оплата
    payment_status = Column(Boolean)  # True=paid, False=unpaid, None=unknown
    
    # Контакты
    contact_number_primary = Column(String(20))
    contact_number_secondary = Column(String(20))
    
    # Товары
    items = Column(JSONB)  # [{"name": "...", "quantity": "..."}]
    
    # Имя клиента
    client_name = Column(String(100))
    
    # Сырые данные
    raw_message_text = Column(Text, nullable=False)
    openai_response = Column(JSONB)
    
    # Мета
    confidence = Column(String(20))  # 'high', 'medium', 'low'
    processing_status = Column(String(20), default='completed')
    
    created_at = Column(DateTime(timezone=False), server_default='now()')
    updated_at = Column(DateTime(timezone=False), server_default='now()')
    
    __table_args__ = (
        UniqueConstraint('message_table', 'message_id', name='orders_message_unique'),
        Index('idx_orders_chat_id', 'chat_id'),
        Index('idx_orders_delivery_datetime', 'estimated_delivery_datetime'),
        Index('idx_orders_accepted_date', 'order_accepted_date'),
        Index('idx_orders_payment_status', 'payment_status'),
    )
    
    def __repr__(self):
        return f"<Order(id={self.id}, delivery={self.estimated_delivery_datetime}, client_name={self.client_name})>"

class OutgoingAPIMessage(Base):
    __tablename__ = "outgoing_api_message"
    id = Column(Integer, primary_key=True)
    receipt_id = Column(String)
    id_message = Column(String)
    timestamp = Column(DateTime(timezone=True))
    chat_id = Column(String)
    sender = Column(String)
    chat_name = Column(String)
    sender_name = Column(String)
    text = Column(Text)
    raw_data = Column(JSONB)
    order_processed = Column(Boolean, server_default='false')

class IncomingMessage(Base):
    __tablename__ = "incoming_message"
    id = Column(Integer, primary_key=True)
    receipt_id = Column(String)
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
    order_processed = Column(Boolean, server_default='false')

class IncomingCall(Base):
    __tablename__ = "incoming_call"
    id = Column(Integer, primary_key=True)
    receipt_id = Column(String)
    from_id = Column(String)
    status = Column(String)
    id_message = Column(String)
    timestamp = Column(DateTime(timezone=True))
    raw_data = Column(JSONB)

class OutgoingMessage(Base):
    __tablename__ = "outgoing_message"
    id = Column(Integer, primary_key=True)
    receipt_id = Column(String)
    id_message = Column(String)
    timestamp = Column(DateTime(timezone=True))
    chat_id = Column(String)
    sender = Column(String)
    chat_name = Column(String)
    sender_name = Column(String)
    text = Column(Text)
    raw_data = Column(JSONB)
    order_processed = Column(Boolean, server_default='false')

class OutgoingMessageStatus(Base):
    __tablename__ = "outgoing_message_status"
    id = Column(Integer, primary_key=True)
    receipt_id = Column(String)
    chat_id = Column(String)
    status = Column(String)
    id_message = Column(String)
    send_by_api = Column(Boolean)
    timestamp = Column(DateTime(timezone=True))
    raw_data = Column(JSONB)
