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

def get_chat_history(chat_id: str, count: int = 3):
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

def debug_process():
    """Debug message processing step by step"""
    db = next(get_db())
    
    try:
        print("=== DEBUGGING MESSAGE PROCESSING ===")
        
        # Test database connection
        print("\n1. Testing database connection...")
        existing_count = db.query(Order).count()
        print(f"   Current orders in database: {existing_count}")
        
        # Get messages
        print("\n2. Getting chat history...")
        messages = get_chat_history(MAIN_GROUP_CHAT_ID, 3)  # Just get 3 for testing
        
        if not messages:
            print("   No messages found!")
            return
        
        print(f"   Found {len(messages)} messages")
        
        # Process each message with detailed logging
        for i, msg in enumerate(messages[:2]):  # Just process 2 messages
            print(f"\n=== PROCESSING MESSAGE {i+1} ===")
            
            # Check message type - accept both textMessage and outgoing types
            msg_type = msg.get('type')
            type_message = msg.get('typeMessage')
            
            print(f"   Message type: {msg_type}")
            print(f"   Type message: {type_message}")
            
            # Skip if not a text message
            if type_message != 'textMessage':
                print(f"   Skipping: not a text message (typeMessage: {type_message})")
                continue
            
            message_id = msg.get('idMessage')
            message_text = msg.get('textMessage', '')
            
            print(f"   Message ID: {message_id}")
            print(f"   Message text: {message_text}")
            
            # Check if already exists
            existing = db.query(Order).filter(Order.message_id == message_id).first()
            if existing:
                print(f"   Already processed - skipping")
                continue
            
            # Test OpenAI parsing
            print("\n   Testing OpenAI parsing...")
            try:
                parsed_data = parse_order(message_text)
                print(f"   OpenAI result: {json.dumps(parsed_data, indent=2, ensure_ascii=False)}")
                
                if not parsed_data:
                    print("   ERROR: OpenAI returned None/empty")
                    continue
                    
            except Exception as e:
                print(f"   ERROR parsing with OpenAI: {e}")
                continue
            
            # Try to save to database
            print("\n   Saving to database...")
            try:
                order = Order(
                    message_id=message_id,
                    chat_id=MAIN_GROUP_CHAT_ID,
                    sender=msg.get('chatId', ''),
                    raw_message=message_text,
                    parsed_data=json.dumps(parsed_data, ensure_ascii=False),
                    order_date=parsed_data.get("order_date") if parsed_data.get("is_order") else None,
                    customer_name=parsed_data.get("customer_name") if parsed_data.get("is_order") else None,
                    total_amount=parsed_data.get("total_amount") if parsed_data.get("is_order") else None,
                    delivery_time=parsed_data.get("delivery_time") if parsed_data.get("is_order") else None,
                    processed=not parsed_data.get("is_order", False)
                )
                
                db.add(order)
                db.commit()
                print("   ✅ Successfully saved to database!")
                
                # Verify it was saved
                saved_order = db.query(Order).filter(Order.message_id == message_id).first()
                if saved_order:
                    print(f"   ✅ Verified: Order ID {saved_order.id} in database")
                else:
                    print("   ❌ ERROR: Order not found after saving!")
                
            except Exception as e:
                print(f"   ❌ ERROR saving to database: {e}")
                db.rollback()
                continue
        
        # Final count
        final_count = db.query(Order).count()
        print(f"\n=== FINAL RESULTS ===")
        print(f"Orders in database: {final_count}")
        print(f"New orders added: {final_count - existing_count}")
        
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_process()