from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import uuid

from app.core.database import Base


class ConversationStatus(enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    PENDING = "pending"
    ARCHIVED = "archived"


class ConversationChannel(enum.Enum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    SMS = "sms"
    EMAIL = "email"
    INSTAGRAM = "instagram"
    PHONE = "phone"
    WEB = "web"


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Client relationship
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    
    # Conversation details
    channel = Column(Enum(ConversationChannel), nullable=False)
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE)
    
    # Channel-specific identifiers
    external_id = Column(String, nullable=True)  # ID from external platform
    thread_id = Column(String, nullable=True)  # Thread/chat ID
    
    # Metadata
    title = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)
    priority = Column(Integer, default=0)  # 0=normal, 1=high, 2=urgent
    
    # AI and automation
    ai_enabled = Column(Boolean, default=True)
    auto_response_enabled = Column(Boolean, default=True)
    
    # Statistics
    message_count = Column(Integer, default=0)
    unread_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    client = relationship("Client", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, client_id={self.client_id}, channel={self.channel})>" 