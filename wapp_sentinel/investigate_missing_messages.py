#!/usr/bin/env python3
"""
Investigate why messages from June-August 2025 are missing
This script will help identify if it's an API limitation, pagination issue, or other problem
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

def test_different_count_values():
    """Test retrieving different numbers of messages"""
    print("🔍 TESTING DIFFERENT MESSAGE COUNTS")
    print("=" * 60)
    
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    
    # Test different count values
    test_counts = [50, 100, 200, 500, 1000, 1500, 2000]
    
    for count in test_counts:
        print(f"\n📊 Testing count={count}:")
        
        payload = {
            "chatId": MAIN_GROUP_CHAT_ID,
            "count": count
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code != 200:
                print(f"   ❌ Error: {response.text}")
                continue
            
            messages = response.json() or []
            print(f"   📥 Retrieved: {len(messages)} messages")
            
            if messages:
                # Check date range
                timestamps = [msg.get('timestamp', 0) for msg in messages if msg.get('timestamp')]
                if timestamps:
                    oldest_ts = min(timestamps)
                    newest_ts = max(timestamps)
                    oldest_date = datetime.fromtimestamp(oldest_ts)
                    newest_date = datetime.fromtimestamp(newest_ts)
                    
                    print(f"   📅 Date range:")
                    print(f"      Oldest: {oldest_date}")
                    print(f"      Newest: {newest_date}")
                    print(f"      Span: {(newest_date - oldest_date).days} days")
                    
                    # Check for June-August 2025 messages
                    june_start = datetime(2025, 6, 1).timestamp()
                    aug_end = datetime(2025, 8, 31, 23, 59, 59).timestamp()
                    
                    summer_messages = [
                        msg for msg in messages 
                        if june_start <= msg.get('timestamp', 0) <= aug_end
                    ]
                    
                    print(f"   🌞 June-August 2025 messages: {len(summer_messages)}")
                    
                    if summer_messages:
                        print(f"      Found summer messages! Showing first 3:")
                        for i, msg in enumerate(summer_messages[:3]):
                            ts = msg.get('timestamp', 0)
                            dt = datetime.fromtimestamp(ts)
                            text = msg.get('textMessage', '')[:50]
                            print(f"         {dt}: {text}...")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_pagination_with_offset():
    """Test if GreenAPI supports pagination or offset"""
    print(f"\n🔄 TESTING PAGINATION/OFFSET")
    print("=" * 60)
    
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    
    # Try different payload structures
    test_payloads = [
        # Standard request
        {"chatId": MAIN_GROUP_CHAT_ID, "count": 100},
        
        # Try with offset (if supported)
        {"chatId": MAIN_GROUP_CHAT_ID, "count": 100, "offset": 100},
        
        # Try with lastMessageId (if supported)  
        {"chatId": MAIN_GROUP_CHAT_ID, "count": 100, "lastMessageId": ""},
        
        # Try requesting from specific date
        {"chatId": MAIN_GROUP_CHAT_ID, "count": 100, "fromTimestamp": int(datetime(2025, 6, 1).timestamp())},
    ]
    
    for i, payload in enumerate(test_payloads):
        print(f"\n📊 Test {i+1}: {payload}")
        
        try:
            response = requests.post(url, json=payload)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                messages = response.json() or []
                print(f"   📥 Retrieved: {len(messages)} messages")
                
                if messages:
                    # Show first message
                    first_msg = messages[0]
                    ts = first_msg.get('timestamp', 0)
                    dt = datetime.fromtimestamp(ts) if ts else 'No timestamp'
                    print(f"   🕐 First message: {dt}")
            else:
                print(f"   ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def analyze_message_gaps():
    """Analyze gaps in message timeline"""
    print(f"\n🕳️  ANALYZING MESSAGE GAPS")
    print("=" * 60)
    
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    payload = {"chatId": MAIN_GROUP_CHAT_ID, "count": 1000}
    
    try:
        response = requests.post(url, json=payload)
        messages = response.json() or []
        
        print(f"📥 Analyzing {len(messages)} messages for gaps...")
        
        # Extract and sort timestamps
        timestamped_messages = [
            {
                'timestamp': msg.get('timestamp', 0),
                'datetime': datetime.fromtimestamp(msg.get('timestamp', 0)) if msg.get('timestamp') else None,
                'type': msg.get('type', 'unknown'),
                'text': msg.get('textMessage', '')[:50]
            }
            for msg in messages if msg.get('timestamp')
        ]
        
        # Sort by timestamp
        timestamped_messages.sort(key=lambda x: x['timestamp'])
        
        print(f"📊 Found {len(timestamped_messages)} messages with timestamps")
        
        # Look for gaps > 1 day
        print(f"\n🕳️  GAPS > 24 HOURS:")
        
        for i in range(1, len(timestamped_messages)):
            prev_msg = timestamped_messages[i-1]
            curr_msg = timestamped_messages[i]
            
            if prev_msg['datetime'] and curr_msg['datetime']:
                gap = curr_msg['datetime'] - prev_msg['datetime']
                
                if gap.days > 1:
                    print(f"\n⚠️  GAP FOUND:")
                    print(f"   From: {prev_msg['datetime']} ({prev_msg['type']})")
                    print(f"   To: {curr_msg['datetime']} ({curr_msg['type']})")
                    print(f"   Gap: {gap.days} days, {gap.seconds//3600} hours")
                    print(f"   Last message before gap: {prev_msg['text']}...")
                    print(f"   First message after gap: {curr_msg['text']}...")
        
        # Monthly distribution
        print(f"\n📅 MONTHLY MESSAGE DISTRIBUTION:")
        monthly_counts = {}
        
        for msg in timestamped_messages:
            if msg['datetime']:
                month_key = msg['datetime'].strftime('%Y-%m')
                if month_key not in monthly_counts:
                    monthly_counts[month_key] = 0
                monthly_counts[month_key] += 1
        
        for month in sorted(monthly_counts.keys()):
            print(f"   {month}: {monthly_counts[month]} messages")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def check_api_settings():
    """Check GreenAPI settings for message history limits"""
    print(f"\n⚙️  CHECKING API SETTINGS")
    print("=" * 60)
    
    settings_url = f"{BASE_URL}/getSettings/{GREEN_API_TOKEN}"
    
    try:
        response = requests.get(settings_url)
        if response.status_code == 200:
            settings = response.json()
            
            print("📋 GreenAPI Settings:")
            relevant_settings = [
                'enableMessagesHistory',
                'incomingWebhook',
                'outgoingWebhook',
                'keepOnlineStatus',
                'pollMessageWebhook',
                'enableMessagesHistoryPeriod'
            ]
            
            for setting in relevant_settings:
                value = settings.get(setting, 'Not found')
                print(f"   {setting}: {value}")
            
            # Check if there are any limits mentioned
            print(f"\n📋 All settings:")
            for key, value in settings.items():
                if 'history' in key.lower() or 'message' in key.lower() or 'limit' in key.lower():
                    print(f"   {key}: {value}")
        else:
            print(f"❌ Error getting settings: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 INVESTIGATING MISSING MESSAGES")
    print("=" * 70)
    
    # Run all investigations
    test_different_count_values()
    test_pagination_with_offset()
    analyze_message_gaps()
    check_api_settings()
    
    print(f"\n💡 POSSIBLE CAUSES FOR MISSING MESSAGES:")
    print("1. GreenAPI message history limit (only stores X days/messages)")
    print("2. Pagination needed - API only returns first/last N messages")
    print("3. Messages were deleted from WhatsApp")
    print("4. API settings limit message history retrieval")
    print("5. Rate limiting or API access restrictions")
    print("6. Messages are in different chat or group")
