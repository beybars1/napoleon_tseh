#!/usr/bin/env python3
"""
Process ALL available messages from WhatsApp group
This script will process ALL 497 messages you have available
"""

import json
from datetime import datetime, timedelta

from ..core.config import settings
from ..core.database import get_db, Order
from ..services.openai_service import parse_order
from ..services.greenapi_service import GreenAPIService

class ProcessAllMessages:
    def __init__(self):
        self.greenapi = GreenAPIService()
        self.main_group_chat_id = settings.MAIN_GROUP_CHAT_ID

    def process_all_available_messages(self):
        """Process ALL available messages from your WhatsApp group"""
        print("🔄 PROCESSING ALL AVAILABLE MESSAGES")
        print("=" * 60)
        print("Based on your preview, we have ~497 messages to analyze!")
        
        # Get ALL available messages
        messages = self.greenapi.get_all_available_messages(self.main_group_chat_id)
        
        if not messages:
            print("❌ No messages retrieved!")
            return
        
        print(f"📥 Retrieved {len(messages)} total messages")
        
        # Show date range
        timestamps = [msg.get('timestamp', 0) for msg in messages if msg.get('timestamp')]
        if timestamps:
            oldest_ts = min(timestamps)
            newest_ts = max(timestamps)
            oldest_date = datetime.fromtimestamp(oldest_ts)
            newest_date = datetime.fromtimestamp(newest_ts)
            
            print(f"📅 Message date range:")
            print(f"   Oldest: {oldest_date}")
            print(f"   Newest: {newest_date}")
            print(f"   Total span: {(newest_date - oldest_date).days} days")
        
        # Filter for incoming messages only (skip your own messages)
        incoming_messages = [msg for msg in messages if msg.get('type') == 'incoming']
        outgoing_messages = [msg for msg in messages if msg.get('type') == 'outgoing']
        
        print(f"📊 Message breakdown:")
        print(f"   📨 Incoming: {len(incoming_messages)} (will process these)")
        print(f"   📤 Outgoing: {len(outgoing_messages)} (will skip these)")
        
        if not incoming_messages:
            print("❌ No incoming messages to process!")
            return
        
        # Process messages
        db = next(get_db())
        
        try:
            processed_count = 0
            order_count = 0
            skipped_count = 0
            error_count = 0
            
            print(f"\n🔄 Processing {len(incoming_messages)} incoming messages...")
            print("-" * 60)
            
            for i, msg in enumerate(incoming_messages):
                try:
                    msg_id = msg.get('idMessage')
                    msg_text = msg.get('textMessage', '').strip()
                    timestamp = msg.get('timestamp', 0)
                    msg_time = datetime.fromtimestamp(timestamp) if timestamp else 'Unknown'
                    
                    # Progress indicator
                    if i % 10 == 0 or i == len(incoming_messages) - 1:
                        print(f"📋 Progress: {i+1}/{len(incoming_messages)} ({((i+1)/len(incoming_messages)*100):.1f}%)")
                    
                    print(f"[{i+1}] {msg_time}: {msg_text[:60]}...")
                    
                    if not msg_id or not msg_text:
                        print("   ⏭️  Skipped: No ID or text")
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
                        chat_id=self.main_group_chat_id,
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
                        print(f"   ✅ ORDER: {customer} - {order_date} at {delivery_time}")
                    else:
                        print("   📝 Regular message saved")
                    
                    processed_count += 1
                    
                except Exception as e:
                    print(f"   ❌ Error processing message: {e}")
                    error_count += 1
                    continue
            
            print("\n" + "=" * 60)
            print("🎉 PROCESSING COMPLETE!")
            print("=" * 60)
            print(f"📥 Total messages analyzed: {len(incoming_messages)}")
            print(f"✅ Successfully processed: {processed_count}")
            print(f"🛒 Orders found: {order_count}")
            print(f"⏭️  Skipped (duplicates/empty): {skipped_count}")
            print(f"❌ Errors: {error_count}")
            
            # Show recent orders summary
            if order_count > 0:
                print(f"\n🛒 RECENT ORDERS FOUND:")
                orders = db.query(Order).filter(
                    Order.order_date.isnot(None)
                ).order_by(Order.created_at.desc()).limit(15).all()
                
                for order in orders:
                    parsed = json.loads(order.parsed_data)
                    customer = order.customer_name or 'Unknown'
                    order_date = order.order_date or 'No date'
                    delivery_time = order.delivery_time or 'No time'
                    print(f"   • {customer}: {order_date} at {delivery_time}")
            
            print(f"\n✅ Your database now contains ALL historical orders!")
            print(f"🔗 Check results: curl http://localhost:8000/orders")
            print(f"📊 View today's orders: curl http://localhost:8000/orders/today")
            
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            db.rollback()
        finally:
            db.close()

    def show_quick_preview(self):
        """Show a quick preview of what we'll process"""
        print("👀 QUICK PREVIEW OF ALL MESSAGES")
        print("=" * 50)
        
        messages = self.greenapi.get_all_available_messages(self.main_group_chat_id)
        
        if not messages:
            print("❌ No messages found")
            return
        
        incoming_messages = [msg for msg in messages if msg.get('type') == 'incoming']
        
        print(f"📊 Found {len(messages)} total messages")
        print(f"📨 {len(incoming_messages)} incoming messages (will process)")
        print(f"📤 {len(messages) - len(incoming_messages)} outgoing messages (will skip)")
        
        # Show sample of incoming messages
        print(f"\n📝 Sample incoming messages (first 10):")
        print("-" * 50)
        
        for i, msg in enumerate(incoming_messages[:10]):
            timestamp = msg.get('timestamp', 0)
            msg_time = datetime.fromtimestamp(timestamp) if timestamp else 'Unknown'
            msg_text = msg.get('textMessage', '')[:80]
            
            # Simple order detection
            is_potential_order = any(keyword in msg_text.lower() for keyword in 
                                   ['заказ', 'торт', 'наполеон', 'время', 'доставка'])
            
            status = "🛒 POTENTIAL ORDER" if is_potential_order else "💬 Regular message"
            
            print(f"{i+1:2d}. [{msg_time.strftime('%Y-%m-%d %H:%M')}] {status}")
            print(f"    {msg_text}...")
            print()