from greenapi_service import get_recent_messages
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")

def test_recent_messages():
    """Test getting recent messages only"""
    
    print("=== TESTING RECENT MESSAGES ===")
    print(f"Getting messages from last 48 hours from: {MAIN_GROUP_CHAT_ID}")
    
    messages = get_recent_messages(MAIN_GROUP_CHAT_ID, hours_back=48)
    
    if not messages:
        print("❌ No recent messages found!")
        print("\nPossible solutions:")
        print("1. Send a test message to your main group RIGHT NOW")
        print("2. Check if your group chat ID is correct")
        print("3. Verify GreenAPI permissions")
        return
    
    print(f"✅ Found {len(messages)} recent messages")
    
    for i, msg in enumerate(messages[:10]):  # Show first 10
        timestamp = msg.get('timestamp', 0)
        msg_time = datetime.fromtimestamp(timestamp) if timestamp else 'Unknown'
        msg_text = msg.get('textMessage', '')[:50] + '...' if len(msg.get('textMessage', '')) > 50 else msg.get('textMessage', '')
        
        print(f"\nMessage {i+1}:")
        print(f"  Time: {msg_time}")
        print(f"  Type: {msg.get('typeMessage')}")
        print(f"  Text: {msg_text}")
    
    print(f"\n=== NEXT STEPS ===")
    print("1. If you see recent messages above, run: POST /process-messages")
    print("2. If no recent messages, send a test order to your group first")
    print("3. Then check: GET /orders/today")

if __name__ == "__main__":
    test_recent_messages()