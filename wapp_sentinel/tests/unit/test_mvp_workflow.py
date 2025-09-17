#!/usr/bin/env python3
"""
MVP Testing Script for Napoleon WhatsApp Order Automation
This script tests the complete workflow:
1. Check for new messages in main group
2. Process them with OpenAI
3. Generate daily consolidation
4. Send to operational group (in test mode)
"""

import os
import requests
import json
from datetime import date, datetime
from dotenv import load_dotenv
from greenapi_service import get_recent_messages, send_message
from openai_service import parse_order, consolidate_orders
from database import get_db, Order

load_dotenv()

MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")
OPERATIONAL_GROUP_CHAT_ID = os.getenv("OPERATIONAL_GROUP_CHAT_ID", "test@g.us")
API_BASE = "http://localhost:8000"

def test_message_flow():
    """Test the complete message processing flow"""
    print("🧪 TESTING MVP WORKFLOW")
    print("=" * 50)
    
    # Step 1: Check recent messages
    print("\n1️⃣ CHECKING RECENT MESSAGES")
    messages = get_recent_messages(MAIN_GROUP_CHAT_ID, hours_back=48)
    print(f"Found {len(messages)} recent messages")
    
    if not messages:
        print("❌ No recent messages. Send a test order to your main group first!")
        return
    
    # Step 2: Process messages via API
    print("\n2️⃣ PROCESSING MESSAGES")
    try:
        response = requests.post(f"{API_BASE}/process-messages")
        if response.status_code == 200:
            print("✅ Message processing triggered successfully")
        else:
            print(f"❌ Error processing messages: {response.text}")
            return
    except Exception as e:
        print(f"❌ API error: {e}")
        return
    
    # Step 3: Check today's orders
    print("\n3️⃣ CHECKING TODAY'S ORDERS")
    try:
        response = requests.get(f"{API_BASE}/orders/today")
        today_orders = response.json()
        print(f"Found {len(today_orders)} orders for today")
        
        for order in today_orders:
            print(f"  - {order['customer_name']}: {order['delivery_time']}")
    except Exception as e:
        print(f"❌ Error getting today's orders: {e}")
        return
    
    # Step 4: Test consolidation
    print("\n4️⃣ TESTING CONSOLIDATION")
    if today_orders:
        try:
            # Enable test mode
            os.environ["TESTING_MODE"] = "true"
            
            response = requests.post(f"{API_BASE}/send-daily-orders")
            if response.status_code == 200:
                print("✅ Daily orders consolidation triggered")
                print("📱 Check the console output for the consolidated message preview")
            else:
                print(f"❌ Error sending daily orders: {response.text}")
        except Exception as e:
            print(f"❌ Error in consolidation: {e}")
    else:
        print("⚠️ No orders for today to consolidate")
    
    # Step 5: Show next steps
    print("\n5️⃣ NEXT STEPS FOR PRODUCTION")
    print("=" * 50)
    print("1. Set TESTING_MODE=false in your .env file")
    print("2. Add your OPERATIONAL_GROUP_CHAT_ID to .env")
    print("3. Enable daily scheduling (uncomment in main.py)")
    print("4. Run the server: uvicorn main:app --reload")
    print("5. The system will automatically:")
    print("   - Check for new messages every 2 minutes")
    print("   - Send daily consolidation at 8 AM (when enabled)")

def test_bulk_via_api():
    """Test bulk processing via API endpoint"""
    print("🌐 TESTING BULK PROCESSING VIA API")
    print("=" * 50)
    
    try:
        print("📡 Triggering bulk processing via API...")
        response = requests.post(f"{API_BASE}/bulk-process-messages?days=7")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
            print("💡 Check the server logs to see processing progress")
            print("🔗 After processing, check: curl http://localhost:8000/orders")
        else:
            print(f"❌ API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error calling API: {e}")

def test_manual_order():
    """Test parsing a manual order"""
    print("\n🧪 TESTING MANUAL ORDER PARSING")
    print("=" * 50)
    
    test_order = """Заказ на завтра 31.08
Время: 14:00
Наполеон классик 1кг
Шоколадный торт 2кг

Анна
+7 701 123 4567
Оплачено ✅"""
    
    print("Test order text:")
    print(test_order)
    print("\nParsing with OpenAI...")
    
    try:
        result = parse_order(test_order)
        print("\n📊 PARSED RESULT:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get("is_order"):
            print("✅ Successfully identified as an order")
        else:
            print("❌ Not identified as an order")
            
    except Exception as e:
        print(f"❌ Error parsing order: {e}")

def check_system_status():
    """Check if all components are working"""
    print("\n🔍 SYSTEM STATUS CHECK")
    print("=" * 50)
    
    # Check API
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code == 200:
            print("✅ API Server: Running")
        else:
            print("❌ API Server: Error")
    except:
        print("❌ API Server: Not running (start with: uvicorn main:app --reload)")
    
    # Check database
    try:
        response = requests.get(f"{API_BASE}/orders")
        orders = response.json()
        print(f"✅ Database: Connected ({len(orders)} total orders)")
    except:
        print("❌ Database: Connection error")
    
    # Check environment variables
    required_vars = ["GREEN_API_ID_INSTANCE", "GREEN_API_TOKEN", "OPENAI_API_KEY", "MAIN_GROUP_CHAT_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if not missing_vars:
        print("✅ Environment: All required variables set")
    else:
        print(f"❌ Environment: Missing variables: {missing_vars}")
    
    # Check GreenAPI connection
    try:
        messages = get_recent_messages(MAIN_GROUP_CHAT_ID, hours_back=1)
        print("✅ GreenAPI: Connected")
    except:
        print("❌ GreenAPI: Connection error")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            check_system_status()
        elif sys.argv[1] == "parse":
            test_manual_order()
        elif sys.argv[1] == "flow":
            test_message_flow()
        elif sys.argv[1] == "bulk":
            test_bulk_via_api()
        else:
            print("Usage: python test_mvp_workflow.py [status|parse|flow|bulk]")
    else:
        print("🚀 NAPOLEON ORDER AUTOMATION - MVP TESTER")
        print("=" * 50)
        print("Available commands:")
        print("  python test_mvp_workflow.py status  - Check system status")
        print("  python test_mvp_workflow.py parse   - Test order parsing")
        print("  python test_mvp_workflow.py flow    - Test complete workflow")
        print("  python test_mvp_workflow.py bulk    - Bulk process last 7 days messages")
        print("\nFor first-time setup, run 'status' first!")
