#!/usr/bin/env python3
"""
Debug script to analyze message timestamps and filtering logic
This will help us understand why we're not getting the expected number of messages
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

def test_raw_message_retrieval():
    """Test raw message retrieval from API"""
    print("🔍 TESTING RAW MESSAGE RETRIEVAL")
    print("=" * 60)
    
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    
    payload = {
        "chatId": MAIN_GROUP_CHAT_ID,
        "count": 1000
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return None
        
        messages = response.json() or []
        print(f"📥 Retrieved {len(messages)} total messages")
        
        if not messages:
            print("❌ No messages retrieved!")
            return None
        
        # Analyze message structure
        print(f"\n📋 MESSAGE STRUCTURE ANALYSIS:")
        sample_msg = messages[0]
        print(f"Sample message keys: {list(sample_msg.keys())}")
        print(f"Sample message: {json.dumps(sample_msg, indent=2, ensure_ascii=False)[:500]}...")
        
        return messages
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def analyze_timestamps(messages):
    """Analyze timestamps in detail"""
    print(f"\n📅 TIMESTAMP ANALYSIS")
    print("=" * 60)
    
    # Extract all timestamps
    timestamps = []
    for i, msg in enumerate(messages):
        timestamp = msg.get('timestamp', 0)
        msg_type = msg.get('type', 'unknown')
        msg_text = msg.get('textMessage', '')[:50]
        
        if timestamp:
            dt = datetime.fromtimestamp(timestamp)
            timestamps.append({
                'index': i,
                'timestamp': timestamp,
                'datetime': dt,
                'type': msg_type,
                'text': msg_text
            })
    
    # Sort by timestamp
    timestamps.sort(key=lambda x: x['timestamp'])
    
    print(f"📊 Found {len(timestamps)} messages with timestamps")
    
    if timestamps:
        oldest = timestamps[0]
        newest = timestamps[-1]
        
        print(f"🕐 Oldest message:")
        print(f"   Date: {oldest['datetime']}")
        print(f"   Type: {oldest['type']}")
        print(f"   Text: {oldest['text']}")
        print(f"   Raw timestamp: {oldest['timestamp']}")
        
        print(f"\n🕐 Newest message:")
        print(f"   Date: {newest['datetime']}")
        print(f"   Type: {newest['type']}")
        print(f"   Text: {newest['text']}")
        print(f"   Raw timestamp: {newest['timestamp']}")
        
        span_days = (newest['datetime'] - oldest['datetime']).days
        print(f"\n📏 Total span: {span_days} days")
    
    return timestamps

def test_timeframe_filtering(timestamps):
    """Test different timeframe filtering"""
    print(f"\n🗓️  TIMEFRAME FILTERING TEST")
    print("=" * 60)
    
    now = datetime.now()
    print(f"Current time: {now}")
    print(f"Current timestamp: {int(now.timestamp())}")
    
    timeframes = [1, 3, 7, 14, 30, 60, 90, 180, 365]
    
    for days in timeframes:
        cutoff_time = now - timedelta(days=days)
        cutoff_timestamp = int(cutoff_time.timestamp())
        
        print(f"\n📅 Testing last {days} days:")
        print(f"   Cutoff date: {cutoff_time}")
        print(f"   Cutoff timestamp: {cutoff_timestamp}")
        
        # Filter messages
        filtered = [t for t in timestamps if t['timestamp'] >= cutoff_timestamp]
        
        incoming_count = sum(1 for t in filtered if t['type'] == 'incoming')
        outgoing_count = sum(1 for t in filtered if t['type'] == 'outgoing')
        
        print(f"   📊 Found: {len(filtered)} total | 📨 {incoming_count} in | 📤 {outgoing_count} out")
        
        # Show sample messages in this timeframe
        if filtered and len(filtered) <= 10:
            print(f"   📝 Messages in this timeframe:")
            for t in filtered[:5]:  # Show first 5
                print(f"      {t['datetime'].strftime('%Y-%m-%d %H:%M')} ({t['type']}): {t['text'][:30]}...")

def test_specific_timeframes():
    """Test specific timeframes that should have messages"""
    print(f"\n🎯 TESTING SPECIFIC TIMEFRAMES")
    print("=" * 60)
    
    # Get raw messages first
    messages = test_raw_message_retrieval()
    if not messages:
        return
    
    # Analyze timestamps
    timestamps = analyze_timestamps(messages)
    if not timestamps:
        return
    
    # Test filtering
    test_timeframe_filtering(timestamps)
    
    # Additional specific tests
    print(f"\n🔬 ADDITIONAL TESTS:")
    
    # Test last 6 months
    six_months_ago = datetime.now() - timedelta(days=180)
    six_months_timestamp = int(six_months_ago.timestamp())
    
    recent_messages = [t for t in timestamps if t['timestamp'] >= six_months_timestamp]
    
    print(f"📊 Messages from last 6 months: {len(recent_messages)}")
    
    if recent_messages:
        print(f"Sample recent messages:")
        for t in recent_messages[:10]:
            print(f"   {t['datetime'].strftime('%Y-%m-%d %H:%M')} ({t['type']}): {t['text'][:50]}...")

def verify_our_filtering_logic():
    """Verify our current filtering logic matches what we expect"""
    print(f"\n🧪 VERIFYING OUR FILTERING LOGIC")
    print("=" * 60)
    
    # Simulate our current filtering
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    payload = {"chatId": MAIN_GROUP_CHAT_ID, "count": 1000}
    
    try:
        response = requests.post(url, json=payload)
        messages = response.json() or []
        
        print(f"📥 Retrieved {len(messages)} messages")
        
        # Test 60 days filtering (like your command)
        days_back = 60
        cutoff_time = datetime.now() - timedelta(days=days_back)
        cutoff_timestamp = int(cutoff_time.timestamp())
        
        print(f"\n🗓️  Testing 60 days filter:")
        print(f"   Current time: {datetime.now()}")
        print(f"   Cutoff time: {cutoff_time}")
        print(f"   Cutoff timestamp: {cutoff_timestamp}")
        
        # Apply the same filtering logic as our script
        filtered_messages = [
            msg for msg in messages 
            if msg.get('timestamp', 0) >= cutoff_timestamp
        ]
        
        print(f"   📊 Filtered messages: {len(filtered_messages)}")
        
        # Show details of filtered messages
        for i, msg in enumerate(filtered_messages[:10]):
            timestamp = msg.get('timestamp', 0)
            msg_time = datetime.fromtimestamp(timestamp) if timestamp else 'Unknown'
            msg_type = msg.get('type', 'unknown')
            msg_text = msg.get('textMessage', '')[:50]
            
            print(f"   {i+1}. {msg_time} ({msg_type}): {msg_text}...")
        
        # Check messages with text
        messages_with_text = [msg for msg in filtered_messages if msg.get('textMessage', '').strip()]
        print(f"   📝 Messages with text: {len(messages_with_text)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 MESSAGE RETRIEVAL DEBUG SCRIPT")
    print("=" * 70)
    
    # Run all tests
    test_specific_timeframes()
    print("\n" + "="*70)
    verify_our_filtering_logic()
    
    print(f"\n💡 DEBUGGING SUMMARY:")
    print("1. Check if timestamps are in the expected format")
    print("2. Verify timezone issues (UTC vs local time)")
    print("3. Check if filtering logic matches message dates")
    print("4. Look for messages with empty text that get filtered out")
