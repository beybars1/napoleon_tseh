import os
import requests
from dotenv import load_dotenv

load_dotenv()

GREEN_API_ID_INSTANCE = os.getenv("GREEN_API_ID_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")

print("=== GREENAPI DEBUG ===")
print(f"Instance ID: {GREEN_API_ID_INSTANCE}")
print(f"Token: {GREEN_API_TOKEN[:10]}..." if GREEN_API_TOKEN else "Token: None")
print(f"Main Group Chat ID: {MAIN_GROUP_CHAT_ID}")

def test_greenapi_connection():
    """Test basic GreenAPI connection"""
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/getStateInstance/{GREEN_API_TOKEN}"
    
    try:
        response = requests.get(url)
        print(f"\n=== CONNECTION TEST ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Connection Error: {e}")
        return False

def check_notifications():
    """Check for notifications"""
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/receiveNotification/{GREEN_API_TOKEN}"
    
    try:
        response = requests.get(url)
        print(f"\n=== NOTIFICATIONS CHECK ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data is None:
                print("No pending notifications")
            else:
                print(f"Found notification: {data}")
                
    except Exception as e:
        print(f"Notifications Error: {e}")

def check_webhook_settings():
    """Check webhook settings"""
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/getSettings/{GREEN_API_TOKEN}"
    
    try:
        response = requests.get(url)
        print(f"\n=== WEBHOOK SETTINGS ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Settings Error: {e}")

if __name__ == "__main__":
    if not all([GREEN_API_ID_INSTANCE, GREEN_API_TOKEN, MAIN_GROUP_CHAT_ID]):
        print("ERROR: Missing environment variables!")
        print("Please check your .env file")
    else:
        test_greenapi_connection()
        check_notifications()
        check_webhook_settings()
        
        print("\n=== NEXT STEPS ===")
        print("1. If connection failed: Check your GreenAPI credentials")
        print("2. If no notifications: Send a test message to your main group")
        print("3. If webhook not set: You might need to configure webhook URL")
        print("4. Try running this script again after sending a test message")