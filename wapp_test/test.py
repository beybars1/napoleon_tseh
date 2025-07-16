"""
WhatsApp Business Data Extractor using Green API
This script connects to your WhatsApp Business account via Green API
and extracts chat messages and other data.
"""

import os
import json
import time
import pandas as pd
from datetime import datetime
from whatsapp_api_client_python import GreenAPI

# Configuration
INSTANCE_ID = "7105242930"  # Replace with your Green API Instance ID
API_TOKEN = ""      # Replace with your Green API Token

def connect_to_green_api():
    """Initialize and return the Green API client"""
    print("Connecting to Green API...")
    green_api = GreenAPI(INSTANCE_ID, API_TOKEN)
    return green_api

def check_auth_status(green_api):
    """Check if the WhatsApp account is authenticated with Green API"""
    state = green_api.account.getStateInstance()
    
    if state.code == 200 and state.data['stateInstance'] == 'authorized':
        print("✅ Account is authorized and ready")
        return True
    else:
        print("❌ Account is not authorized. Current state:", state.data['stateInstance'])
        print("Please ensure you've scanned the QR code in your Green API account dashboard")
        return False

def get_chats(green_api):
    """Retrieve list of chats"""
    print("Retrieving chat list...")
    chats_response = green_api.account.getContacts()
    
    if chats_response.code == 200:
        chats = chats_response.data
        print(f"Found {len(chats)} chats")
        return chats
    else:
        print(f"Failed to get chats: {chats_response.code}")
        return []

def get_chat_history(green_api, chat_id, count=100):
    """Retrieve message history for a specific chat"""
    print(f"Retrieving message history for {chat_id}...")
    
    # Get chat history
    history_response = green_api.messages.getChatHistory(
        chatId=chat_id,
        count=count
    )
    
    if history_response.code == 200:
        messages = history_response.data
        print(f"Retrieved {len(messages)} messages")
        return messages
    else:
        print(f"Failed to get chat history: {history_response.code}")
        return []

def process_messages(messages):
    """Process and structure message data"""
    processed_data = []
    
    for msg in messages:
        try:
            # Skip system messages or messages without proper structure
            if 'messageData' not in msg or 'textMessageData' not in msg.get('messageData', {}):
                continue
                
            # Extract basic information
            message_info = {
                'message_id': msg.get('idMessage'),
                'timestamp': msg.get('timestamp'),
                'datetime': datetime.fromtimestamp(msg.get('timestamp')).strftime('%Y-%m-%d %H:%M:%S'),
                'chat_id': msg.get('chatId'),
                'sender': msg.get('senderName', 'Unknown'),
                'type': msg.get('type'),
                'message': msg.get('messageData', {}).get('textMessageData', {}).get('textMessage', ''),
            }
            
            processed_data.append(message_info)
        except Exception as e:
            print(f"Error processing message: {e}")
            continue
    
    return processed_data

def save_to_csv(data, filename="whatsapp_messages.csv"):
    """Save processed messages to CSV file"""
    if not data:
        print("No data to save")
        return
        
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

def main():
    # Connect to Green API
    green_api = connect_to_green_api()
    
    # Check authentication status
    if not check_auth_status(green_api):
        return
    
    # Get all chats
    chats = get_chats(green_api)
    
    if not chats:
        return
    
    # Display available chats
    print("\nAvailable Chats:")
    for i, chat in enumerate(chats):
        print(f"{i+1}. {chat.get('name', 'Unknown')} - {chat.get('id')}")
    
    # Get user selection
    try:
        selection = int(input("\nEnter the number of the chat to extract (0 for all): "))
        
        all_messages = []
        
        if selection == 0:
            # Process all chats
            for chat in chats:
                chat_id = chat.get('id')
                messages = get_chat_history(green_api, chat_id)
                processed = process_messages(messages)
                all_messages.extend(processed)
        else:
            # Process selected chat
            selected_chat = chats[selection-1]
            chat_id = selected_chat.get('id')
            messages = get_chat_history(green_api, chat_id)
            all_messages = process_messages(messages)
        
        # Save data to CSV
        save_to_csv(all_messages)
        
    except (ValueError, IndexError) as e:
        print(f"Invalid selection: {e}")

if __name__ == "__main__":
    main()