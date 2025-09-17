import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
import json
import os

from ..core.config import settings

class GreenAPIService:
    def __init__(self):
        self.instance_id = settings.GREEN_API_ID_INSTANCE
        self.api_token = settings.GREEN_API_TOKEN
        self.base_url = f"https://api.green-api.com/waInstance{self.instance_id}"
        
    def _make_request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> dict:
        """Make request to GreenAPI with retries"""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"GreenAPI request error: {e}")
            return {"error": str(e)}

    def get_chat_history(
        self, 
        chat_id: str, 
        count: int = 100,
        message_type: Optional[str] = None,
        min_timestamp: Optional[int] = None
    ) -> List[Dict]:
        """
        Get chat history for a specific chat
        
        Args:
            chat_id: Chat ID in format "1234567890@g.us" for groups
            count: Number of messages to retrieve
            message_type: Filter by 'incoming' or 'outgoing'
            min_timestamp: Only get messages after this timestamp
        """
        endpoint = f"getChatHistory/{self.api_token}"
        
        data = {
            "chatId": chat_id,
            "count": min(count, settings.MAX_MESSAGES_PER_REQUEST)
        }
        
        print(f"🔄 Getting chat history for {chat_id}")
        response = self._make_request("POST", endpoint, data=data)
        messages = response or []
        
        if messages:
            # Show message type breakdown
            type_breakdown = {}
            for msg in messages:
                msg_type = msg.get('type', 'unknown')
                type_breakdown[msg_type] = type_breakdown.get(msg_type, 0) + 1
            print(f"📊 Message types: {type_breakdown}")
            
            # Show date range
            timestamps = [msg.get('timestamp', 0) for msg in messages if msg.get('timestamp')]
            if timestamps:
                oldest_ts = min(timestamps)
                newest_ts = max(timestamps)
                print(f"📅 Date range: {datetime.fromtimestamp(oldest_ts)} to {datetime.fromtimestamp(newest_ts)}")
        
        # Apply filters
        if message_type:
            messages = [msg for msg in messages if msg.get('type') == message_type]
            print(f"🔍 Filtered to {len(messages)} {message_type} messages")
            
        if min_timestamp:
            original_count = len(messages)
            messages = [msg for msg in messages if msg.get('timestamp', 0) >= min_timestamp]
            print(f"⏰ Time filtered from {original_count} to {len(messages)} messages")
            
        return messages

    def get_messages_by_date_range(
        self,
        chat_id: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        message_type: Optional[str] = None
    ) -> List[Dict]:
        """Get messages within a specific date range"""
        end_date = end_date or datetime.now()
        min_timestamp = int(start_date.timestamp())
        
        print(f"📅 Getting messages from {start_date} to {end_date}")
        
        # Get messages in batches
        all_messages = []
        batch_size = settings.MAX_MESSAGES_PER_REQUEST
        
        while True:
            batch = self.get_chat_history(
                chat_id=chat_id,
                count=batch_size,
                message_type=message_type,
                min_timestamp=min_timestamp
            )
            
            if not batch:
                break
                
            all_messages.extend(batch)
            
            # Check if we've reached the date range
            oldest_timestamp = min(msg.get('timestamp', float('inf')) for msg in batch)
            if oldest_timestamp < min_timestamp:
                break
                
        print(f"✅ Retrieved {len(all_messages)} total messages")
        return all_messages

    def get_outgoing_messages(self, chat_id: str = None, minutes: int = 1440) -> List[Dict]:
        """Get outgoing messages from last N minutes (default 24 hours)"""
        # Try multiple possible endpoints
        possible_urls = [
            f"lastOutgoingMessages/{self.api_token}",
            f"LastOutgoingMessages/{self.api_token}",
            f"getLastOutgoingMessages/{self.api_token}"
        ]
        
        all_outgoing = []
        
        for endpoint in possible_urls:
            print(f"🔄 Trying outgoing messages endpoint: {endpoint}")
            
            try:
                # Try GET method
                response = self._make_request("GET", endpoint, params={"minutes": minutes})
                if "error" not in response:
                    all_outgoing = response
                    break
                    
                # Try POST method
                response = self._make_request("POST", endpoint, data={"minutes": minutes})
                if "error" not in response:
                    all_outgoing = response
                    break
                    
            except Exception as e:
                print(f"Error with {endpoint}: {e}")
                continue
        
        if not all_outgoing:
            print("⚠️ No outgoing messages found")
            return []
        
        # Filter by chat_id if specified
        if chat_id:
            filtered_messages = []
            for msg in all_outgoing:
                msg_chat_id = msg.get('chatId') or msg.get('chat_id') or msg.get('to')
                if msg_chat_id == chat_id:
                    filtered_messages.append(msg)
            
            print(f"🔍 Filtered to {len(filtered_messages)} messages for chat {chat_id}")
            return filtered_messages
        
        return all_outgoing

    def get_combined_messages(self, chat_id: str, hours_back: int = 48) -> List[Dict]:
        """Get both incoming and outgoing messages combined"""
        print(f"🔄 Getting combined messages for last {hours_back} hours")
        
        # Get incoming messages
        incoming = self.get_chat_history(
            chat_id=chat_id,
            count=1000,
            message_type="incoming",
            min_timestamp=int((datetime.now() - timedelta(hours=hours_back)).timestamp())
        )
        
        # Get outgoing messages
        outgoing = self.get_outgoing_messages(chat_id, hours_back * 60)
        
        # Combine and sort
        all_messages = incoming + outgoing
        all_messages.sort(key=lambda x: x.get('timestamp', 0))
        
        print(f"📊 Combined results:")
        print(f"   📥 Incoming: {len(incoming)}")
        print(f"   📤 Outgoing: {len(outgoing)}")
        print(f"   📋 Total: {len(all_messages)}")
        
        return all_messages

    def send_message(self, chat_id: str, message: str) -> dict:
        """Send message to WhatsApp chat"""
        # Check test mode
        if os.getenv("TESTING_MODE") == "true":
            print(f"\n🧪 TEST MODE - Would send to: {chat_id}")
            print(f"📱 Message preview:")
            print("-" * 40)
            print(message)
            print("-" * 40)
            return {"success": True, "test_mode": True}
            
        endpoint = f"sendMessage/{self.api_token}"
        data = {
            "chatId": chat_id,
            "message": message
        }
        return self._make_request("POST", endpoint, data=data)

    def get_notification(self) -> Optional[Dict]:
        """Get next notification from the queue"""
        endpoint = f"receiveNotification/{self.api_token}"
        return self._make_request("GET", endpoint)

    def delete_notification(self, receipt_id: int) -> bool:
        """Delete a notification from the queue"""
        endpoint = f"deleteNotification/{self.api_token}/{receipt_id}"
        result = self._make_request("DELETE", endpoint)
        return "error" not in result

    def get_chat_info(self, chat_id: str) -> dict:
        """Get information about a chat"""
        endpoint = f"getChatInfo/{self.api_token}"
        data = {"chatId": chat_id}
        return self._make_request("POST", endpoint, data=data)

    def get_message_stats(self, chat_id: str, days: int = 7) -> dict:
        """Get message statistics for a chat"""
        start_date = datetime.now() - timedelta(days=days)
        messages = self.get_messages_by_date_range(chat_id, start_date)
        
        stats = {
            "total_messages": len(messages),
            "message_types": {},
            "senders": {},
            "hourly_activity": {str(h): 0 for h in range(24)}
        }
        
        for msg in messages:
            # Count by type
            msg_type = msg.get('type', 'unknown')
            stats["message_types"][msg_type] = stats["message_types"].get(msg_type, 0) + 1
            
            # Count by sender
            sender = msg.get('senderData', {}).get('sender', 'unknown')
            stats["senders"][sender] = stats["senders"].get(sender, 0) + 1
            
            # Count by hour
            if msg.get('timestamp'):
                hour = datetime.fromtimestamp(msg['timestamp']).hour
                stats["hourly_activity"][str(hour)] += 1
        
        return stats