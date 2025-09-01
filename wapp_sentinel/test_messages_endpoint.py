#!/usr/bin/env python3
"""
Test script for the new messages retrieval endpoints
"""

import requests
import json
import sys
from datetime import datetime

API_BASE = "http://localhost:8000"

def test_messages_all():
    """Test the /messages/all endpoint with different parameters"""
    print("🧪 TESTING /messages/all ENDPOINT")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Get all available messages",
            "params": {}
        },
        {
            "name": "Get messages from last 24 hours",
            "params": {"hours_back": 24}
        },
        {
            "name": "Get messages from last 7 days",
            "params": {"days_back": 7}
        },
        {
            "name": "Get only incoming messages from last 3 days",
            "params": {"days_back": 3, "message_type": "incoming"}
        },
        {
            "name": "Get only outgoing messages from last 3 days",
            "params": {"days_back": 3, "message_type": "outgoing"}
        },
        {
            "name": "Get last 50 messages maximum",
            "params": {"days_back": 7, "max_messages": 50}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ {test_case['name']}")
        print("-" * 30)
        
        try:
            response = requests.get(f"{API_BASE}/messages/all", params=test_case['params'])
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success!")
                print(f"   Total messages: {data['total_messages']}")
                print(f"   Incoming: {data['message_breakdown']['incoming']}")
                print(f"   Outgoing: {data['message_breakdown']['outgoing']}")
                
                if 'date_range' in data:
                    print(f"   Date range: {data['date_range']['span_days']} days")
                    print(f"   From: {data['date_range']['oldest_message'][:10]}")
                    print(f"   To: {data['date_range']['newest_message'][:10]}")
                
                # Show sample of first few messages
                if data['messages']:
                    print(f"   Sample messages:")
                    for j, msg in enumerate(data['messages'][:3]):
                        msg_time = datetime.fromtimestamp(msg.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M') if msg.get('timestamp') else 'Unknown'
                        msg_type = msg.get('type', 'unknown')
                        msg_text = msg.get('textMessage', '')[:50] + "..." if len(msg.get('textMessage', '')) > 50 else msg.get('textMessage', '')
                        print(f"     {j+1}. [{msg_time}] {msg_type}: {msg_text}")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

def test_messages_summary():
    """Test the /messages/summary endpoint"""
    print("\n🧪 TESTING /messages/summary ENDPOINT")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE}/messages/summary", params={"days_back": 7})
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Summary retrieved successfully!")
            print(f"   Chat ID: {data['chat_id']}")
            print(f"   Total messages: {data['summary']['total_messages']}")
            print(f"   Incoming: {data['summary']['incoming_messages']}")
            print(f"   Outgoing: {data['summary']['outgoing_messages']}")
            print(f"   Days analyzed: {data['summary']['days_analyzed']}")
            
            if 'date_range' in data:
                print(f"   Date span: {data['date_range']['span_days']} days")
            
            print(f"   Message types breakdown:")
            for msg_type, count in data['message_types'].items():
                print(f"     {msg_type}: {count}")
            
            print(f"   Recent messages sample:")
            for i, msg in enumerate(data['recent_messages_sample'], 1):
                print(f"     {i}. [{msg['timestamp'][:10] if msg['timestamp'] else 'Unknown'}] {msg['type']}: {msg['text_preview']}")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def check_api_status():
    """Check if the API server is running"""
    print("🔍 CHECKING API STATUS")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code == 200:
            print("✅ API Server is running")
            return True
        else:
            print(f"❌ API Server returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        print("💡 Make sure to start the server with: uvicorn main:app --reload")
        return False

def test_outgoing_messages():
    """Test the /messages/outgoing endpoint"""
    print("\n🧪 TESTING /messages/outgoing ENDPOINT")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE}/messages/outgoing", params={"hours_back": 24})
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Outgoing messages retrieved successfully!")
            print(f"   Chat ID: {data['chat_id']}")
            print(f"   Total outgoing messages: {data['total_outgoing_messages']}")
            print(f"   Hours analyzed: {data['hours_analyzed']}")
            
            if data['messages']:
                print(f"   Sample outgoing messages:")
                for i, msg in enumerate(data['messages'][:3], 1):
                    msg_time = datetime.fromtimestamp(msg.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M') if msg.get('timestamp') else 'Unknown'
                    msg_text = msg.get('textMessage', '')[:50] + "..." if len(msg.get('textMessage', '')) > 50 else msg.get('textMessage', '')
                    print(f"     {i}. [{msg_time}] {msg_text}")
            else:
                print("   ⚠️  No outgoing messages found in the last 24 hours")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_debug_endpoint():
    """Test the /messages/debug endpoint"""
    print("\n🧪 TESTING /messages/debug ENDPOINT")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE}/messages/debug")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Debug information retrieved successfully!")
            print(f"   Chat ID: {data['chat_id']}")
            
            debug_results = data['debug_results']
            print(f"\n   📊 Debug Results:")
            
            for method_name, result in debug_results.items():
                print(f"     {method_name}:")
                print(f"       Method: {result['method']}")
                print(f"       Count: {result['count']}")
                
                if 'breakdown' in result:
                    breakdown = result['breakdown']
                    print(f"       Incoming: {breakdown.get('incoming', 0)}")
                    print(f"       Outgoing: {breakdown.get('outgoing', 0)}")
                print()
            
            print(f"   💡 Recommendation: {data['recommendation']}")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    """Main test function"""
    print("🚀 MESSAGES ENDPOINT TESTER")
    print("=" * 50)
    
    # Check if server is running
    if not check_api_status():
        return
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "all":
            test_messages_all()
        elif sys.argv[1] == "summary":
            test_messages_summary()
        elif sys.argv[1] == "outgoing":
            test_outgoing_messages()
        elif sys.argv[1] == "debug":
            test_debug_endpoint()
        else:
            print("Usage: python test_messages_endpoint.py [all|summary|outgoing|debug]")
    else:
        # Run all tests
        test_messages_all()
        test_messages_summary()
        test_outgoing_messages()
        test_debug_endpoint()
    
    print("\n🎉 Testing complete!")
    print("\n📚 Available endpoints:")
    print("   GET /messages/all - Retrieve all messages with filtering")
    print("   GET /messages/summary - Get message statistics summary")
    print("   GET /messages/outgoing - Get only outgoing messages")
    print("   GET /messages/debug - Debug message retrieval methods")
    print("\n💡 Usage examples:")
    print("   curl 'http://localhost:8000/messages/all'")
    print("   curl 'http://localhost:8000/messages/all?days_back=7&message_type=incoming'")
    print("   curl 'http://localhost:8000/messages/outgoing?hours_back=48'")
    print("   curl 'http://localhost:8000/messages/debug'")
    print("   curl 'http://localhost:8000/messages/summary?days_back=3'")

if __name__ == "__main__":
    main()
