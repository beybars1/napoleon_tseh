#!/usr/bin/env python3
"""
Bulk Message Processor for Napoleon WhatsApp Orders
This script fetches ALL messages from the last 7 days and processes them into the database.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database import get_db, Order
from openai_service import parse_order
from greenapi_service import GREEN_API_ID_INSTANCE, GREEN_API_TOKEN

load_dotenv()

# Load chat ID from environment
MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")

def get_all_messages_last_7_days(chat_id: str):
    """Get ALL messages from last 7 days using GreenAPI"""
    print(f"📥 Fetching messages from last 7 days for: {chat_id}")
    
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/getChatHistory/{GREEN_API_TOKEN}"
    
    # Calculate 7 days ago timestamp
    seven_days_ago = datetime.now() - timedelta(days=7)
    cutoff_timestamp = int(seven_days_ago.timestamp())
    
    print(f"📅 Looking for messages after: {seven_days_ago}")
    
    all_messages = []
    
    # Start with getting a large batch
    payload = {
        "chatId": chat_id,
        "count": 1000  # Get maximum messages
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"❌ Error getting chat history: {response.text}")
            return []
        
        messages = response.json() or []
        print(f"📊 Retrieved {len(messages)} total messages from API")
        
        # Filter for last 7 days
        for msg in messages:
            msg_timestamp = msg.get('timestamp', 0)
            if msg_timestamp >= cutoff_timestamp:
                all_messages.append(msg)
        
        print(f"✅ Found {len(all_messages)} messages from last 7 days")
        
        # Show breakdown by type
        incoming_count = sum(1 for msg in all_messages if msg.get('type') == 'incoming')
        outgoing_count = sum(1 for msg in all_messages if msg.get('type') == 'outgoing')
        
        print(f"   📨 Incoming: {incoming_count}")
        print(f"   📤 Outgoing: {outgoing_count}")
        
        return all_messages
        
    except Exception as e:
        print(f"❌ Error fetching messages: {e}")
        return []

def bulk_process_messages():
    """Process all messages from last 7 days and populate database"""
    print("🚀 BULK MESSAGE PROCESSING - LAST 7 DAYS")
    print("=" * 60)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Fetch all messages
        messages = get_all_messages_last_7_days(MAIN_GROUP_CHAT_ID)
        
        if not messages:
            print("❌ No messages found to process")
            return
        
        # Sort messages by timestamp (oldest first)
        messages.sort(key=lambda x: x.get('timestamp', 0))
        
        processed_count = 0
        order_count = 0
        skipped_count = 0
        error_count = 0
        
        print(f"\n🔄 Processing {len(messages)} messages...")
        print("-" * 40)
        
        for i, msg in enumerate(messages):
            try:
                msg_id = msg.get('idMessage')
                msg_timestamp = msg.get('timestamp', 0)
                msg_time = datetime.fromtimestamp(msg_timestamp) if msg_timestamp else None
                msg_text = msg.get('textMessage', '')
                msg_type = msg.get('type', '')
                
                print(f"[{i+1}/{len(messages)}] {msg_time} - {msg_type[:3]}: {msg_text[:50]}...")
                
                # Skip if no message ID or text
                if not msg_id or not msg_text:
                    print("   ⏭️  Skipped: No ID or text")
                    skipped_count += 1
                    continue
                
                # Skip outgoing messages (your own messages)
                if msg_type == 'outgoing':
                    print("   ⏭️  Skipped: Outgoing message")
                    skipped_count += 1
                    continue
                
                # Check if already processed
                existing = db.query(Order).filter(Order.message_id == msg_id).first()
                if existing:
                    print("   ⏭️  Skipped: Already in database")
                    skipped_count += 1
                    continue
                
                # Parse with OpenAI
                print("   🤖 Parsing with OpenAI...")
                parsed_data = parse_order(msg_text)
                
                # Create order record
                order = Order(
                    message_id=msg_id,
                    chat_id=MAIN_GROUP_CHAT_ID,
                    sender=msg.get('senderData', {}).get('sender', ''),
                    raw_message=msg_text,
                    parsed_data=json.dumps(parsed_data),
                    order_date=parsed_data.get("order_date") if parsed_data.get("is_order") else None,
                    customer_name=parsed_data.get("customer_name") if parsed_data.get("is_order") else None,
                    total_amount=parsed_data.get("total_amount") if parsed_data.get("is_order") else None,
                    delivery_time=parsed_data.get("delivery_time") if parsed_data.get("is_order") else None,
                    processed=not parsed_data.get("is_order", False)
                )
                
                db.add(order)
                db.commit()
                
                if parsed_data.get("is_order"):
                    print(f"   ✅ ORDER: {parsed_data.get('customer_name', 'Unknown')} - {parsed_data.get('order_date')}")
                    order_count += 1
                else:
                    print("   📝 Non-order message saved")
                
                processed_count += 1
                
            except Exception as e:
                print(f"   ❌ Error processing message: {e}")
                error_count += 1
                continue
        
        print("\n" + "=" * 60)
        print("📊 BULK PROCESSING COMPLETE")
        print("=" * 60)
        print(f"📥 Total messages fetched: {len(messages)}")
        print(f"✅ Successfully processed: {processed_count}")
        print(f"🛒 Orders found: {order_count}")
        print(f"⏭️  Skipped: {skipped_count}")
        print(f"❌ Errors: {error_count}")
        
        # Show order summary
        if order_count > 0:
            print("\n🛒 ORDERS SUMMARY:")
            orders = db.query(Order).filter(Order.order_date.isnot(None)).order_by(Order.created_at.desc()).limit(10).all()
            
            for order in orders:
                parsed = json.loads(order.parsed_data)
                print(f"   • {order.customer_name or 'Unknown'}: {order.order_date} at {order.delivery_time}")
        
        print(f"\n✅ Database now contains all messages from last 7 days!")
        print(f"🔗 Check results: curl http://localhost:8000/orders")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        db.close()

def show_message_preview():
    """Show preview of messages that will be processed"""
    print("👀 PREVIEW: Messages from last 7 days")
    print("=" * 50)
    
    messages = get_all_messages_last_7_days(MAIN_GROUP_CHAT_ID)
    
    if not messages:
        print("❌ No messages found")
        return
    
    # Show first 10 messages as preview
    print(f"📋 Showing first 10 of {len(messages)} messages:")
    print("-" * 50)
    
    for i, msg in enumerate(messages[:10]):
        msg_timestamp = msg.get('timestamp', 0)
        msg_time = datetime.fromtimestamp(msg_timestamp) if msg_timestamp else 'Unknown'
        msg_text = msg.get('textMessage', '')[:100]
        msg_type = msg.get('type', 'unknown')
        
        print(f"{i+1}. [{msg_time}] {msg_type}: {msg_text}...")
    
    if len(messages) > 10:
        print(f"... and {len(messages) - 10} more messages")
    
    print(f"\n💡 To process all {len(messages)} messages, run:")
    print("   python bulk_process_messages.py process")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "process":
        bulk_process_messages()
    elif len(sys.argv) > 1 and sys.argv[1] == "preview":
        show_message_preview()
    else:
        print("🔄 BULK MESSAGE PROCESSOR")
        print("=" * 40)
        print("This script processes ALL messages from your main WhatsApp group")
        print("from the last 7 days and populates your database with orders.")
        print("\nCommands:")
        print("  python bulk_process_messages.py preview  - Show messages preview")
        print("  python bulk_process_messages.py process  - Process all messages")
        print("\n⚠️  WARNING: This will make many OpenAI API calls!")
        print("💡 Tip: Run 'preview' first to see what will be processed")
