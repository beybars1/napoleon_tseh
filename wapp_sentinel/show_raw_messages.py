#!/usr/bin/env python3
"""
Simple script to show raw message data without any filtering
This will help us see exactly what we're getting from the API
"""

import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

GREEN_API_ID_INSTANCE = os.getenv("GREEN_API_ID_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")
BASE_URL = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}"

def show_raw_messages(count=50):
    """Show raw messages without any filtering"""
    print(f"📥 SHOWING {count} RAW MESSAGES")
    print("=" * 60)
    
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    payload = {
        "chatId": MAIN_GROUP_CHAT_ID,
        "count": count
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return
        
        messages = response.json() or []
        print(f"Retrieved {len(messages)} messages")
        
        # Count by type
        incoming = sum(1 for msg in messages if msg.get('type') == 'incoming')
        outgoing = sum(1 for msg in messages if msg.get('type') == 'outgoing')
        
        print(f"📊 Message types:")
        print(f"   📨 Incoming: {incoming}")
        print(f"   📤 Outgoing: {outgoing}")
        print(f"   📋 Total: {len(messages)}")
        
        # Show first 20 messages
        print(f"\n📝 FIRST 20 MESSAGES (newest to oldest):")
        print("-" * 80)
        
        for i, msg in enumerate(messages[:20]):
            timestamp = msg.get('timestamp', 0)
            msg_time = datetime.fromtimestamp(timestamp) if timestamp else 'No timestamp'
            msg_type = msg.get('type', 'unknown')
            msg_text = msg.get('textMessage', '').strip()
            
            if len(msg_text) > 80:
                msg_text = msg_text[:80] + "..."
            
            print(f"{i+1:2d}. 🕐 {msg_time}")
            print(f"    📱 Type: {msg_type}")
            print(f"    💬 Text: {msg_text}")
            print(f"    🔢 Raw timestamp: {timestamp}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")

def show_date_distribution():
    """Show distribution of messages by date"""
    print(f"\n📅 MESSAGE DISTRIBUTION BY DATE")
    print("=" * 60)
    
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    payload = {
        "chatId": MAIN_GROUP_CHAT_ID,
        "count": 1000
    }
    
    try:
        response = requests.post(url, json=payload)
        messages = response.json() or []
        
        # Group by date
        date_counts = {}
        
        for msg in messages:
            timestamp = msg.get('timestamp', 0)
            if timestamp:
                dt = datetime.fromtimestamp(timestamp)
                date_str = dt.strftime('%Y-%m-%d')
                
                if date_str not in date_counts:
                    date_counts[date_str] = {'incoming': 0, 'outgoing': 0, 'total': 0}
                
                msg_type = msg.get('type', 'unknown')
                if msg_type == 'incoming':
                    date_counts[date_str]['incoming'] += 1
                elif msg_type == 'outgoing':
                    date_counts[date_str]['outgoing'] += 1
                
                date_counts[date_str]['total'] += 1
        
        # Sort by date
        sorted_dates = sorted(date_counts.keys(), reverse=True)
        
        print(f"📊 Messages by date (last 30 days):")
        print("Date       | Total | In  | Out")
        print("-" * 30)
        
        for date_str in sorted_dates[:30]:  # Show last 30 days
            counts = date_counts[date_str]
            print(f"{date_str} | {counts['total']:5d} | {counts['incoming']:3d} | {counts['outgoing']:3d}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_timeframe_logic():
    """Test our exact timeframe logic"""
    print(f"\n🧪 TESTING TIMEFRAME LOGIC")
    print("=" * 60)
    
    now = datetime.now()
    print(f"Current time: {now}")
    
    # Test different timeframes
    for days in [1, 7, 30, 60, 90]:
        cutoff_time = now - timedelta(days=days)
        cutoff_timestamp = int(cutoff_time.timestamp())
        
        print(f"\n📅 Last {days} days:")
        print(f"   Cutoff date: {cutoff_time}")
        print(f"   Cutoff timestamp: {cutoff_timestamp}")
        
        # Get messages and filter
        url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
        payload = {"chatId": MAIN_GROUP_CHAT_ID, "count": 1000}
        
        try:
            response = requests.post(url, json=payload)
            messages = response.json() or []
            
            # Apply filtering
            filtered = [
                msg for msg in messages 
                if msg.get('timestamp', 0) >= cutoff_timestamp
            ]
            
            # Count types
            incoming = sum(1 for msg in filtered if msg.get('type') == 'incoming')
            outgoing = sum(1 for msg in filtered if msg.get('type') == 'outgoing')
            
            print(f"   📊 Found: {len(filtered)} total | 📨 {incoming} in | 📤 {outgoing} out")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
            show_raw_messages(count)
        except ValueError:
            print("Usage: python show_raw_messages.py [count]")
    else:
        # Run all tests
        show_raw_messages(50)
        show_date_distribution()
        test_timeframe_logic()
