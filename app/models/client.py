from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Basic information
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, nullable=True)
    
    # Social media handles
    whatsapp_id = Column(String, nullable=True)
    telegram_id = Column(String, nullable=True)
    instagram_handle = Column(String, nullable=True)
    
    # Address information
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    
    # Client preferences and metadata
    preferences = Column(JSON, nullable=True)  # Store dietary preferences, favorite items, etc.
    tags = Column(JSON, nullable=True)  # Store tags like "VIP", "Regular", etc.
    notes = Column(Text, nullable=True)  # Internal notes about the client
    
    # Status and tracking
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    total_orders = Column(Integer, default=0)
    total_spent = Column(Integer, default=0)  # Store in cents
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_contact = Column(DateTime(timezone=True), nullable=True)
    last_order = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    # orders = relationship("Order", back_populates="client")  # Temporarily disabled due to import issue
    conversations = relationship("Conversation", back_populates="client")
    
    @property
    def full_name(self):
        """Get full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return f"Client {self.phone}"
    
    def __repr__(self):
        return f"<Client(id={self.id}, phone={self.phone}, name={self.full_name})>" 