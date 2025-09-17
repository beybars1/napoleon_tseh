#!/usr/bin/env python3
"""
Simple direct test of outgoing message functionality
Run this before starting the FastAPI server to debug
"""

import sys
import os
from datetime import datetime

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from greenapi_service import get_recent_messages, get_outgoing_messages, get_combined_messages
from dotenv import load_dotenv

load_dotenv()

MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")

def test_direct():
    """Test the functions directly"""
    print("🧪 DIRECT FUNCTION TESTING")
    print("=" * 50)
    
    if not MAIN_GROUP_CHAT_ID:
        print("❌ MAIN_GROUP_CHAT_ID not set!")
        return
    
    print(f"Testing with chat ID: {MAIN_GROUP_CHAT_ID}")
    
    # Test 1: Recent messages (should include both types)
    print("\n1️⃣ Testing get_recent_messages (24 hours)...")
    recent = get_recent_messages(MAIN_GROUP_CHAT_ID, 24)
    
    # Test 2: Outgoing messages specifically
    print("\n2️⃣ Testing get_outgoing_messages (24 hours)...")
    outgoing = get_outgoing_messages(MAIN_GROUP_CHAT_ID, 1440)  # 24 hours in minutes
    
    # Test 3: Combined messages
    print("\n3️⃣ Testing get_combined_messages (24 hours)...")
    combined = get_combined_messages(MAIN_GROUP_CHAT_ID, 24)
    
    # Summary
    print("\n📊 SUMMARY")
    print("=" * 30)
    print(f"Recent messages: {len(recent)}")
    if recent:
        recent_types = {}
        for msg in recent:
            msg_type = msg.get('type', 'unknown')
            recent_types[msg_type] = recent_types.get(msg_type, 0) + 1
        print(f"  Types: {recent_types}")
    
    print(f"Outgoing messages: {len(outgoing)}")
    print(f"Combined messages: {len(combined)}")
    
    if combined:
        combined_types = {}
        for msg in combined:
            msg_type = msg.get('type', 'unknown')
            combined_types[msg_type] = combined_types.get(msg_type, 0) + 1
        print(f"  Combined types: {combined_types}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if not outgoing and not any(msg.get('type') == 'outgoing' for msg in recent):
        print("❌ No outgoing messages found. Possible causes:")
        print("   1. You haven't sent any WhatsApp messages recently (last 24h)")
        print("   2. GreenAPI webhook settings not configured")
        print("   3. Using wrong chat ID")
        print("   4. GreenAPI plan doesn't support outgoing messages")
        print("\n   🔧 Try running: python debug_greenapi_direct.py")
    else:
        print("✅ Found some outgoing messages or mixed types")
    
    # Show sample messages if available
    if recent:
        print(f"\n📋 Sample recent messages:")
        for i, msg in enumerate(recent[:5]):
            msg_type = msg.get('type', 'unknown')
            timestamp = msg.get('timestamp', 0)
            msg_time = datetime.fromtimestamp(timestamp).strftime('%m-%d %H:%M') if timestamp else 'Unknown'
            text = str(msg.get('textMessage', ''))[:40] + "..." if len(str(msg.get('textMessage', ''))) > 40 else str(msg.get('textMessage', ''))
            sender = msg.get('senderData', {}).get('sender', 'Unknown')
            print(f"   {i+1}. [{msg_time}] {msg_type} from {sender}: {text}")

if __name__ == "__main__":
    test_direct()
