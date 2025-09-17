#!/usr/bin/env python3
"""
Process messages from a specific date range
Since most messages are from February-August 2025, let's process those
"""

import json
import requests
from datetime import datetime, timedelta

from ..core.config import settings
from ..core.database import get_db, Order
from ..services.openai_service import parse_order

class DateRangeProcessor:
    def __init__(self):
        self.green_api_id = settings.GREEN_API_ID_INSTANCE
        self.green_api_token = settings.GREEN_API_TOKEN
        self.main_group_chat_id = settings.MAIN_GROUP_CHAT_ID
        self.base_url = f"https://api.green-api.com/waInstance{self.green_api_id}"

    def get_messages_in_date_range(self, start_date, end_date):
        """Get messages between two dates"""
        url = f"{self.base_url}/getChatHistory/{self.green_api_token}"
        
        payload = {
            "chatId": self.main_group_chat_id,
            "count": 1000
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code != 200:
                print(f"❌ Error: {response.text}")
                return []
            
            messages = response.json() or []
            print(f"📥 Retrieved {len(messages)} total messages from API")
            
            # Convert dates to timestamps
            start_timestamp = int(start_date.timestamp())
            end_timestamp = int(end_date.timestamp())
            
            print(f"📅 Filtering messages between:")
            print(f"   Start: {start_date} (timestamp: {start_timestamp})")
            print(f"   End: {end_date} (timestamp: {end_timestamp})")
            
            # Filter messages in date range
            filtered_messages = []
            for msg in messages:
                msg_timestamp = msg.get('timestamp', 0)
                if start_timestamp <= msg_timestamp <= end_timestamp:
                    filtered_messages.append(msg)
            
            print(f"🗓️  Found {len(filtered_messages)} messages in date range")
            
            # Show breakdown
            incoming_count = sum(1 for msg in filtered_messages if msg.get('type') == 'incoming')
            outgoing_count = sum(1 for msg in filtered_messages if msg.get('type') == 'outgoing')
            
            print(f"   📨 Incoming: {incoming_count}")
            print(f"   📤 Outgoing: {outgoing_count}")
            
            return filtered_messages
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return []

    def process_messages_in_range(self, start_date, end_date, max_messages=50):
        """Process messages in a specific date range"""
        print(f"🔄 PROCESSING MESSAGES FROM {start_date.strftime('%Y-%m-%d')} TO {end_date.strftime('%Y-%m-%d')}")
        print("=" * 80)
        
        messages = self.get_messages_in_date_range(start_date, end_date)
        
        if not messages:
            print("❌ No messages found in date range")
            return
        
        # Filter messages with text
        processable_messages = [msg for msg in messages if msg.get('textMessage', '').strip()]
        
        print(f"📝 {len(processable_messages)} messages have text content")
        
        if len(processable_messages) > max_messages:
            print(f"⚠️  Limiting to first {max_messages} messages for testing")
            processable_messages = processable_messages[:max_messages]
        
        # Process messages
        db = next(get_db())
        
        try:
            processed_count = 0
            order_count = 0
            skipped_count = 0
            
            print(f"\n🔄 Processing {len(processable_messages)} messages...")
            print("-" * 50)
            
            for i, msg in enumerate(processable_messages):
                try:
                    msg_id = msg.get('idMessage')
                    msg_text = msg.get('textMessage', '').strip()
                    timestamp = msg.get('timestamp', 0)
                    msg_time = datetime.fromtimestamp(timestamp) if timestamp else 'Unknown'
                    msg_type = msg.get('type', 'unknown')
                    
                    # Progress
                    if i % 5 == 0:
                        print(f"📋 Progress: {i+1}/{len(processable_messages)}")
                    
                    print(f"[{i+1}] {msg_time} ({msg_type}): {msg_text[:60]}...")
                    
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
                    print("   🤖 Parsing...")
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
                        print(f"   ✅ ORDER #{order_count}: {customer} - {order_date}")
                    else:
                        print("   📝 Non-order message")
                    
                    processed_count += 1
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    continue
            
            print(f"\n🎉 PROCESSING COMPLETE!")
            print(f"   📥 Processed: {processed_count}")
            print(f"   🛒 Orders found: {order_count}")
            print(f"   ⏭️  Skipped: {skipped_count}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.rollback()
        finally:
            db.close()

    def suggest_date_ranges(self):
        """Suggest good date ranges based on your data"""
        print("💡 SUGGESTED DATE RANGES TO PROCESS")
        print("=" * 50)
        
        # Based on your terminal output: 2025-02-14 to 2025-08-31
        
        suggestions = [
            ("Recent (last 6 months)", datetime(2025, 3, 1), datetime(2025, 8, 31)),
            ("Spring 2025", datetime(2025, 3, 1), datetime(2025, 5, 31)),
            ("Summer 2025", datetime(2025, 6, 1), datetime(2025, 8, 31)),
            ("All available", datetime(2025, 2, 14), datetime(2025, 8, 31)),
        ]
        
        for name, start, end in suggestions:
            print(f"\n📅 {name}:")
            print(f"   From: {start.strftime('%Y-%m-%d')}")
            print(f"   To: {end.strftime('%Y-%m-%d')}")
            print(f"   Command: python process_date_range.py '{start.strftime('%Y-%m-%d')}' '{end.strftime('%Y-%m-%d')}'")