#!/usr/bin/env python3
"""
Flexible bulk processing with different timeframe options
Since you have 497 messages but only 2 from last 7 days, 
let's try different timeframes or process ALL messages
"""

import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database import get_db, Order
from openai_service import parse_order

load_dotenv()

GREEN_API_ID_INSTANCE = os.getenv("GREEN_API_ID_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")
BASE_URL = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}"

def get_messages_with_timeframe(chat_id: str, days_back: int = None):
    """Get messages with flexible timeframe or ALL messages"""
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    
    payload = {
        "chatId": chat_id,
        "count": 1000  # Maximum
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Error getting chat history: {response.text}")
            return []
        
        messages = response.json() or []
        print(f"📥 Retrieved {len(messages)} total messages from API")
        
        if not messages:
            return []
        
        # Show date range of ALL messages
        timestamps = [msg.get('timestamp', 0) for msg in messages if msg.get('timestamp')]
        if timestamps:
            oldest_ts = min(timestamps)
            newest_ts = max(timestamps)
            oldest_date = datetime.fromtimestamp(oldest_ts)
            newest_date = datetime.fromtimestamp(newest_ts)
            
            print(f"📅 Full message range available:")
            print(f"   Oldest: {oldest_date}")
            print(f"   Newest: {newest_date}")
            print(f"   Total span: {(newest_date - oldest_date).days} days")
        
        # If days_back is specified, filter
        if days_back:
            cutoff_time = datetime.now() - timedelta(days=days_back)
            cutoff_timestamp = int(cutoff_time.timestamp())
            
            filtered_messages = [
                msg for msg in messages 
                if msg.get('timestamp', 0) >= cutoff_timestamp
            ]
            
            print(f"🗓️  After filtering to last {days_back} days: {len(filtered_messages)} messages")
            return filtered_messages
        else:
            print(f"📋 Using ALL {len(messages)} available messages")
            return messages
            
    except Exception as e:
        print(f"Error getting messages: {e}")
        return []

def analyze_timeframes(chat_id: str):
    """Analyze how many messages are in different timeframes"""
    print("🔍 ANALYZING MESSAGE DISTRIBUTION BY TIMEFRAME")
    print("=" * 60)
    
    # Get all messages first
    messages = get_messages_with_timeframe(chat_id)
    
    if not messages:
        print("❌ No messages to analyze")
        return
    
    # Analyze different timeframes
    timeframes = [1, 3, 7, 14, 30, 60, 90, 180, 365]
    
    print(f"📊 MESSAGE DISTRIBUTION:")
    print("-" * 40)
    
    for days in timeframes:
        cutoff_time = datetime.now() - timedelta(days=days)
        cutoff_timestamp = int(cutoff_time.timestamp())
        
        filtered_messages = [
            msg for msg in messages 
            if msg.get('timestamp', 0) >= cutoff_timestamp
        ]
        
        incoming_count = sum(1 for msg in filtered_messages if msg.get('type') == 'incoming')
        outgoing_count = sum(1 for msg in filtered_messages if msg.get('type') == 'outgoing')
        
        print(f"Last {days:3d} days: {len(filtered_messages):3d} total | 📨 {incoming_count:3d} in | 📤 {outgoing_count:3d} out")
    
    # Show ALL available
    incoming_total = sum(1 for msg in messages if msg.get('type') == 'incoming')
    outgoing_total = sum(1 for msg in messages if msg.get('type') == 'outgoing')
    
    print(f"ALL messages: {len(messages):3d} total | 📨 {incoming_total:3d} in | 📤 {outgoing_total:3d} out")
    
    return incoming_total

def process_messages_by_timeframe(chat_id: str, days_back: int = None):
    """Process messages from specified timeframe"""
    
    if days_back:
        print(f"🔄 PROCESSING MESSAGES FROM LAST {days_back} DAYS")
    else:
        print(f"🔄 PROCESSING ALL AVAILABLE MESSAGES")
    
    print("=" * 60)
    
    # Get messages
    messages = get_messages_with_timeframe(chat_id, days_back)
    
    if not messages:
        print("❌ No messages to process")
        return
    
    # Process BOTH incoming and outgoing messages (since manager posts orders)
    processable_messages = [msg for msg in messages if msg.get('textMessage', '').strip()]
    
    if not processable_messages:
        print("❌ No messages with text to process")
        return
    
    incoming_count = sum(1 for msg in processable_messages if msg.get('type') == 'incoming')
    outgoing_count = sum(1 for msg in processable_messages if msg.get('type') == 'outgoing')
    
    print(f"📝 Will process {len(processable_messages)} total messages:")
    print(f"   📨 Incoming: {incoming_count}")
    print(f"   📤 Outgoing: {outgoing_count} (manager's orders)")
    print(f"   💡 Both types will be processed for orders")
    
    # Ask for confirmation
    print(f"\n⚠️  This will make {len(processable_messages)} OpenAI API calls")
    if len(processable_messages) > 50:
        print("   This may take time and cost money!")
    
    response = input(f"\nProceed? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cancelled")
        return
    
    # Process messages
    db = next(get_db())
    
    try:
        processed_count = 0
        order_count = 0
        skipped_count = 0
        
        print(f"\n🔄 Processing {len(processable_messages)} messages...")
        print("-" * 40)
        
        for i, msg in enumerate(processable_messages):
            try:
                msg_id = msg.get('idMessage')
                msg_text = msg.get('textMessage', '').strip()
                timestamp = msg.get('timestamp', 0)
                msg_time = datetime.fromtimestamp(timestamp) if timestamp else 'Unknown'
                
                # Progress every 10 messages
                if i % 10 == 0:
                    print(f"📋 Progress: {i+1}/{len(processable_messages)} ({(i+1)/len(processable_messages)*100:.0f}%)")
                
                if not msg_id or not msg_text:
                    skipped_count += 1
                    continue
                
                # Check if already processed
                existing = db.query(Order).filter(Order.message_id == msg_id).first()
                if existing:
                    skipped_count += 1
                    continue
                
                # Parse with OpenAI
                parsed_data = parse_order(msg_text)
                
                # Create order record
                order = Order(
                    message_id=msg_id,
                    chat_id=chat_id,
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
                    order_count += 1
                    customer = parsed_data.get('customer_name', 'Unknown')
                    order_date = parsed_data.get('order_date', 'No date')
                    print(f"✅ ORDER #{order_count}: {customer} - {order_date}")
                
                processed_count += 1
                
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        
        print(f"\n🎉 PROCESSING COMPLETE!")
        print(f"   📥 Processed: {processed_count}")
        print(f"   🛒 Orders found: {order_count}")
        print(f"   ⏭️  Skipped: {skipped_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        # No arguments - show analysis
        total_incoming = analyze_timeframes(MAIN_GROUP_CHAT_ID)
        
        # Get all messages to calculate total processable
        messages = get_messages_with_timeframe(MAIN_GROUP_CHAT_ID)
        total_processable = len([msg for msg in messages if msg.get('textMessage', '').strip()])
        
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"   📊 Total processable messages: {total_processable}")
        print(f"   📨 Incoming: {total_incoming}")
        print(f"   📤 Outgoing: {total_processable - total_incoming} (likely manager's orders)")
        
        if total_processable > 100:
            print(f"   Consider processing by timeframes:")
            print(f"   python flexible_bulk_process.py 30   # Last 30 days")
            print(f"   python flexible_bulk_process.py 90   # Last 90 days") 
            print(f"   python flexible_bulk_process.py all  # ALL {total_processable} messages")
        else:
            print(f"   You have {total_processable} processable messages - safe to process all")
            print(f"   python flexible_bulk_process.py all")
    
    elif len(sys.argv) == 2:
        if sys.argv[1] == "all":
            process_messages_by_timeframe(MAIN_GROUP_CHAT_ID, None)
        else:
            try:
                days = int(sys.argv[1])
                process_messages_by_timeframe(MAIN_GROUP_CHAT_ID, days)
            except ValueError:
                print("Usage: python flexible_bulk_process.py [days|all]")
                print("Examples:")
                print("  python flexible_bulk_process.py 30   # Last 30 days")
                print("  python flexible_bulk_process.py all  # All messages")
