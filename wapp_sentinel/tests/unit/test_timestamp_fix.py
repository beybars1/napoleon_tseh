#!/usr/bin/env python3
"""
Test the timestamp filtering fix
"""

import sys
import os
from datetime import datetime

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from greenapi_service import get_recent_messages
from dotenv import load_dotenv

load_dotenv()

MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")

def test_timestamp_fix():
    """Test the enhanced timestamp debugging"""
    print("🧪 TESTING TIMESTAMP FILTERING FIX")
    print("=" * 50)
    
    if not MAIN_GROUP_CHAT_ID:
        print("❌ MAIN_GROUP_CHAT_ID not set!")
        return
    
    print(f"Testing with chat ID: {MAIN_GROUP_CHAT_ID}")
    
    # Test with 24 hours - should now show detailed timestamp debug info
    print("\n🕐 Testing get_recent_messages with enhanced debugging...")
    recent = get_recent_messages(MAIN_GROUP_CHAT_ID, 24)
    
    print(f"\n📊 RESULTS:")
    print(f"Total messages after filtering: {len(recent)}")
    
    if recent:
        type_counts = {}
        for msg in recent:
            msg_type = msg.get('type', 'unknown')
            type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
        print(f"Message types: {type_counts}")
        
        # Show recent messages with timestamps
        print(f"\n📋 Sample filtered messages:")
        for i, msg in enumerate(recent[:5]):
            msg_type = msg.get('type', 'unknown')
            timestamp = msg.get('timestamp', 0)
            if timestamp:
                msg_time = datetime.fromtimestamp(timestamp)
                hours_ago = (datetime.now() - msg_time).total_seconds() / 3600
                print(f"   {i+1}. {msg_type} - {msg_time.strftime('%Y-%m-%d %H:%M:%S')} ({hours_ago:.1f}h ago)")
            else:
                print(f"   {i+1}. {msg_type} - No timestamp")
    
    print(f"\n💡 If you see detailed debug output above showing filtered out outgoing messages,")
    print(f"   then we've identified the timestamp issue and can fix it!")

if __name__ == "__main__":
    test_timestamp_fix()
