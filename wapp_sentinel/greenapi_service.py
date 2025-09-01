import requests
import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

load_dotenv()

GREEN_API_ID_INSTANCE = os.getenv("GREEN_API_ID_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
BASE_URL = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}"

def get_recent_messages(chat_id: str, hours_back: int = 48):
    """Get messages from specified hours back"""
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    
    # Calculate timestamp for hours_back ago
    cutoff_time = datetime.now() - timedelta(hours=hours_back)
    cutoff_timestamp = int(cutoff_time.timestamp())
    
    payload = {
        "chatId": chat_id,
        "count": 1000  # Get more messages to ensure we capture all recent ones
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Error getting chat history: {response.text}")
            return []
        
        messages = response.json() or []
        
        # Filter messages from specified time period
        recent_messages = []
        for msg in messages:
            msg_timestamp = msg.get('timestamp', 0)
            
            # Only include messages from specified time period
            if msg_timestamp >= cutoff_timestamp:
                recent_messages.append(msg)
        
        print(f"Found {len(recent_messages)} recent messages (last {hours_back} hours)")
        return recent_messages
        
    except Exception as e:
        print(f"Error getting recent messages: {e}")
        return []

def get_messages_bulk(chat_id: str, days_back: int = 7, max_messages: int = 1000):
    """Get all messages from specified days back with enhanced retrieval"""
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    
    # Calculate timestamp for days_back ago
    cutoff_time = datetime.now() - timedelta(days=days_back)
    cutoff_timestamp = int(cutoff_time.timestamp())
    
    print(f"Fetching messages from last {days_back} days...")
    print(f"Looking for messages after: {cutoff_time}")
    print(f"Cut-off timestamp: {cutoff_timestamp}")
    
    all_messages = []
    
    # Try different approaches to get more messages
    for count in [1000, 500, 100]:
        print(f"\n📡 Trying to fetch {count} messages...")
        
        payload = {
            "chatId": chat_id,
            "count": count
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code != 200:
                print(f"❌ Error with count={count}: {response.text}")
                continue
            
            messages = response.json() or []
            print(f"📥 Retrieved {len(messages)} total messages from API")
            
            if messages:
                # Show date range of retrieved messages
                timestamps = [msg.get('timestamp', 0) for msg in messages if msg.get('timestamp')]
                if timestamps:
                    oldest_ts = min(timestamps)
                    newest_ts = max(timestamps)
                    oldest_date = datetime.fromtimestamp(oldest_ts)
                    newest_date = datetime.fromtimestamp(newest_ts)
                    
                    print(f"📅 Message date range:")
                    print(f"   Oldest: {oldest_date}")
                    print(f"   Newest: {newest_date}")
                    print(f"   Span: {(newest_date - oldest_date).days} days")
                
                # Filter messages from specified time period
                filtered_messages = []
                for msg in messages:
                    msg_timestamp = msg.get('timestamp', 0)
                    msg_date = datetime.fromtimestamp(msg_timestamp) if msg_timestamp else None
                    
                    if msg_timestamp >= cutoff_timestamp:
                        filtered_messages.append(msg)
                
                # Sort by timestamp (oldest first)
                filtered_messages.sort(key=lambda x: x.get('timestamp', 0))
                
                print(f"🗓️  Found {len(filtered_messages)} messages from last {days_back} days")
                
                # Show breakdown
                incoming_count = sum(1 for msg in filtered_messages if msg.get('type') == 'incoming')
                outgoing_count = sum(1 for msg in filtered_messages if msg.get('type') == 'outgoing')
                
                print(f"   📨 Incoming: {incoming_count}")
                print(f"   📤 Outgoing: {outgoing_count}")
                
                # If we found messages within our timeframe, use this result
                if filtered_messages:
                    return filtered_messages
                else:
                    print(f"⚠️  No messages found within {days_back} days timeframe")
                    # Show some sample messages to debug
                    print(f"📝 Sample of available messages:")
                    for i, msg in enumerate(messages[:3]):
                        timestamp = msg.get('timestamp', 0)
                        msg_time = datetime.fromtimestamp(timestamp) if timestamp else 'Unknown'
                        msg_type = msg.get('type', 'unknown')
                        msg_text = msg.get('textMessage', '')[:50]
                        print(f"   {i+1}. [{msg_time}] {msg_type}: {msg_text}...")
                
            else:
                print(f"❌ No messages retrieved with count={count}")
                
        except Exception as e:
            print(f"❌ Error with count={count}: {e}")
            continue
    
    # If we reach here, we couldn't get messages within the timeframe
    print(f"\n⚠️  Could not retrieve messages from last {days_back} days")
    print(f"💡 Trying to get ANY available messages for analysis...")
    
    # Try one more time with basic parameters
    try:
        payload = {"chatId": chat_id, "count": 100}
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            messages = response.json() or []
            print(f"📥 Retrieved {len(messages)} messages for analysis")
            
            # Return all messages regardless of timeframe for manual analysis
            return messages
        
    except Exception as e:
        print(f"❌ Final attempt failed: {e}")
    
    return []

def get_all_available_messages(chat_id: str):
    """Get all available messages regardless of timeframe"""
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    
    print(f"📥 Fetching ALL available messages for: {chat_id}")
    
    payload = {
        "chatId": chat_id,
        "count": 1000  # Maximum
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Error getting chat history: {response.text}")
            return []
        
        messages = response.json() or []
        print(f"Retrieved {len(messages)} total messages from API")
        
        if messages:
            # Show date range
            timestamps = [msg.get('timestamp', 0) for msg in messages if msg.get('timestamp')]
            if timestamps:
                oldest_ts = min(timestamps)
                newest_ts = max(timestamps)
                oldest_date = datetime.fromtimestamp(oldest_ts)
                newest_date = datetime.fromtimestamp(newest_ts)
                
                print(f"📅 Full date range available:")
                print(f"   Oldest: {oldest_date}")
                print(f"   Newest: {newest_date}")
                print(f"   Total span: {(newest_date - oldest_date).days} days")
            
            # Show breakdown
            incoming_count = sum(1 for msg in messages if msg.get('type') == 'incoming')
            outgoing_count = sum(1 for msg in messages if msg.get('type') == 'outgoing')
            
            print(f"📊 Message breakdown:")
            print(f"   📨 Incoming: {incoming_count}")
            print(f"   📤 Outgoing: {outgoing_count}")
        
        return messages
        
    except Exception as e:
        print(f"Error getting all messages: {e}")
        return []

def send_message(chat_id: str, message: str):
    """Send message to WhatsApp group via GreenAPI"""
    
    # TESTING MODE - check environment variable
    if os.getenv("TESTING_MODE") == "true":
        print(f"\n🧪 TEST MODE - Would send to: {chat_id}")
        print(f"📱 Message preview:")
        print("-" * 40)
        print(message)
        print("-" * 40)
        return {"success": True, "test_mode": True, "message": "Test mode - not actually sent"}
    
    url = f"{BASE_URL}/sendMessage/{GREEN_API_TOKEN}"
    
    payload = {
        "chatId": chat_id,
        "message": message
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return {"error": str(e)}

def get_notification():
    """Get incoming notifications from GreenAPI"""
    url = f"{BASE_URL}/receiveNotification/{GREEN_API_TOKEN}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting notification: {e}")
        return None

def delete_notification(receipt_id: str):
    """Delete processed notification"""
    url = f"{BASE_URL}/deleteNotification/{GREEN_API_TOKEN}/{receipt_id}"
    
    try:
        response = requests.delete(url)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error deleting notification: {e}")
        return False