from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, Index, Boolean, Date, UniqueConstraint, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

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


class Conversation(Base):
    """SQLAlchemy model for AI agent conversations"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(String, nullable=False, index=True)
    sender_name = Column(String)
    sender_phone = Column(String)
    status = Column(String, nullable=False, index=True)  # active, completed, abandoned, escalated
    current_step = Column(String)  # current node in graph
    
    # v2 Architecture additions
    last_intent = Column(String(50))  # Last classified intent
    conversation_stage = Column(String(50), default='browsing')  # browsing | ordering | confirming | completed | escalated
    clarification_count = Column(Integer, default=0)  # Track if agent is stuck
    flagged_for_human = Column(Boolean, default=False, index=True)  # Escalation flag
    escalation_reason = Column(String(100))  # Why escalated
    
    created_at = Column(DateTime(timezone=True), server_default='now()', nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default='now()', nullable=False)
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")
    ai_orders = relationship("AIGeneratedOrder", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, chat_id={self.chat_id}, status={self.status})>"


class ConversationMessage(Base):
    """SQLAlchemy model for conversation messages"""
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    intent = Column(String(50))  # v2: Classified intent for user messages
    timestamp = Column(DateTime(timezone=True), server_default='now()', nullable=False, index=True)
    message_metadata = Column(JSONB)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<ConversationMessage(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"


class AIGeneratedOrder(Base):
    """SQLAlchemy model for AI-generated orders"""
    __tablename__ = "ai_generated_orders"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='SET NULL'))
    chat_id = Column(String, nullable=False, index=True)
    client_name = Column(String)
    client_phone = Column(String)
    additional_phone = Column(String)
    items = Column(JSONB, nullable=False)
    estimated_delivery_datetime = Column(DateTime(timezone=True))
    delivery_address = Column(String)
    payment_status = Column(String)
    total_amount = Column(Numeric(10, 2))
    notes = Column(Text)
    validation_status = Column(String, nullable=False, index=True)  # pending, validated, rejected
    created_at = Column(DateTime(timezone=True), server_default='now()', nullable=False)
    confirmed_at = Column(DateTime(timezone=True))
    
    # Relationships
    conversation = relationship("Conversation", back_populates="ai_orders")
    
    def __repr__(self):
        return f"<AIGeneratedOrder(id={self.id}, conversation_id={self.conversation_id}, validation_status={self.validation_status})>"


class Product(Base):
    """SQLAlchemy model for product catalog"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    
    # Identity
    product_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "napoleon_classic"
    name = Column(String(200), nullable=False)  # "Торт Наполеон Классический"
    category = Column(String(50), nullable=False, index=True)  # "cake" | "dessert_set" | "pastry"
    
    # Details
    description = Column(Text)
    price_per_kg = Column(Numeric(10, 2))  # For cakes
    fixed_price = Column(Numeric(10, 2))  # For sets
    available = Column(Boolean, default=True, index=True)
    
    # Attributes (JSONB for flexibility)
    sizes = Column(JSONB)  # ["1kg", "1.5kg", "2kg", "3kg"]
    ingredients = Column(JSONB)  # ["мука", "масло", "яйца", ...]
    allergens = Column(JSONB)  # ["глютен", "яйца", "молоко"]
    
    # Business rules
    preparation_hours = Column(Integer, default=4)  # Minimum lead time
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default='now()', nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default='now()', nullable=False)
    
    def __repr__(self):
        return f"<Product(id={self.product_id}, name={self.name}, category={self.category}, available={self.available})>"

