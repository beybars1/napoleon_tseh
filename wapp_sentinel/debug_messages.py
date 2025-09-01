#!/usr/bin/env python3
"""
Debug script to investigate message retrieval issues
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

def debug_message_retrieval():
    """Debug what messages we can actually retrieve"""
    print("🔍 DEBUGGING MESSAGE RETRIEVAL")
    print("=" * 50)
    
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/getChatHistory/{GREEN_API_TOKEN}"
    
    print(f"📡 API URL: {url}")
    print(f"💬 Chat ID: {MAIN_GROUP_CHAT_ID}")
    
    # Test different count values
    for count in [50, 100, 500, 1000]:
        print(f"\n📊 Testing with count={count}")
        print("-" * 30)
        
        payload = {
            "chatId": MAIN_GROUP_CHAT_ID,
            "count": count
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code} - {response.text}")
                continue
            
            messages = response.json() or []
            print(f"📥 Retrieved {len(messages)} total messages")
            
            if not messages:
                print("❌ No messages retrieved!")
                continue
            
            # Analyze timestamps
            timestamps = [msg.get('timestamp', 0) for msg in messages if msg.get('timestamp')]
            if timestamps:
                oldest_ts = min(timestamps)
                newest_ts = max(timestamps)
                oldest_date = datetime.fromtimestamp(oldest_ts)
                newest_date = datetime.fromtimestamp(newest_ts)
                
                print(f"📅 Date range:")
                print(f"   Oldest: {oldest_date}")
                print(f"   Newest: {newest_date}")
                print(f"   Span: {(newest_date - oldest_date).days} days")
            
            # Analyze message types
            incoming = sum(1 for msg in messages if msg.get('type') == 'incoming')
            outgoing = sum(1 for msg in messages if msg.get('type') == 'outgoing')
            
            print(f"📨 Message types:")
            print(f"   Incoming: {incoming}")
            print(f"   Outgoing: {outgoing}")
            
            # Show last 7 days filtering
            seven_days_ago = datetime.now() - timedelta(days=7)
            seven_days_timestamp = int(seven_days_ago.timestamp())
            
            recent_messages = [
                msg for msg in messages 
                if msg.get('timestamp', 0) >= seven_days_timestamp
            ]
            
            print(f"🗓️  Messages from last 7 days: {len(recent_messages)}")
            print(f"   Cut-off date: {seven_days_ago}")
            
            # Show sample messages
            print(f"\n📝 Sample messages (first 5):")
            for i, msg in enumerate(messages[:5]):
                timestamp = msg.get('timestamp', 0)
                msg_time = datetime.fromtimestamp(timestamp) if timestamp else 'Unknown'
                msg_type = msg.get('type', 'unknown')
                msg_text = msg.get('textMessage', '')[:50]
                
                print(f"   {i+1}. [{msg_time}] {msg_type}: {msg_text}...")
            
            # Stop at first successful retrieval for detailed analysis
            if messages:
                break
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_different_timeframes():
    """Test different timeframes to see what's available"""
    print("\n🕐 TESTING DIFFERENT TIMEFRAMES")
    print("=" * 50)
    
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/getChatHistory/{GREEN_API_TOKEN}"
    
    payload = {
        "chatId": MAIN_GROUP_CHAT_ID,
        "count": 1000  # Maximum
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return
        
        messages = response.json() or []
        print(f"📥 Retrieved {len(messages)} total messages")
        
        if not messages:
            print("❌ No messages to analyze!")
            return
        
        # Test different timeframes
        timeframes = [1, 3, 7, 14, 30]
        
        for days in timeframes:
            cutoff_time = datetime.now() - timedelta(days=days)
            cutoff_timestamp = int(cutoff_time.timestamp())
            
            filtered_messages = [
                msg for msg in messages 
                if msg.get('timestamp', 0) >= cutoff_timestamp
            ]
            
            incoming_count = sum(1 for msg in filtered_messages if msg.get('type') == 'incoming')
            outgoing_count = sum(1 for msg in filtered_messages if msg.get('type') == 'outgoing')
            
            print(f"📅 Last {days} days (since {cutoff_time.strftime('%Y-%m-%d')}):")
            print(f"   Total: {len(filtered_messages)} messages")
            print(f"   Incoming: {incoming_count}, Outgoing: {outgoing_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def check_api_settings():
    """Check GreenAPI settings that might affect message history"""
    print("\n⚙️ CHECKING API SETTINGS")
    print("=" * 50)
    
    settings_url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/getSettings/{GREEN_API_TOKEN}"
    
    try:
        response = requests.get(settings_url)
        if response.status_code == 200:
            settings = response.json()
            print("📋 Current GreenAPI settings:")
            
            relevant_settings = [
                'incomingWebhook',
                'outgoingWebhook', 
                'enableMessagesHistory',
                'keepOnlineStatus',
                'pollMessageWebhook'
            ]
            
            for setting in relevant_settings:
                value = settings.get(setting, 'Not found')
                print(f"   {setting}: {value}")
                
        else:
            print(f"❌ Error getting settings: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_message_retrieval()
    test_different_timeframes()
    check_api_settings()
    
    print("\n💡 RECOMMENDATIONS:")
    print("1. If you see very few messages, the chat history might be limited")
    print("2. Check if 'enableMessagesHistory' is enabled in your GreenAPI settings")
    print("3. Try with different count values or use pagination")
    print("4. Consider using real-time webhook notifications instead")
