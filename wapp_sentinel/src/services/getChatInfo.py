import requests
import json

# Replace with your GreenAPI credentials
GREEN_API_ID_INSTANCE = "7105242930"
GREEN_API_TOKEN = "6e6a238888e0439490087474fbcf53dfa378df90300d4793a3"

def get_all_chats():
    """Get all chats from GreenAPI"""
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/getChats/{GREEN_API_TOKEN}"
    
    try:
        response = requests.post(url)
        response.raise_for_status()
        chats = response.json()
        for chat in chats:
            if chat['id'].endswith('@g.us'):
                print(f"Name: {chat.get('name', 'No Name')}")
                print(f"Chat ID: {chat['id']}")
                print("-" * 50)
        # print("=== ALL CHATS ===")
        # for chat in chats:
        #     chat_type = "GROUP" if chat['id'].endswith('@g.us') else "INDIVIDUAL"
        #     print(f"Name: {chat.get('name', 'No Name')}")
        #     print(f"Chat ID: {chat['id']}")
        #     print(f"Type: {chat_type}")
        #     print("-" * 50)
            
        return chats
    except Exception as e:
        print(f"Error getting chats: {e}")
        return []

if __name__ == "__main__":
    get_all_chats()