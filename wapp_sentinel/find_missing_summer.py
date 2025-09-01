#!/usr/bin/env python3
"""
Simple script to find what happened to June-August 2025 messages
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GREEN_API_ID_INSTANCE = os.getenv("GREEN_API_ID_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")

def find_missing_summer():
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/getChatHistory/{GREEN_API_TOKEN}"
    
    print("🔍 LOOKING FOR MISSING SUMMER MESSAGES")
    print("=" * 50)
    
    # Try getting more messages
    for count in [100, 500, 1000, 2000]:
        print(f"\n📊 Trying count={count}:")
        
        payload = {
            "chatId": MAIN_GROUP_CHAT_ID,
            "count": count
        }
        
        try:
            response = requests.post(url, json=payload)
            messages = response.json() or []
            
            print(f"   📥 Got {len(messages)} messages")
            
            # Look for summer months
            june_count = 0
            july_count = 0
            august_count = 0
            
            for msg in messages:
                timestamp = msg.get('timestamp', 0)
                if timestamp:
                    dt = datetime.fromtimestamp(timestamp)
                    
                    if dt.year == 2025:
                        if dt.month == 6:  # June
                            june_count += 1
                        elif dt.month == 7:  # July
                            july_count += 1
                        elif dt.month == 8:  # August (before 31st)
                            if dt.day < 31:  # Exclude the 2 recent messages
                                august_count += 1
            
            print(f"   🌞 Summer 2025 messages:")
            print(f"      June: {june_count}")
            print(f"      July: {july_count}")
            print(f"      August (1-30): {august_count}")
            
            if june_count > 0 or july_count > 0 or august_count > 0:
                print("   ✅ Found summer messages!")
                break
            else:
                print("   ❌ No summer messages found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Show message timeline
    print(f"\n📅 MESSAGE TIMELINE ANALYSIS:")
    
    try:
        payload = {"chatId": MAIN_GROUP_CHAT_ID, "count": 1000}
        response = requests.post(url, json=payload)
        messages = response.json() or []
        
        # Group by month
        monthly = {}
        
        for msg in messages:
            timestamp = msg.get('timestamp', 0)
            if timestamp:
                dt = datetime.fromtimestamp(timestamp)
                month_key = f"{dt.year}-{dt.month:02d}"
                
                if month_key not in monthly:
                    monthly[month_key] = 0
                monthly[month_key] += 1
        
        print("Month     | Messages")
        print("-" * 20)
        for month in sorted(monthly.keys()):
            print(f"{month}     | {monthly[month]:8d}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_missing_summer()
