from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

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
