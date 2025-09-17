#!/usr/bin/env python3
"""
Super simple test to understand message retrieval
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

GREEN_API_ID_INSTANCE = os.getenv("GREEN_API_ID_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN") 
MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")

def simple_test():
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/getChatHistory/{GREEN_API_TOKEN}"
    
    payload = {
        "chatId": MAIN_GROUP_CHAT_ID,
        "count": 100
    }
    
    print("🔍 SIMPLE MESSAGE TEST")
    print("=" * 40)
    
    try:
        response = requests.post(url, json=payload)
        messages = response.json() or []
        
        print(f"📥 Total messages: {len(messages)}")
        
        # Count by type
        incoming_count = 0
        outgoing_count = 0
        
        for msg in messages:
            msg_type = msg.get('type', '')
            if msg_type == 'incoming':
                incoming_count += 1
            elif msg_type == 'outgoing':
                outgoing_count += 1
        
        print(f"📨 Incoming: {incoming_count}")
        print(f"📤 Outgoing: {outgoing_count}")
        
        # Show first 10 messages with dates
        print(f"\n📋 FIRST 10 MESSAGES:")
        print("-" * 40)
        
        for i, msg in enumerate(messages[:10]):
            timestamp = msg.get('timestamp', 0)
            if timestamp:
                dt = datetime.fromtimestamp(timestamp)
                date_str = dt.strftime('%Y-%m-%d %H:%M')
            else:
                date_str = 'No timestamp'
            
            msg_type = msg.get('type', 'unknown')
            text = msg.get('textMessage', '')[:50]
            
            print(f"{i+1}. {date_str} ({msg_type}): {text}...")
        
        # Test filtering for last 180 days
        print(f"\n🗓️  TESTING 180 DAYS FILTER:")
        cutoff = datetime.now() - timedelta(days=180)
        cutoff_ts = int(cutoff.timestamp())
        
        print(f"Cutoff date: {cutoff}")
        print(f"Cutoff timestamp: {cutoff_ts}")
        
        filtered = []
        for msg in messages:
            msg_ts = msg.get('timestamp', 0)
            if msg_ts >= cutoff_ts:
                filtered.append(msg)
        
        print(f"Messages after filter: {len(filtered)}")
        
        # Show filtered messages
        for i, msg in enumerate(filtered[:5]):
            timestamp = msg.get('timestamp', 0)
            dt = datetime.fromtimestamp(timestamp) if timestamp else None
            msg_type = msg.get('type', 'unknown')
            text = msg.get('textMessage', '')[:30]
            
            print(f"  {i+1}. {dt} ({msg_type}): {text}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    simple_test()
