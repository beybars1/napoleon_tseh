import requests
import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

load_dotenv()

GREEN_API_ID_INSTANCE = os.getenv("GREEN_API_ID_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
BASE_URL = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}"

def get_recent_messages(chat_id: str, hours_back: int = 48):
    """Get messages from specified hours back (should include both incoming and outgoing)"""
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    
    # Calculate timestamp for hours_back ago
    cutoff_time = datetime.now() - timedelta(hours=hours_back)
    cutoff_timestamp = int(cutoff_time.timestamp())
    
    payload = {
        "chatId": chat_id,
        "count": 1000  # Get more messages to ensure we capture all recent ones
    }
    
    try:
        print(f"🔄 Getting chat history for {chat_id} (last {hours_back} hours)")
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            print(f"❌ Error getting chat history: {response.status_code} - {response.text}")
            return []
        
        messages = response.json() or []
        print(f"📥 Retrieved {len(messages)} total messages from getChatHistory")
        
        # Analyze message types before filtering
        if messages:
            type_breakdown = {}
            for msg in messages:
                msg_type = msg.get('type', 'unknown')
                type_breakdown[msg_type] = type_breakdown.get(msg_type, 0) + 1
            
            print(f"📊 Message types in response: {type_breakdown}")
            
            # Show samples of different types
            for msg_type in type_breakdown.keys():
                sample_msgs = [msg for msg in messages if msg.get('type') == msg_type][:2]
                print(f"   Sample {msg_type} messages:")
                for i, msg in enumerate(sample_msgs):
                    timestamp = msg.get('timestamp', 0)
                    msg_time = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S') if timestamp else 'Unknown'
                    text = str(msg.get('textMessage', ''))[:30] + "..." if len(str(msg.get('textMessage', ''))) > 30 else str(msg.get('textMessage', ''))
                    sender = msg.get('senderData', {}).get('sender', 'Unknown')
                    print(f"     {i+1}. [{msg_time}] from {sender}: {text}")
        
        # Filter messages from specified time period
        recent_messages = []
        debug_timestamps = {"kept": [], "filtered_out": []}
        
        for msg in messages:
            msg_timestamp = msg.get('timestamp', 0)
            msg_type = msg.get('type', 'unknown')
            
            # Debug: Check timestamp values
            if msg_timestamp:
                msg_time = datetime.fromtimestamp(msg_timestamp)
                is_recent = msg_timestamp >= cutoff_timestamp
                
                if is_recent:
                    recent_messages.append(msg)
                    debug_timestamps["kept"].append({
                        "type": msg_type,
                        "timestamp": msg_timestamp,
                        "datetime": msg_time.strftime('%Y-%m-%d %H:%M:%S'),
                        "text_preview": str(msg.get('textMessage', ''))[:30]
                    })
                else:
                    debug_timestamps["filtered_out"].append({
                        "type": msg_type,
                        "timestamp": msg_timestamp,
                        "datetime": msg_time.strftime('%Y-%m-%d %H:%M:%S'),
                        "hours_old": (datetime.now() - msg_time).total_seconds() / 3600
                    })
            else:
                # No timestamp - include it anyway
                recent_messages.append(msg)
                debug_timestamps["kept"].append({
                    "type": msg_type,
                    "timestamp": "None",
                    "datetime": "No timestamp",
                    "text_preview": str(msg.get('textMessage', ''))[:30]
                })
        
        # Debug output
        print(f"🕐 Cutoff time: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')} ({cutoff_timestamp})")
        print(f"🕐 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if debug_timestamps["kept"]:
            print(f"✅ Kept {len(debug_timestamps['kept'])} messages:")
            for i, item in enumerate(debug_timestamps["kept"][:3]):
                print(f"   {i+1}. {item['type']} at {item['datetime']}: {item.get('text_preview', '')}")
        
        if debug_timestamps["filtered_out"]:
            print(f"❌ Filtered out {len(debug_timestamps['filtered_out'])} messages:")
            for i, item in enumerate(debug_timestamps["filtered_out"][:3]):
                print(f"   {i+1}. {item['type']} at {item['datetime']} ({item.get('hours_old', 0):.1f}h old)")
                
        # Show type breakdown of filtered out messages
        filtered_types = {}
        for item in debug_timestamps["filtered_out"]:
            msg_type = item['type']
            filtered_types[msg_type] = filtered_types.get(msg_type, 0) + 1
        
        if filtered_types:
            print(f"🗑️  Filtered out types: {filtered_types}")
        
        # Final breakdown
        if recent_messages:
            filtered_types = {}
            for msg in recent_messages:
                msg_type = msg.get('type', 'unknown')
                filtered_types[msg_type] = filtered_types.get(msg_type, 0) + 1
            print(f"📋 After time filtering ({hours_back}h): {filtered_types}")
        
        print(f"✅ Found {len(recent_messages)} recent messages (last {hours_back} hours)")
        return recent_messages
        
    except Exception as e:
        print(f"❌ Error getting recent messages: {e}")
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

def get_outgoing_messages(chat_id: str = None, minutes: int = 1440):
    """Get outgoing messages from last N minutes (default 24 hours = 1440 minutes)"""
    
    # Try multiple possible endpoints for outgoing messages
    possible_urls = [
        f"{BASE_URL}/lastOutgoingMessages/{GREEN_API_TOKEN}",
        f"{BASE_URL}/LastOutgoingMessages/{GREEN_API_TOKEN}",
        f"{BASE_URL}/getLastOutgoingMessages/{GREEN_API_TOKEN}"
    ]
    
    all_outgoing = []
    
    for url in possible_urls:
        print(f"🔄 Trying outgoing messages endpoint: {url}")
        
        try:
            # Try GET method with params
            response = requests.get(url, params={"minutes": minutes})
            print(f"   GET Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json() or []
                print(f"   ✅ GET Success! Retrieved {len(data)} outgoing messages")
                all_outgoing = data
                break
            else:
                print(f"   ❌ GET Failed: {response.text[:100]}")
            
            # Try POST method with JSON body
            response = requests.post(url, json={"minutes": minutes})
            print(f"   POST Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json() or []
                print(f"   ✅ POST Success! Retrieved {len(data)} outgoing messages")
                all_outgoing = data
                break
            else:
                print(f"   ❌ POST Failed: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Exception with {url}: {e}")
            continue
    
    if not all_outgoing:
        print("⚠️  No outgoing messages found from any endpoint")
        return []
    
    # Filter by chat_id if specified
    if chat_id:
        print(f"🔍 Filtering outgoing messages for chat: {chat_id}")
        filtered_messages = []
        
        for msg in all_outgoing:
            msg_chat_id = msg.get('chatId') or msg.get('chat_id') or msg.get('to')
            if msg_chat_id == chat_id:
                filtered_messages.append(msg)
        
        print(f"   Filtered to {len(filtered_messages)} messages for specific chat")
        return filtered_messages
    
    return all_outgoing

def get_combined_messages(chat_id: str, hours_back: int = 48):
    """Get both incoming and outgoing messages combined"""
    print(f"🔄 Fetching combined messages for last {hours_back} hours...")
    
    # Get incoming messages
    print("📥 Getting incoming messages...")
    incoming_messages = get_recent_messages(chat_id, hours_back)
    
    # Get outgoing messages (convert hours to minutes)
    print("📤 Getting outgoing messages...")
    outgoing_messages = get_outgoing_messages(chat_id, hours_back * 60)
    
    # Combine and sort by timestamp
    all_messages = incoming_messages + outgoing_messages
    
    # Sort by timestamp (oldest first)
    all_messages.sort(key=lambda x: x.get('timestamp', 0))
    
    print(f"📊 Combined results:")
    print(f"   📥 Incoming: {len(incoming_messages)}")
    print(f"   📤 Outgoing: {len(outgoing_messages)}")
    print(f"   📋 Total: {len(all_messages)}")
    
    return all_messages

def get_all_available_messages(chat_id: str):
    """Get ALL available messages regardless of timeframe - this should include both types"""
    print(f"📥 Fetching ALL available messages for: {chat_id}")
    
    # Get messages using chat history (should include both incoming and outgoing)
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    payload = {
        "chatId": chat_id,
        "count": 1000  # Maximum
    }
    
    all_messages = []
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"❌ Error getting chat history: {response.text}")
            return []
        
        all_messages = response.json() or []
        print(f"📥 Retrieved {len(all_messages)} total messages from getChatHistory")
        
        # Analyze what we got
        if all_messages:
            type_breakdown = {}
            for msg in all_messages:
                msg_type = msg.get('type', 'unknown')
                type_breakdown[msg_type] = type_breakdown.get(msg_type, 0) + 1
            
            print(f"📊 Message types retrieved: {type_breakdown}")
            
            # Show date range
            timestamps = [msg.get('timestamp', 0) for msg in all_messages if msg.get('timestamp')]
            if timestamps:
                oldest_ts = min(timestamps)
                newest_ts = max(timestamps)
                oldest_date = datetime.fromtimestamp(oldest_ts)
                newest_date = datetime.fromtimestamp(newest_ts)
                
                print(f"📅 Full date range available:")
                print(f"   Oldest: {oldest_date}")
                print(f"   Newest: {newest_date}")
                print(f"   Total span: {(newest_date - oldest_date).days} days")
            
            # Sort by timestamp (newest first for better user experience)
            all_messages.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            print(f"✅ Returning {len(all_messages)} messages WITHOUT time filtering")
        
    except Exception as e:
        print(f"❌ Error getting all messages: {e}")
        return []
    
    return all_messages

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