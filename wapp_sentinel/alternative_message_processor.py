import requests
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import json
from datetime import datetime

from database import get_db, Order
from openai_service import parse_order

load_dotenv()

GREEN_API_ID_INSTANCE = os.getenv("GREEN_API_ID_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")

def get_chat_history(chat_id: str, count: int = 10):
    """Get recent messages from chat using getChatHistory"""
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/getChatHistory/{GREEN_API_TOKEN}"
    
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

def process_chat_history():
    """Process recent messages from chat history"""
    db = next(get_db())
    
    try:
        print("Getting chat history...")
        messages = get_chat_history(MAIN_GROUP_CHAT_ID)
        
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
                chat_id=MAIN_GROUP_CHAT_ID,
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
    finally:
        db.close()

if __name__ == "__main__":
    process_chat_history()