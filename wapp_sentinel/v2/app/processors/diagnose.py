"""
Diagnostic script to check why Worker 2 is not processing messages
"""

import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.database.database import SessionLocal
from app.database.models import IncomingMessage, OutgoingMessage, OutgoingAPIMessage
from dotenv import load_dotenv

load_dotenv()

TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID", "120363403664602093@g.us")

def check_database():
    """Check database for messages"""
    db = SessionLocal()
    
    print("=" * 60)
    print("DIAGNOSTIC CHECK")
    print("=" * 60)
    print(f"\nTarget Chat ID: {TARGET_CHAT_ID}")
    print()
    
    # Check incoming_message
    print("[1] Checking incoming_message table...")
    incoming = db.query(IncomingMessage).filter(
        IncomingMessage.chat_id == TARGET_CHAT_ID
    ).order_by(IncomingMessage.timestamp.desc()).limit(5).all()
    
    print(f"    Total messages from target chat: {db.query(IncomingMessage).filter(IncomingMessage.chat_id == TARGET_CHAT_ID).count()}")
    print(f"    Unprocessed messages: {db.query(IncomingMessage).filter(IncomingMessage.chat_id == TARGET_CHAT_ID, IncomingMessage.order_processed == False).count()}")
    
    if incoming:
        print(f"\n    Last 3 messages:")
        for msg in incoming[:3]:
            print(f"    - ID: {msg.id}, timestamp: {msg.timestamp}, processed: {msg.order_processed}")
            print(f"      text: {msg.text_message[:50] if msg.text_message else 'None'}...")
    
    # Check outgoing_message
    print("\n[2] Checking outgoing_message table...")
    outgoing = db.query(OutgoingMessage).filter(
        OutgoingMessage.chat_id == TARGET_CHAT_ID
    ).order_by(OutgoingMessage.timestamp.desc()).limit(5).all()
    
    print(f"    Total messages from target chat: {db.query(OutgoingMessage).filter(OutgoingMessage.chat_id == TARGET_CHAT_ID).count()}")
    print(f"    Unprocessed messages: {db.query(OutgoingMessage).filter(OutgoingMessage.chat_id == TARGET_CHAT_ID, OutgoingMessage.order_processed == False).count()}")
    
    if outgoing:
        print(f"\n    Last 3 messages:")
        for msg in outgoing[:3]:
            print(f"    - ID: {msg.id}, timestamp: {msg.timestamp}, processed: {msg.order_processed}")
            print(f"      text: {msg.text[:50] if msg.text else 'None'}...")
    
    # Check outgoing_api_message
    print("\n[3] Checking outgoing_api_message table...")
    outgoing_api = db.query(OutgoingAPIMessage).filter(
        OutgoingAPIMessage.chat_id == TARGET_CHAT_ID
    ).order_by(OutgoingAPIMessage.timestamp.desc()).limit(5).all()
    
    print(f"    Total messages from target chat: {db.query(OutgoingAPIMessage).filter(OutgoingAPIMessage.chat_id == TARGET_CHAT_ID).count()}")
    print(f"    Unprocessed messages: {db.query(OutgoingAPIMessage).filter(OutgoingAPIMessage.chat_id == TARGET_CHAT_ID, OutgoingAPIMessage.order_processed == False).count()}")
    
    if outgoing_api:
        print(f"\n    Last 3 messages:")
        for msg in outgoing_api[:3]:
            print(f"    - ID: {msg.id}, timestamp: {msg.timestamp}, processed: {msg.order_processed}")
            print(f"      text: {msg.text[:50] if msg.text else 'None'}...")
    
    # Check ALL recent messages (any chat_id)
    print("\n[4] Checking ALL recent messages (any chat_id)...")
    all_incoming = db.query(IncomingMessage).order_by(IncomingMessage.timestamp.desc()).limit(3).all()
    
    print(f"    Last 3 incoming messages from ANY chat:")
    for msg in all_incoming:
        print(f"    - ID: {msg.id}, chat_id: {msg.chat_id}")
        print(f"      timestamp: {msg.timestamp}, processed: {msg.order_processed}")
        print(f"      text: {msg.text_message[:50] if msg.text_message else 'None'}...")
        print(f"      Match target? {msg.chat_id == TARGET_CHAT_ID}")
        print()
    
    db.close()

if __name__ == "__main__":
    check_database()
