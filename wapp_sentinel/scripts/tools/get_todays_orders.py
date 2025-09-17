#!/usr/bin/env python3
"""
Get today's orders from main group
This script focuses on recent messages (last 24-48 hours) to find today's orders
"""

import os
import json
import requests
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
from database import get_db, Order
from openai_service import parse_order

load_dotenv()

GREEN_API_ID_INSTANCE = os.getenv("GREEN_API_ID_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")
BASE_URL = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}"

def get_recent_messages_for_today():
    """Get messages from last 48 hours to find today's orders"""
    print("📅 GETTING TODAY'S ORDERS")
    print("=" * 50)
    
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    
    # Get messages from last 48 hours
    hours_back = 48
    cutoff_time = datetime.now() - timedelta(hours=hours_back)
    cutoff_timestamp = int(cutoff_time.timestamp())
    
    print(f"🕐 Looking for messages since: {cutoff_time}")
    print(f"📱 Chat ID: {MAIN_GROUP_CHAT_ID}")
    
    payload = {
        "chatId": MAIN_GROUP_CHAT_ID,
        "count": 100  # Should be enough for 48 hours
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return []
        
        messages = response.json() or []
        print(f"📥 Retrieved {len(messages)} total messages")
        
        # Filter for last 48 hours
        recent_messages = []
        for msg in messages:
            msg_timestamp = msg.get('timestamp', 0)
            if msg_timestamp >= cutoff_timestamp:
                recent_messages.append(msg)
        
        print(f"🗓️  Found {len(recent_messages)} messages from last 48 hours")
        
        # Show breakdown
        incoming_count = sum(1 for msg in recent_messages if msg.get('type') == 'incoming')
        outgoing_count = sum(1 for msg in recent_messages if msg.get('type') == 'outgoing')
        
        print(f"📊 Message types:")
        print(f"   📨 Incoming: {incoming_count}")
        print(f"   📤 Outgoing: {outgoing_count}")
        
        # Show all recent messages
        if recent_messages:
            print(f"\n📝 RECENT MESSAGES (last 48h):")
            print("-" * 60)
            
            for i, msg in enumerate(recent_messages):
                timestamp = msg.get('timestamp', 0)
                msg_time = datetime.fromtimestamp(timestamp) if timestamp else 'No time'
                msg_type = msg.get('type', 'unknown')
                msg_text = msg.get('textMessage', '').strip()
                
                print(f"{i+1}. 🕐 {msg_time}")
                print(f"   📱 Type: {msg_type}")
                print(f"   💬 Text: {msg_text}")
                
                # Quick order detection
                order_keywords = ['заказ', 'торт', 'наполеон', 'время', 'доставка', 'оплачено']
                if any(keyword in msg_text.lower() for keyword in order_keywords):
                    print(f"   🛒 POTENTIAL ORDER!")
                
                print()
        
        return recent_messages
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def process_todays_messages(messages):
    """Process recent messages to extract orders"""
    print(f"🔄 PROCESSING RECENT MESSAGES FOR ORDERS")
    print("=" * 50)
    
    if not messages:
        print("❌ No messages to process")
        return
    
    # Filter messages with text (both incoming and outgoing)
    processable_messages = [msg for msg in messages if msg.get('textMessage', '').strip()]
    
    print(f"📝 Processing {len(processable_messages)} messages with text")
    
    db = next(get_db())
    
    try:
        processed_count = 0
        order_count = 0
        skipped_count = 0
        orders_found = []
        
        for i, msg in enumerate(processable_messages):
            try:
                msg_id = msg.get('idMessage')
                msg_text = msg.get('textMessage', '').strip()
                timestamp = msg.get('timestamp', 0)
                msg_time = datetime.fromtimestamp(timestamp) if timestamp else 'Unknown'
                msg_type = msg.get('type', 'unknown')
                
                print(f"\n[{i+1}/{len(processable_messages)}] {msg_time} ({msg_type}):")
                print(f"Text: {msg_text[:80]}...")
                
                if not msg_id or not msg_text:
                    skipped_count += 1
                    continue
                
                # Check if already processed
                existing = db.query(Order).filter(Order.message_id == msg_id).first()
                if existing:
                    print("   ⏭️  Already in database")
                    skipped_count += 1
                    continue
                
                # Parse with OpenAI
                print("   🤖 Analyzing with OpenAI...")
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
                    customer = parsed_data.get('customer_name', 'Unknown')
                    order_date = parsed_data.get('order_date', 'No date')
                    delivery_time = parsed_data.get('delivery_time', 'No time')
                    
                    print(f"   ✅ ORDER FOUND: {customer} - {order_date} at {delivery_time}")
                    
                    orders_found.append({
                        'customer': customer,
                        'date': order_date,
                        'time': delivery_time,
                        'items': parsed_data.get('items', []),
                        'message_time': msg_time
                    })
                else:
                    print("   📝 Not an order")
                
                processed_count += 1
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
        
        # Summary
        print(f"\n🎉 PROCESSING COMPLETE!")
        print("=" * 50)
        print(f"📥 Messages processed: {processed_count}")
        print(f"🛒 Orders found: {order_count}")
        print(f"⏭️  Skipped: {skipped_count}")
        
        # Show today's orders
        if orders_found:
            today_str = date.today().strftime("%Y-%m-%d")
            todays_orders = [order for order in orders_found if order['date'] == today_str]
            
            print(f"\n📅 TODAY'S ORDERS ({today_str}):")
            print("-" * 50)
            
            if todays_orders:
                for i, order in enumerate(todays_orders):
                    print(f"{i+1}. 👤 {order['customer']}")
                    print(f"   🕐 Delivery: {order['time']}")
                    print(f"   📱 Message: {order['message_time']}")
                    if order['items']:
                        print(f"   🛒 Items:")
                        for item in order['items']:
                            product = item.get('product', 'Unknown')
                            quantity = item.get('quantity', '')
                            print(f"      - {product} {quantity}")
                    print()
            else:
                print("❌ No orders found for today")
                print(f"\n📋 All orders found (any date):")
                for i, order in enumerate(orders_found):
                    print(f"{i+1}. {order['customer']} - {order['date']} at {order['time']}")
        else:
            print("❌ No orders found in recent messages")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

def quick_check_todays_orders():
    """Quick check - just show if we have today's orders in database"""
    print(f"🔍 QUICK CHECK: TODAY'S ORDERS IN DATABASE")
    print("=" * 50)
    
    db = next(get_db())
    
    try:
        today_str = date.today().strftime("%Y-%m-%d")
        print(f"📅 Checking for orders on: {today_str}")
        
        # Check database for today's orders
        todays_orders = db.query(Order).filter(Order.order_date == today_str).all()
        
        print(f"📊 Found {len(todays_orders)} orders for today in database")
        
        if todays_orders:
            print(f"\n📋 TODAY'S ORDERS:")
            for i, order in enumerate(todays_orders):
                parsed = json.loads(order.parsed_data)
                customer = order.customer_name or 'Unknown'
                delivery_time = order.delivery_time or 'No time'
                print(f"{i+1}. {customer} - {delivery_time}")
                
                # Show items
                items = parsed.get('items', [])
                if items:
                    for item in items:
                        product = item.get('product', 'Unknown')
                        quantity = item.get('quantity', '')
                        print(f"   - {product} {quantity}")
        else:
            print("❌ No orders for today in database")
            print("💡 Try running: python get_todays_orders.py process")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "process":
        # Process recent messages
        messages = get_recent_messages_for_today()
        if messages:
            process_todays_messages(messages)
    elif len(sys.argv) > 1 and sys.argv[1] == "check":
        # Just check database
        quick_check_todays_orders()
    else:
        # Show recent messages only
        messages = get_recent_messages_for_today()
        
        print(f"\n💡 NEXT STEPS:")
        print("To process these messages for orders:")
        print("   python get_todays_orders.py process")
        print("\nTo check existing orders in database:")
        print("   python get_todays_orders.py check")

