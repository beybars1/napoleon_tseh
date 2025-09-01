import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

GREEN_API_ID_INSTANCE = os.getenv("GREEN_API_ID_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")

def get_all_group_messages():
    """Get all messages from group (incoming and outgoing)"""
    
    print("=== TESTING ALL GROUP MESSAGES ===")
    
    # Method 1: Try getContactInfo to understand group structure
    contact_url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/getContactInfo/{GREEN_API_TOKEN}"
    contact_payload = {"chatId": MAIN_GROUP_CHAT_ID}
    
    try:
        contact_response = requests.post(contact_url, json=contact_payload)
        print(f"Group info: {contact_response.text}")
    except Exception as e:
        print(f"Error getting group info: {e}")
    
    # Method 2: Try getChatHistory with different parameters
    history_url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/getChatHistory/{GREEN_API_TOKEN}"
    
    # Try getting more messages and see what we get
    payload = {
        "chatId": MAIN_GROUP_CHAT_ID,
        "count": 50
    }
    
    try:
        response = requests.post(history_url, json=payload)
        if response.status_code == 200:
            messages = response.json() or []
            print(f"\nFound {len(messages)} total messages")
            
            # Analyze message types
            incoming_count = 0
            outgoing_count = 0
            
            for msg in messages:
                msg_type = msg.get('type', '')
                if msg_type == 'incoming':
                    incoming_count += 1
                elif msg_type == 'outgoing':
                    outgoing_count += 1
            
            print(f"Incoming messages: {incoming_count}")
            print(f"Outgoing messages: {outgoing_count}")
            
            # Show recent messages with sender info
            print(f"\n=== RECENT MESSAGES (All Types) ===")
            cutoff_time = datetime.now() - timedelta(hours=48)
            cutoff_timestamp = int(cutoff_time.timestamp())
            
            recent_messages = []
            for msg in messages:
                if msg.get('timestamp', 0) >= cutoff_timestamp:
                    recent_messages.append(msg)
            
            print(f"Recent messages (48h): {len(recent_messages)}")
            
            for i, msg in enumerate(recent_messages[:5]):  # Show first 5
                timestamp = msg.get('timestamp', 0)
                msg_time = datetime.fromtimestamp(timestamp) if timestamp else 'Unknown'
                msg_type = msg.get('type', 'unknown')
                sender_data = msg.get('senderData', {})
                sender_name = sender_data.get('senderName', 'Unknown')
                msg_text = msg.get('textMessage', '')[:50]
                
                print(f"\nMessage {i+1}:")
                print(f"  Time: {msg_time}")
                print(f"  Type: {msg_type}")
                print(f"  Sender: {sender_name}")
                print(f"  Text: {msg_text}...")
                
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

    # Method 3: Try using webhooks (if no incoming messages found)
    if incoming_count == 0:
        print(f"\n=== WEBHOOK RECOMMENDATION ===")
        print("❌ No incoming messages found in history")
        print("This usually means:")
        print("1. Only your own messages are stored in history")
        print("2. You need to enable proper webhook settings")
        print("3. Or use real-time notification polling")
        
        # Check current webhook settings
        settings_url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/getSettings/{GREEN_API_TOKEN}"
        try:
            settings_response = requests.get(settings_url)
            if settings_response.status_code == 200:
                settings = settings_response.json()
                print(f"\nCurrent settings:")
                print(f"  incomingWebhook: {settings.get('incomingWebhook')}")
                print(f"  enableMessagesHistory: {settings.get('enableMessagesHistory')}")
        except:
            pass

if __name__ == "__main__":
    get_all_group_messages()