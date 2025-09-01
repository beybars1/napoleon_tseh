#!/usr/bin/env python3
"""
Test the final fix - should now show outgoing messages
"""

import sys
import os
from datetime import datetime

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from greenapi_service import get_all_available_messages
from dotenv import load_dotenv

load_dotenv()

MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")

def test_final_fix():
    """Test that we now get both incoming and outgoing messages"""
    print("🎯 TESTING FINAL FIX")
    print("=" * 50)
    
    if not MAIN_GROUP_CHAT_ID:
        print("❌ MAIN_GROUP_CHAT_ID not set!")
        return
    
    print(f"Testing with chat ID: {MAIN_GROUP_CHAT_ID}")
    
    # Test get_all_available_messages (no time filtering)
    print("\n📥 Testing get_all_available_messages (no time filtering)...")
    all_messages = get_all_available_messages(MAIN_GROUP_CHAT_ID)
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"Total messages: {len(all_messages)}")
    
    if all_messages:
        type_counts = {}
        for msg in all_messages:
            msg_type = msg.get('type', 'unknown')
            type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
        
        print(f"Message types: {type_counts}")
        
        # Show samples of each type
        print(f"\n📋 Sample messages:")
        
        # Show incoming samples
        incoming_msgs = [msg for msg in all_messages if msg.get('type') == 'incoming'][:3]
        if incoming_msgs:
            print(f"📨 Incoming samples:")
            for i, msg in enumerate(incoming_msgs):
                timestamp = msg.get('timestamp', 0)
                msg_time = datetime.fromtimestamp(timestamp).strftime('%m-%d %H:%M') if timestamp else 'Unknown'
                text = str(msg.get('textMessage', ''))[:40] + "..." if len(str(msg.get('textMessage', ''))) > 40 else str(msg.get('textMessage', ''))
                print(f"   {i+1}. [{msg_time}] {text}")
        
        # Show outgoing samples
        outgoing_msgs = [msg for msg in all_messages if msg.get('type') == 'outgoing'][:3]
        if outgoing_msgs:
            print(f"📤 Outgoing samples:")
            for i, msg in enumerate(outgoing_msgs):
                timestamp = msg.get('timestamp', 0)
                msg_time = datetime.fromtimestamp(timestamp).strftime('%m-%d %H:%M') if timestamp else 'Unknown'
                text = str(msg.get('textMessage', ''))[:40] + "..." if len(str(msg.get('textMessage', ''))) > 40 else str(msg.get('textMessage', ''))
                print(f"   {i+1}. [{msg_time}] {text}")
        else:
            print("❌ Still no outgoing messages found!")
            print("   This means your bakery hasn't sent any messages to this group recently.")
            print("   Try sending a test message from your WhatsApp to the group, then run this again.")
    
    return all_messages

if __name__ == "__main__":
    result = test_final_fix()
    
    if result:
        outgoing_count = len([msg for msg in result if msg.get('type') == 'outgoing'])
        if outgoing_count > 0:
            print(f"\n🎉 SUCCESS! Found {outgoing_count} outgoing messages!")
            print("✅ The fix is working - you should now see both incoming and outgoing messages in your API!")
        else:
            print(f"\n⚠️  Still no outgoing messages, but this might be expected if:")
            print("   1. Your bakery hasn't sent messages to this group recently")
            print("   2. All outgoing messages are very old")
            print("   3. You're using a different phone number for sending")
    else:
        print(f"\n❌ No messages retrieved at all - check your API configuration")
