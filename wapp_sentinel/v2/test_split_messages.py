"""
Test script for Split Messages Daily Report Feature
This demonstrates how to send daily reports as multiple separate messages
"""
import requests
from datetime import date

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_split_messages_report():
    """
    Test sending daily report as multiple separate messages
    """
    print("\n🧪 Testing Split Messages Daily Report\n")
    
    # Replace with your actual chat ID
    # Format: "79123456789@c.us" for individual or "79123456789-1234567890@g.us" for group
    CHAT_ID = "79123456789@c.us"
    
    # Get today's date
    today = date.today().strftime("%Y-%m-%d")
    
    # Test 1: Send with split messages (default)
    print("📤 Test 1: Sending report with SPLIT MESSAGES (default)")
    print(f"   Date: {today}")
    print(f"   Split messages: True")
    print(f"   Delay: 1.5 seconds\n")
    
    url = f"{BASE_URL}/orders/send-daily-report"
    payload = {
        "date": today,
        "chat_id": CHAT_ID,
        "split_messages": True,  # Send as multiple messages
        "delay_seconds": 1.5     # 1.5 seconds delay between messages
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        print("✅ Success!")
        print(f"   Status: {result.get('status')}")
        print(f"   Orders count: {result.get('orders_count')}")
        print(f"   Messages sent: {result.get('messages_sent')}")
        print(f"   Messages failed: {result.get('messages_failed')}")
        print(f"   Split mode: {result.get('split_mode')}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Send as single message (old method)
    print("📤 Test 2: Sending report as SINGLE MESSAGE (legacy mode)")
    print(f"   Date: {today}")
    print(f"   Split messages: False\n")
    
    payload = {
        "date": today,
        "chat_id": CHAT_ID,
        "split_messages": False  # Send as one message (old behavior)
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        print("✅ Success!")
        print(f"   Status: {result.get('status')}")
        print(f"   Orders count: {result.get('orders_count')}")
        print(f"   Split mode: {result.get('split_mode')}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Custom delay
    print("📤 Test 3: Sending with CUSTOM DELAY")
    print(f"   Date: {today}")
    print(f"   Split messages: True")
    print(f"   Delay: 0.5 seconds (faster)\n")
    
    payload = {
        "date": today,
        "chat_id": CHAT_ID,
        "split_messages": True,
        "delay_seconds": 0.5  # Faster delay
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        print("✅ Success!")
        print(f"   Status: {result.get('status')}")
        print(f"   Orders count: {result.get('orders_count')}")
        print(f"   Messages sent: {result.get('messages_sent')}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")


def test_preview_report():
    """
    Preview the report without sending (still shows as single message for preview)
    """
    print("\n🔍 Testing Report Preview\n")
    
    today = date.today().strftime("%Y-%m-%d")
    
    url = f"{BASE_URL}/orders/preview-daily-report"
    payload = {
        "date": today
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        print("✅ Preview Generated!")
        print(f"   Date: {result.get('date')}")
        print(f"   Orders count: {result.get('orders_count')}")
        print("\n📋 Report Preview:")
        print(result.get('report_text', 'No report text available'))
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("   SPLIT MESSAGES DAILY REPORT TEST")
    print("="*70)
    print("\n⚠️  IMPORTANT: Update CHAT_ID in the script before running!")
    print("    Format: '79123456789@c.us' for individual")
    print("    Format: '79123456789-1234567890@g.us' for group\n")
    
    # Uncomment the tests you want to run
    # test_split_messages_report()
    # test_preview_report()
    
    print("\n✨ Uncomment the test functions to run them!\n")
