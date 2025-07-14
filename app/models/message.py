from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import uuid

from app.core.database import Base


class MessageType(enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    STICKER = "sticker"
    VOICE = "voice"
    SYSTEM = "system"


class MessageDirection(enum.Enum):
    INCOMING = "incoming"  # From client to business
    OUTGOING = "outgoing"  # From business to client


class MessageStatus(enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    PENDING = "pending"


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Conversation relationship
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    
    # Message details
    direction = Column(Enum(MessageDirection), nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)
    status = Column(Enum(MessageStatus), default=MessageStatus.SENT)
    
    # Content
    content = Column(Text, nullable=True)  # Text content
    media_url = Column(String, nullable=True)  # URL for media files
    media_type = Column(String, nullable=True)  # MIME type
    media_size = Column(Integer, nullable=True)  # File size in bytes
    
    # External platform data
    external_id = Column(String, nullable=True)  # ID from external platform
    external_data = Column(JSON, nullable=True)  # Raw data from platform
    
    # AI and processing
    ai_processed = Column(Boolean, default=False)
    ai_response = Column(Text, nullable=True)
    ai_confidence = Column(Integer, nullable=True)  # 0-100
    ai_intent = Column(String, nullable=True)  # Detected intent
    ai_entities = Column(JSON, nullable=True)  # Extracted entities
    
    # Metadata
    message_metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    @property
    def is_from_client(self):
        """Check if message is from client"""
        return self.direction == MessageDirection.INCOMING
    
    @property
    def is_from_business(self):
        """Check if message is from business"""
        return self.direction == MessageDirection.OUTGOING
    
    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, direction={self.direction})>" 