#!/usr/bin/env python3
"""
Systematic GreenAPI Testing Script
Tests all possible methods to retrieve outgoing messages
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

GREEN_API_ID_INSTANCE = os.getenv("GREEN_API_ID_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")

BASE_URL = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}"

def test_1_basic_getchathistory():
    """Test 1: Basic getChatHistory - current implementation"""
    print("🧪 TEST 1: Basic getChatHistory")
    print("-" * 40)
    
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    
    test_cases = [
        {"chatId": MAIN_GROUP_CHAT_ID, "count": 100},
        {"chatId": MAIN_GROUP_CHAT_ID, "count": 50},
        {"chatId": MAIN_GROUP_CHAT_ID, "count": 1000},
    ]
    
    for i, payload in enumerate(test_cases, 1):
        print(f"\n  Case {i}: count={payload['count']}")
        try:
            response = requests.post(url, json=payload, timeout=10)
            print(f"    Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json() or []
                print(f"    Total messages: {len(data)}")
                
                # Analyze types
                types = {}
                recent_24h = {"incoming": 0, "outgoing": 0}
                cutoff = datetime.now() - timedelta(hours=24)
                cutoff_ts = int(cutoff.timestamp())
                
                for msg in data:
                    msg_type = msg.get('type', 'unknown')
                    types[msg_type] = types.get(msg_type, 0) + 1
                    
                    # Check if recent
                    timestamp = msg.get('timestamp', 0)
                    if timestamp >= cutoff_ts:
                        if msg_type in ['incoming', 'outgoing']:
                            recent_24h[msg_type] += 1
                
                print(f"    All types: {types}")
                print(f"    Recent 24h: {recent_24h}")
                
                # Show sample outgoing if any
                outgoing = [msg for msg in data if msg.get('type') == 'outgoing'][:2]
                if outgoing:
                    print(f"    Sample outgoing:")
                    for j, msg in enumerate(outgoing):
                        ts = msg.get('timestamp', 0)
                        dt = datetime.fromtimestamp(ts).strftime('%m-%d %H:%M') if ts else 'No time'
                        text = str(msg.get('textMessage', ''))[:30]
                        print(f"      {j+1}. [{dt}] {text}")
                else:
                    print(f"    ❌ No outgoing messages found")
            else:
                print(f"    ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"    ❌ Exception: {e}")

def test_2_getchathistory_with_different_params():
    """Test 2: getChatHistory with different parameter combinations"""
    print("\n🧪 TEST 2: getChatHistory with different parameters")
    print("-" * 50)
    
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    
    # Calculate timestamps
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    
    test_cases = [
        # Basic parameters
        {"name": "Just chatId", "payload": {"chatId": MAIN_GROUP_CHAT_ID}},
        {"name": "With count 20", "payload": {"chatId": MAIN_GROUP_CHAT_ID, "count": 20}},
        
        # Try with timestamps (might not be supported but worth testing)
        {"name": "Try with fromTimestamp", "payload": {
            "chatId": MAIN_GROUP_CHAT_ID, 
            "count": 100,
            "fromTimestamp": int(yesterday.timestamp())
        }},
        
        # Try different parameter names
        {"name": "Try with limit instead of count", "payload": {
            "chatId": MAIN_GROUP_CHAT_ID, 
            "limit": 100
        }},
        
        # Try GET method instead of POST
        {"name": "GET method with params", "method": "GET", "params": {
            "chatId": MAIN_GROUP_CHAT_ID,
            "count": 100
        }},
    ]
    
    for test_case in test_cases:
        print(f"\n  Testing: {test_case['name']}")
        try:
            if test_case.get('method') == 'GET':
                response = requests.get(url, params=test_case.get('params', {}), timeout=10)
            else:
                response = requests.post(url, json=test_case['payload'], timeout=10)
            
            print(f"    Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json() or []
                types = {}
                for msg in data:
                    msg_type = msg.get('type', 'unknown')
                    types[msg_type] = types.get(msg_type, 0) + 1
                
                print(f"    Messages: {len(data)}, Types: {types}")
            else:
                print(f"    Error: {response.text[:100]}")
                
        except Exception as e:
            print(f"    Exception: {e}")

def test_3_lastoutgoingmessages():
    """Test 3: All variations of lastOutgoingMessages"""
    print("\n🧪 TEST 3: lastOutgoingMessages variations")
    print("-" * 45)
    
    endpoints = [
        "lastOutgoingMessages",
        "LastOutgoingMessages", 
        "getLastOutgoingMessages",
        "lastSentMessages",
        "outgoingMessages"
    ]
    
    for endpoint in endpoints:
        print(f"\n  Testing: {endpoint}")
        url = f"{BASE_URL}/{endpoint}/{GREEN_API_TOKEN}"
        
        # Test different methods and parameters
        test_configs = [
            {"method": "GET", "params": {"minutes": 1440}},  # 24 hours
            {"method": "GET", "params": {"hours": 24}},
            {"method": "POST", "json": {"minutes": 1440}},
            {"method": "GET", "params": {}},  # No params
        ]
        
        for config in test_configs:
            try:
                if config["method"] == "GET":
                    response = requests.get(url, params=config.get("params", {}), timeout=10)
                else:
                    response = requests.post(url, json=config.get("json", {}), timeout=10)
                
                print(f"    {config['method']} {config.get('params', config.get('json', 'no-params'))}: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json() or []
                    if isinstance(data, list):
                        print(f"      ✅ Got {len(data)} messages")
                        
                        # Filter for our chat if any results
                        our_chat = [msg for msg in data if msg.get('chatId') == MAIN_GROUP_CHAT_ID]
                        if our_chat:
                            print(f"      🎯 {len(our_chat)} messages for our chat")
                            # Show sample
                            for i, msg in enumerate(our_chat[:2]):
                                ts = msg.get('timestamp', 0)
                                dt = datetime.fromtimestamp(ts).strftime('%m-%d %H:%M') if ts else 'No time'
                                text = str(msg.get('textMessage', ''))[:30]
                                print(f"        {i+1}. [{dt}] {text}")
                        else:
                            print(f"      ⚠️  No messages for our specific chat")
                    else:
                        print(f"      Response: {str(data)[:100]}")
                else:
                    print(f"      Error: {response.text[:50]}")
                    
            except Exception as e:
                print(f"      Exception: {e}")

def test_4_webhook_settings():
    """Test 4: Check and update webhook settings"""
    print("\n🧪 TEST 4: Webhook Settings")
    print("-" * 30)
    
    # Get current settings
    print("  Getting current settings...")
    url = f"{BASE_URL}/getSettings/{GREEN_API_TOKEN}"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"    Status: {response.status_code}")
        
        if response.status_code == 200:
            settings = response.json()
            
            important_settings = {
                'incomingWebhook': settings.get('incomingWebhook'),
                'outgoingWebhook': settings.get('outgoingWebhook'),
                'outgoingMessageWebhook': settings.get('outgoingMessageWebhook'),
                'outgoingAPIMessageWebhook': settings.get('outgoingAPIMessageWebhook'),
                'enableMessagesHistory': settings.get('enableMessagesHistory'),
            }
            
            print("    Current settings:")
            for key, value in important_settings.items():
                status = "✅" if value == "yes" else "❌" if value == "no" else "❓"
                print(f"      {status} {key}: {value}")
            
            # Try to enable important settings
            print("\n  Trying to enable outgoing message settings...")
            set_url = f"{BASE_URL}/setSettings/{GREEN_API_TOKEN}"
            
            new_settings = {
                'outgoingWebhook': 'yes',
                'outgoingMessageWebhook': 'yes',
                'outgoingAPIMessageWebhook': 'yes',
                'enableMessagesHistory': 'yes'
            }
            
            set_response = requests.post(set_url, json=new_settings, timeout=10)
            print(f"    Set settings status: {set_response.status_code}")
            
            if set_response.status_code == 200:
                result = set_response.json()
                print(f"    Result: {result}")
            else:
                print(f"    Error: {set_response.text}")
        
    except Exception as e:
        print(f"    Exception: {e}")

def test_5_alternative_endpoints():
    """Test 5: Try alternative endpoints"""
    print("\n🧪 TEST 5: Alternative endpoints")
    print("-" * 35)
    
    alternative_endpoints = [
        "getChatMessages",
        "getHistory", 
        "chatHistory",
        "messages",
        "getAllMessages",
        "getMessages"
    ]
    
    for endpoint in alternative_endpoints:
        print(f"\n  Testing: {endpoint}")
        url = f"{BASE_URL}/{endpoint}/{GREEN_API_TOKEN}"
        
        try:
            # Try POST with our standard payload
            payload = {"chatId": MAIN_GROUP_CHAT_ID, "count": 50}
            response = requests.post(url, json=payload, timeout=10)
            print(f"    POST: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"      ✅ Got {len(data)} items")
                else:
                    print(f"      Response: {str(data)[:50]}")
            
            # Try GET
            response = requests.get(url, params=payload, timeout=10)
            print(f"    GET: {response.status_code}")
            
        except Exception as e:
            print(f"    Exception: {e}")

def main():
    """Run all systematic tests"""
    print("🚀 SYSTEMATIC GREENAPI TESTING")
    print("=" * 60)
    
    if not all([GREEN_API_ID_INSTANCE, GREEN_API_TOKEN, MAIN_GROUP_CHAT_ID]):
        print("❌ Missing environment variables!")
        print(f"   GREEN_API_ID_INSTANCE: {'✅' if GREEN_API_ID_INSTANCE else '❌'}")
        print(f"   GREEN_API_TOKEN: {'✅' if GREEN_API_TOKEN else '❌'}")
        print(f"   MAIN_GROUP_CHAT_ID: {'✅' if MAIN_GROUP_CHAT_ID else '❌'}")
        return
    
    print(f"✅ Testing with:")
    print(f"   Instance: {GREEN_API_ID_INSTANCE}")
    print(f"   Chat: {MAIN_GROUP_CHAT_ID}")
    print(f"   Base URL: {BASE_URL}")
    
    # Run all tests
    test_1_basic_getchathistory()
    test_2_getchathistory_with_different_params()
    test_3_lastoutgoingmessages()
    test_4_webhook_settings()
    test_5_alternative_endpoints()
    
    print("\n" + "=" * 60)
    print("🎯 TESTING COMPLETE")
    print("\nLook for:")
    print("✅ Tests that return outgoing messages")
    print("🎯 Messages specifically for your chat ID")
    print("⚠️  Settings that need to be enabled")
    print("❌ Endpoints that don't work")

if __name__ == "__main__":
    main()
