import requests
from sqlalchemy.orm import Session
import json
from datetime import datetime

from ..core.config import settings
from ..core.database import get_db, Order
from ..services.openai_service import parse_order

class AlternativeMessageProcessor:
    def __init__(self):
        self.green_api_id = settings.GREEN_API_ID_INSTANCE
        self.green_api_token = settings.GREEN_API_TOKEN
        self.main_group_chat_id = settings.MAIN_GROUP_CHAT_ID

    def get_chat_history(self, chat_id: str, count: int = 10):
        """Get recent messages from chat using getChatHistory"""
        url = f"https://api.green-api.com/waInstance{self.green_api_id}/getChatHistory/{self.green_api_token}"
        
        payload = {
            "chatId": chat_id,
            "count": count
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting chat history: {response.text}")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def process_chat_history(self):
        """Process recent messages from chat history"""
        db = next(get_db())
        
        try:
            print("Getting chat history...")
            messages = self.get_chat_history(self.main_group_chat_id)
            
            if not messages:
                print("No messages found")
                return
            
            print(f"Found {len(messages)} messages")
            
            for msg in messages:
                # Skip if not a text message
                if msg.get('type') != 'textMessage':
                    continue
                    
                message_id = msg.get('idMessage')
                message_text = msg.get('textMessage', '')
                sender = msg.get('chatId')  # This contains sender info
                
                print(f"Processing message: {message_text[:50]}...")
                
                # Check if already processed
                existing = db.query(Order).filter(Order.message_id == message_id).first()
                if existing:
                    print("Already processed, skipping")
                    continue
                
                # Parse with OpenAI
                parsed_data = parse_order(message_text)
                print(f"Parsed result: {parsed_data.get('is_order', False)}")
                
                # Save to database
                order = Order(
                    message_id=message_id,
                    chat_id=self.main_group_chat_id,
                    sender=sender,
                    raw_message=message_text,
                    parsed_data=json.dumps(parsed_data),
                    order_date=parsed_data.get("order_date") if parsed_data.get("is_order") else None,
                    customer_name=parsed_data.get("customer_name") if parsed_data.get("is_order") else None,
                    total_amount=parsed_data.get("total_amount") if parsed_data.get("is_order") else None,
                    delivery_time=parsed_data.get("delivery_time") if parsed_data.get("is_order") else None,
                    processed=not parsed_data.get("is_order", False)
                )
                
                db.add(order)
                db.commit()
                print("Saved to database")
            
            print("Processing complete!")
            
        except Exception as e:
            print(f"Error processing chat history: {e}")
            db.rollback()
        finally:
            db.close()