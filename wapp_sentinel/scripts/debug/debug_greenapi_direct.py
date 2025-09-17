#!/usr/bin/env python3
"""
Direct GreenAPI testing script to debug outgoing message retrieval
This script tests the GreenAPI endpoints directly without FastAPI
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GREEN_API_ID_INSTANCE = os.getenv("GREEN_API_ID_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")

BASE_URL = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}"

def test_greenapi_settings():
    """Check current GreenAPI settings"""
    print("🔧 TESTING GREENAPI SETTINGS")
    print("=" * 50)
    
    url = f"{BASE_URL}/getSettings/{GREEN_API_TOKEN}"
    
    try:
        response = requests.get(url)
        print(f"Settings request status: {response.status_code}")
        
        if response.status_code == 200:
            settings = response.json()
            print("✅ Current GreenAPI Settings:")
            print(json.dumps(settings, indent=2))
            
            # Check important settings for outgoing messages
            important_settings = [
                'incomingWebhook',
                'outgoingWebhook', 
                'outgoingMessageWebhook',
                'outgoingAPIMessageWebhook',
                'stateWebhook'
            ]
            
            print("\n📋 Important settings for message retrieval:")
            for setting in important_settings:
                if setting in settings:
                    print(f"   {setting}: {settings[setting]}")
                else:
                    print(f"   {setting}: NOT FOUND")
                    
        else:
            print(f"❌ Error getting settings: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception getting settings: {e}")

def test_outgoing_messages_endpoint():
    """Test the lastOutgoingMessages endpoint directly"""
    print("\n📤 TESTING LAST OUTGOING MESSAGES ENDPOINT")
    print("=" * 50)
    
    # Test different URL variations
    endpoints_to_test = [
        f"{BASE_URL}/lastOutgoingMessages/{GREEN_API_TOKEN}",
        f"{BASE_URL}/LastOutgoingMessages/{GREEN_API_TOKEN}",
        f"{BASE_URL}/getLastOutgoingMessages/{GREEN_API_TOKEN}"
    ]
    
    for i, url in enumerate(endpoints_to_test, 1):
        print(f"\n{i}. Testing URL: {url}")
        
        try:
            # Test with GET method
            print("   Trying GET method...")
            response = requests.get(url, params={"minutes": 1440})  # 24 hours
            print(f"   GET Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ GET Success! Found {len(data) if isinstance(data, list) else 'unknown'} items")
                if isinstance(data, list) and len(data) > 0:
                    print(f"   Sample item: {json.dumps(data[0], indent=2)}")
                elif isinstance(data, dict):
                    print(f"   Response: {json.dumps(data, indent=2)}")
                return data
            else:
                print(f"   ❌ GET Failed: {response.text}")
            
            # Test with POST method
            print("   Trying POST method...")
            response = requests.post(url, json={"minutes": 1440})
            print(f"   POST Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ POST Success! Found {len(data) if isinstance(data, list) else 'unknown'} items")
                if isinstance(data, list) and len(data) > 0:
                    print(f"   Sample item: {json.dumps(data[0], indent=2)}")
                return data
            else:
                print(f"   ❌ POST Failed: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n❌ All outgoing message endpoints failed!")
    return None

def test_chat_history_for_outgoing():
    """Test if getChatHistory includes outgoing messages"""
    print("\n📥 TESTING CHAT HISTORY FOR OUTGOING MESSAGES")
    print("=" * 50)
    
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    
    payload = {
        "chatId": MAIN_GROUP_CHAT_ID,
        "count": 100
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Chat history status: {response.status_code}")
        
        if response.status_code == 200:
            messages = response.json() or []
            print(f"Total messages from chat history: {len(messages)}")
            
            # Analyze message types
            incoming_count = sum(1 for msg in messages if msg.get('type') == 'incoming')
            outgoing_count = sum(1 for msg in messages if msg.get('type') == 'outgoing')
            other_types = {}
            
            for msg in messages:
                msg_type = msg.get('type', 'unknown')
                if msg_type not in ['incoming', 'outgoing']:
                    other_types[msg_type] = other_types.get(msg_type, 0) + 1
            
            print(f"📊 Message breakdown from getChatHistory:")
            print(f"   📨 Incoming: {incoming_count}")
            print(f"   📤 Outgoing: {outgoing_count}")
            if other_types:
                print(f"   🔍 Other types: {other_types}")
            
            # Show sample messages
            print(f"\n📋 Sample messages (first 5):")
            for i, msg in enumerate(messages[:5]):
                msg_type = msg.get('type', 'unknown')
                timestamp = msg.get('timestamp', 0)
                msg_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else 'Unknown'
                text = msg.get('textMessage', '')[:50] + "..." if len(msg.get('textMessage', '')) > 50 else msg.get('textMessage', '')
                sender = msg.get('senderData', {}).get('sender', 'Unknown')
                
                print(f"   {i+1}. [{msg_time}] {msg_type} from {sender}: {text}")
            
            return messages
        else:
            print(f"❌ Error getting chat history: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception getting chat history: {e}")
    
    return []

def test_account_info():
    """Get account information"""
    print("\n🔍 TESTING ACCOUNT INFO")
    print("=" * 50)
    
    url = f"{BASE_URL}/getStateInstance/{GREEN_API_TOKEN}"
    
    try:
        response = requests.get(url)
        print(f"Account info status: {response.status_code}")
        
        if response.status_code == 200:
            info = response.json()
            print(f"✅ Account info: {json.dumps(info, indent=2)}")
        else:
            print(f"❌ Error getting account info: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception getting account info: {e}")

def enable_outgoing_webhooks():
    """Try to enable outgoing message webhooks"""
    print("\n⚙️ TRYING TO ENABLE OUTGOING MESSAGE WEBHOOKS")
    print("=" * 50)
    
    url = f"{BASE_URL}/setSettings/{GREEN_API_TOKEN}"
    
    settings = {
        "outgoingWebhook": "yes",
        "outgoingMessageWebhook": "yes", 
        "outgoingAPIMessageWebhook": "yes",
        "incomingWebhook": "yes"
    }
    
    try:
        response = requests.post(url, json=settings)
        print(f"Set settings status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Settings updated: {json.dumps(result, indent=2)}")
            print("⏰ Note: Settings may take up to 5 minutes to take effect")
        else:
            print(f"❌ Error setting webhooks: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception setting webhooks: {e}")

def main():
    """Main diagnostic function"""
    print("🚀 GREENAPI OUTGOING MESSAGES DIAGNOSTIC")
    print("=" * 60)
    
    # Check environment variables
    if not GREEN_API_ID_INSTANCE or not GREEN_API_TOKEN:
        print("❌ Missing GreenAPI credentials!")
        print("   GREEN_API_ID_INSTANCE:", GREEN_API_ID_INSTANCE)
        print("   GREEN_API_TOKEN:", "Set" if GREEN_API_TOKEN else "Missing")
        return
    
    if not MAIN_GROUP_CHAT_ID:
        print("❌ Missing MAIN_GROUP_CHAT_ID!")
        return
    
    print(f"✅ Environment check passed")
    print(f"   Instance ID: {GREEN_API_ID_INSTANCE}")
    print(f"   Chat ID: {MAIN_GROUP_CHAT_ID}")
    print(f"   Base URL: {BASE_URL}")
    
    # Run all tests
    test_account_info()
    test_greenapi_settings()
    
    # Try to enable webhooks first
    enable_outgoing_webhooks()
    
    # Test endpoints
    outgoing_data = test_outgoing_messages_endpoint()
    chat_history_data = test_chat_history_for_outgoing()
    
    # Summary
    print("\n📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    if outgoing_data:
        print("✅ Outgoing messages endpoint working")
    else:
        print("❌ Outgoing messages endpoint not working")
    
    if chat_history_data:
        outgoing_in_history = sum(1 for msg in chat_history_data if msg.get('type') == 'outgoing')
        if outgoing_in_history > 0:
            print(f"✅ Found {outgoing_in_history} outgoing messages in chat history")
        else:
            print("❌ No outgoing messages found in chat history")
    
    print("\n💡 RECOMMENDATIONS:")
    if not outgoing_data and not any(msg.get('type') == 'outgoing' for msg in chat_history_data):
        print("1. Check if you've sent any messages from your WhatsApp recently")
        print("2. Verify GreenAPI webhook settings are enabled (use setSettings)")
        print("3. Wait 5 minutes after enabling settings")
        print("4. Make sure you're using the correct chat ID")
        print("5. Check if your GreenAPI plan supports outgoing message retrieval")

if __name__ == "__main__":
    main()
