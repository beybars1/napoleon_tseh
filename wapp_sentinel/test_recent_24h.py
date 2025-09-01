#!/usr/bin/env python3
"""
Focused test for recent 24h messages
This will help us understand why outgoing messages from last 24h are missing
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

GREEN_API_ID_INSTANCE = os.getenv("GREEN_API_ID_INSTANCE")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")

BASE_URL = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}"

def analyze_message_timestamps():
    """Get all messages and analyze their timestamps in detail"""
    print("🕐 ANALYZING MESSAGE TIMESTAMPS")
    print("=" * 40)
    
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    payload = {"chatId": MAIN_GROUP_CHAT_ID, "count": 1000}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"❌ API Error: {response.text}")
            return
        
        messages = response.json() or []
        print(f"📥 Retrieved {len(messages)} total messages")
        
        # Current time info
        now = datetime.now()
        now_ts = int(now.timestamp())
        cutoff_24h = now - timedelta(hours=24)
        cutoff_24h_ts = int(cutoff_24h.timestamp())
        cutoff_48h = now - timedelta(hours=48)
        cutoff_48h_ts = int(cutoff_48h.timestamp())
        
        print(f"\n🕐 Time Analysis:")
        print(f"   Current time: {now.strftime('%Y-%m-%d %H:%M:%S')} ({now_ts})")
        print(f"   24h ago: {cutoff_24h.strftime('%Y-%m-%d %H:%M:%S')} ({cutoff_24h_ts})")
        print(f"   48h ago: {cutoff_48h.strftime('%Y-%m-%d %H:%M:%S')} ({cutoff_48h_ts})")
        
        # Analyze by time periods
        periods = {
            "last_24h": {"incoming": [], "outgoing": []},
            "24h_to_48h": {"incoming": [], "outgoing": []},
            "older": {"incoming": [], "outgoing": []}
        }
        
        no_timestamp = []
        
        for msg in messages:
            msg_type = msg.get('type', 'unknown')
            timestamp = msg.get('timestamp', 0)
            
            if not timestamp:
                no_timestamp.append(msg)
                continue
            
            if msg_type not in ['incoming', 'outgoing']:
                continue
            
            if timestamp >= cutoff_24h_ts:
                periods["last_24h"][msg_type].append(msg)
            elif timestamp >= cutoff_48h_ts:
                periods["24h_to_48h"][msg_type].append(msg)
            else:
                periods["older"][msg_type].append(msg)
        
        # Print analysis
        print(f"\n📊 MESSAGE BREAKDOWN BY TIME:")
        for period, data in periods.items():
            total_incoming = len(data["incoming"])
            total_outgoing = len(data["outgoing"])
            print(f"\n  {period}:")
            print(f"    📨 Incoming: {total_incoming}")
            print(f"    📤 Outgoing: {total_outgoing}")
            
            # Show samples from each type
            if data["incoming"]:
                print(f"    📨 Sample incoming:")
                for i, msg in enumerate(data["incoming"][:2]):
                    ts = msg.get('timestamp', 0)
                    dt = datetime.fromtimestamp(ts).strftime('%m-%d %H:%M:%S')
                    text = str(msg.get('textMessage', ''))[:40]
                    print(f"      {i+1}. [{dt}] {text}")
            
            if data["outgoing"]:
                print(f"    📤 Sample outgoing:")
                for i, msg in enumerate(data["outgoing"][:2]):
                    ts = msg.get('timestamp', 0)
                    dt = datetime.fromtimestamp(ts).strftime('%m-%d %H:%M:%S')
                    text = str(msg.get('textMessage', ''))[:40]
                    print(f"      {i+1}. [{dt}] {text}")
        
        if no_timestamp:
            print(f"\n⚠️  {len(no_timestamp)} messages without timestamps")
        
        # Key findings
        print(f"\n🎯 KEY FINDINGS:")
        recent_outgoing = len(periods["last_24h"]["outgoing"])
        if recent_outgoing > 0:
            print(f"✅ Found {recent_outgoing} outgoing messages in last 24h!")
            print("   → The issue is NOT with time filtering")
            print("   → The issue is with our code logic")
        else:
            print(f"❌ No outgoing messages in last 24h")
            print("   → Check if you actually sent messages to this group recently")
            print("   → Or the issue might be with webhook settings")
        
        return periods
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_exact_api_call():
    """Test the exact same API call our code makes"""
    print("\n🔬 TESTING EXACT API CALL FROM OUR CODE")
    print("=" * 45)
    
    # Replicate exactly what our get_recent_messages does
    url = f"{BASE_URL}/getChatHistory/{GREEN_API_TOKEN}"
    
    # Calculate cutoff like our code does
    cutoff_time = datetime.now() - timedelta(hours=24)
    cutoff_timestamp = int(cutoff_time.timestamp())
    
    payload = {
        "chatId": MAIN_GROUP_CHAT_ID,
        "count": 1000
    }
    
    print(f"🔄 Making API call...")
    print(f"   URL: {url}")
    print(f"   Payload: {payload}")
    print(f"   Cutoff time: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')} ({cutoff_timestamp})")
    
    try:
        response = requests.post(url, json=payload)
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ Error: {response.text}")
            return
        
        messages = response.json() or []
        print(f"   📥 Retrieved: {len(messages)} messages")
        
        # Apply same filtering as our code
        recent_messages = []
        filtered_out = []
        
        for msg in messages:
            msg_timestamp = msg.get('timestamp', 0)
            if msg_timestamp >= cutoff_timestamp:
                recent_messages.append(msg)
            else:
                filtered_out.append(msg)
        
        print(f"\n📊 FILTERING RESULTS:")
        print(f"   ✅ Kept: {len(recent_messages)}")
        print(f"   ❌ Filtered out: {len(filtered_out)}")
        
        # Analyze what was kept
        kept_types = {}
        for msg in recent_messages:
            msg_type = msg.get('type', 'unknown')
            kept_types[msg_type] = kept_types.get(msg_type, 0) + 1
        print(f"   Kept types: {kept_types}")
        
        # Analyze what was filtered out
        filtered_types = {}
        for msg in filtered_out:
            msg_type = msg.get('type', 'unknown')
            filtered_types[msg_type] = filtered_types.get(msg_type, 0) + 1
        print(f"   Filtered types: {filtered_types}")
        
        # Show why outgoing were filtered
        if filtered_types.get('outgoing', 0) > 0:
            print(f"\n🔍 WHY OUTGOING MESSAGES WERE FILTERED:")
            outgoing_filtered = [msg for msg in filtered_out if msg.get('type') == 'outgoing'][:3]
            for i, msg in enumerate(outgoing_filtered):
                ts = msg.get('timestamp', 0)
                dt = datetime.fromtimestamp(ts)
                hours_old = (datetime.now() - dt).total_seconds() / 3600
                print(f"   {i+1}. Timestamp: {ts} ({dt.strftime('%Y-%m-%d %H:%M:%S')}) - {hours_old:.1f}h old")
        
        return recent_messages
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def main():
    print("🎯 FOCUSED 24H MESSAGE ANALYSIS")
    print("=" * 50)
    
    if not all([GREEN_API_ID_INSTANCE, GREEN_API_TOKEN, MAIN_GROUP_CHAT_ID]):
        print("❌ Missing environment variables!")
        return
    
    # Run analysis
    periods = analyze_message_timestamps()
    recent_from_api = test_exact_api_call()
    
    print(f"\n🎯 FINAL CONCLUSION:")
    if periods and len(periods["last_24h"]["outgoing"]) > 0:
        print("✅ You DO have outgoing messages in the last 24 hours")
        print("❌ But our filtering code is removing them")
        print("🔧 Need to debug the timestamp comparison logic")
    elif periods:
        print("❌ You have NO outgoing messages in the last 24 hours")
        print("💡 Either:")
        print("   1. You haven't sent messages to this group recently")
        print("   2. Webhook settings are not capturing outgoing messages")
        print("   3. Your messages are being sent from a different number")
    
    if recent_from_api is not None:
        outgoing_in_filtered = len([m for m in recent_from_api if m.get('type') == 'outgoing'])
        if outgoing_in_filtered > 0:
            print(f"✅ After our exact filtering: {outgoing_in_filtered} outgoing messages remain")
        else:
            print(f"❌ After our exact filtering: 0 outgoing messages remain")

if __name__ == "__main__":
    main()
