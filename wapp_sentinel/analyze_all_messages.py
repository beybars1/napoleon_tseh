#!/usr/bin/env python3
"""
Comprehensive message analysis script
This will help understand what messages are actually available in your WhatsApp group
"""

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from greenapi_service import get_all_available_messages
from database import get_db, Order
from openai_service import parse_order

load_dotenv()

MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")

def analyze_all_available_messages():
    """Get and analyze ALL available messages"""
    print("🔍 COMPREHENSIVE MESSAGE ANALYSIS")
    print("=" * 60)
    
    # Get all available messages
    messages = get_all_available_messages(MAIN_GROUP_CHAT_ID)
    
    if not messages:
        print("❌ No messages retrieved!")
        return
    
    print(f"\n📊 DETAILED ANALYSIS OF {len(messages)} MESSAGES")
    print("-" * 60)
    
    # Analyze by time periods
    now = datetime.now()
    timeframes = [
        ("Last 24 hours", 1),
        ("Last 3 days", 3), 
        ("Last 7 days", 7),
        ("Last 14 days", 14),
        ("Last 30 days", 30),
        ("All available", 9999)
    ]
    
    for label, days in timeframes:
        if days == 9999:
            filtered_messages = messages
        else:
            cutoff_time = now - timedelta(days=days)
            cutoff_timestamp = int(cutoff_time.timestamp())
            filtered_messages = [
                msg for msg in messages 
                if msg.get('timestamp', 0) >= cutoff_timestamp
            ]
        
        incoming_count = sum(1 for msg in filtered_messages if msg.get('type') == 'incoming')
        outgoing_count = sum(1 for msg in filtered_messages if msg.get('type') == 'outgoing')
        
        print(f"📅 {label:15}: {len(filtered_messages):3d} total | 📨 {incoming_count:3d} incoming | 📤 {outgoing_count:3d} outgoing")
    
    # Show recent incoming messages in detail
    print(f"\n📨 RECENT INCOMING MESSAGES (Details)")
    print("-" * 60)
    
    # Get incoming messages from last 7 days
    seven_days_ago = now - timedelta(days=7)
    seven_days_timestamp = int(seven_days_ago.timestamp())
    
    recent_incoming = [
        msg for msg in messages 
        if msg.get('type') == 'incoming' and msg.get('timestamp', 0) >= seven_days_timestamp
    ]
    
    # Sort by timestamp (newest first)
    recent_incoming.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    
    print(f"Found {len(recent_incoming)} incoming messages from last 7 days:")
    
    for i, msg in enumerate(recent_incoming[:20]):  # Show first 20
        timestamp = msg.get('timestamp', 0)
        msg_time = datetime.fromtimestamp(timestamp) if timestamp else 'Unknown'
        msg_text = msg.get('textMessage', '').strip()
        sender_data = msg.get('senderData', {})
        sender_name = sender_data.get('senderName', 'Unknown')
        
        print(f"\n{i+1:2d}. 🕐 {msg_time}")
        print(f"    👤 From: {sender_name}")
        print(f"    💬 Text: {msg_text[:100]}{'...' if len(msg_text) > 100 else ''}")
        
        # Quick order detection
        if any(keyword in msg_text.lower() for keyword in ['заказ', 'торт', 'наполеон', 'время']):
            print(f"    🛒 POTENTIAL ORDER!")

def process_all_available_messages():
    """Process ALL available messages (not just last 7 days)"""
    print("\n🔄 PROCESSING ALL AVAILABLE MESSAGES")
    print("=" * 60)
    
    # Get all available messages
    messages = get_all_available_messages(MAIN_GROUP_CHAT_ID)
    
    if not messages:
        print("❌ No messages to process!")
        return
    
    # Filter for incoming messages only
    incoming_messages = [msg for msg in messages if msg.get('type') == 'incoming']
    
    print(f"📝 Processing {len(incoming_messages)} incoming messages...")
    
    db = next(get_db())
    
    try:
        processed_count = 0
        order_count = 0
        skipped_count = 0
        
        for i, msg in enumerate(incoming_messages):
            try:
                msg_id = msg.get('idMessage')
                msg_text = msg.get('textMessage', '').strip()
                
                if not msg_id or not msg_text:
                    skipped_count += 1
                    continue
                
                # Check if already processed
                existing = db.query(Order).filter(Order.message_id == msg_id).first()
                if existing:
                    skipped_count += 1
                    continue
                
                # Show progress
                timestamp = msg.get('timestamp', 0)
                msg_time = datetime.fromtimestamp(timestamp) if timestamp else 'Unknown'
                print(f"[{i+1}/{len(incoming_messages)}] {msg_time}: {msg_text[:50]}...")
                
                # Parse with OpenAI
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
                    order_count += 1
                    print(f"    ✅ ORDER: {parsed_data.get('customer_name', 'Unknown')} - {parsed_data.get('order_date')}")
                else:
                    print(f"    📝 Regular message")
                
                processed_count += 1
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
                continue
        
        print(f"\n🎉 PROCESSING COMPLETE!")
        print(f"   📥 Messages processed: {processed_count}")
        print(f"   🛒 Orders found: {order_count}")
        print(f"   ⏭️  Skipped: {skipped_count}")
        
        # Show orders summary
        if order_count > 0:
            print(f"\n🛒 ORDERS FOUND:")
            orders = db.query(Order).filter(Order.order_date.isnot(None)).order_by(Order.created_at.desc()).limit(10).all()
            
            for order in orders:
                parsed = json.loads(order.parsed_data)
                print(f"   • {order.customer_name or 'Unknown'}: {order.order_date} at {order.delivery_time}")
        
    except Exception as e:
        print(f"❌ Processing error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "process":
        analyze_all_available_messages()
        print("\n" + "="*60)
        process_all_available_messages()
    else:
        analyze_all_available_messages()
        print(f"\n💡 To process all messages into database, run:")
        print(f"   python analyze_all_messages.py process")
        print(f"\n⚠️  This will make many OpenAI API calls!")
