import requests
import os
from dotenv import load_dotenv

load_dotenv()

GREEN_API_ID_INSTANCE = os.getenv("GREEN_API_ID_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")

def fix_greenapi_settings():
    """Enable proper settings for message capture"""
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/setSettings/{GREEN_API_TOKEN}"
    
    # Enable necessary settings for polling mode
    settings = {
        "incomingWebhook": "yes",           # Enable incoming message capture
        "outgoingWebhook": "yes",           # Enable outgoing message capture  
        "enableMessagesHistory": "yes",      # Enable message history
        "markIncomingMessagesReaded": "no",  # Don't auto-mark as read
        "webhookUrl": "",                   # Keep empty for polling
        "webhookUrlToken": ""               # Keep empty for polling
    }
    
    try:
        response = requests.post(url, json=settings)
        print(f"Settings update response: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ Settings updated successfully!")
            print("Now try sending a message and checking notifications again.")
            return True
        else:
            print(f"❌ Failed to update settings: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error updating settings: {e}")
        return False

def get_chat_history(chat_id: str, count: int = 5):
    """Get recent messages from a specific chat"""
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/getChatHistory/{GREEN_API_TOKEN}"
    
    payload = {
        "chatId": chat_id,
        "count": count
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"\n=== CHAT HISTORY ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return None

def restart_greenapi_instance():
    """Restart the GreenAPI instance to apply new settings"""
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/reboot/{GREEN_API_TOKEN}"
    
    try:
        response = requests.get(url)
        print(f"\n=== INSTANCE RESTART ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Instance restart initiated. Wait 30 seconds before testing.")
            return True
        else:
            print("❌ Failed to restart instance")
            return False
    except Exception as e:
        print(f"Error restarting instance: {e}")
        return False

if __name__ == "__main__":
    MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")
    
    print("=== FIXING GREENAPI SETTINGS ===")
    
    # Step 1: Update settings
    if fix_greenapi_settings():
        print("\n⏳ Waiting 5 seconds for settings to apply...")
        import time
        time.sleep(5)
        
        # Step 2: Check chat history (alternative to notifications)
        print(f"\n=== CHECKING RECENT MESSAGES ===")
        history = get_chat_history(MAIN_GROUP_CHAT_ID)
        
        # Step 3: Restart instance for good measure
        restart_choice = input("\nRestart GreenAPI instance for fresh start? (y/n): ")
        if restart_choice.lower() == 'y':
            restart_greenapi_instance()
        
        print("\n=== NEXT STEPS ===")
        print("1. Wait 30 seconds if you restarted the instance")
        print("2. Send a fresh test message to your WhatsApp group")
        print("3. Run: python debug_greenapi.py")
        print("4. If still no notifications, we'll use chat history method instead")
    else:
        print("❌ Failed to update settings. Check your credentials.")