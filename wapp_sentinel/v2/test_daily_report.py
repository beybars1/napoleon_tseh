#!/usr/bin/env python3
"""
Test script for Daily Report API
"""
import requests
from datetime import date, timedelta
import json

BASE_URL = "http://localhost:8000"

def test_preview_report():
    """Test preview endpoint"""
    print("=" * 50)
    print("Testing Preview Report (GET)")
    print("=" * 50)
    
    today = date.today().isoformat()
    url = f"{BASE_URL}/orders/daily-report/{today}"
    
    print(f"Request: GET {url}")
    response = requests.get(url)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Orders Count: {data['orders_count']}")
        print("\nReport Preview:")
        print("-" * 50)
        print(data['report'])
    else:
        print(f"Error: {response.text}")
    
    print("\n")

def test_preview_report_post():
    """Test preview endpoint (POST)"""
    print("=" * 50)
    print("Testing Preview Report (POST)")
    print("=" * 50)
    
    today = date.today().isoformat()
    url = f"{BASE_URL}/orders/preview-daily-report"
    
    payload = {"date": today}
    print(f"Request: POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, json=payload)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data['status']}")
        print(f"Orders Count: {data['orders_count']}")
        print("\nReport Preview:")
        print("-" * 50)
        print(data['report_preview'])
    else:
        print(f"Error: {response.text}")
    
    print("\n")

def test_send_report():
    """Test send report endpoint"""
    print("=" * 50)
    print("Testing Send Report (POST)")
    print("=" * 50)
    
    today = date.today().isoformat()
    url = f"{BASE_URL}/orders/send-daily-report"
    
    # ЗАМЕНИТЕ на реальный chat_id для теста отправки
    test_chat_id = "TEST_CHAT_ID@g.us"
    
    payload = {
        "date": today,
        "chat_id": test_chat_id
    }
    
    print(f"Request: POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\n⚠️  WARNING: This will actually send a message to WhatsApp!")
    print("Update test_chat_id in the script to test sending.\n")
    
    # Раскомментируйте для реальной отправки
    # response = requests.post(url, json=payload)
    # print(f"Status Code: {response.status_code}")
    # print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    print("\n")

def test_different_dates():
    """Test with different dates"""
    print("=" * 50)
    print("Testing Different Dates")
    print("=" * 50)
    
    dates = [
        date.today(),
        date.today() + timedelta(days=1),
        date.today() + timedelta(days=2),
    ]
    
    for test_date in dates:
        date_str = test_date.isoformat()
        url = f"{BASE_URL}/orders/daily-report/{date_str}"
        
        print(f"\nDate: {date_str}")
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Orders Count: {data['orders_count']}")
        else:
            print(f"  Error: {response.status_code}")
    
    print("\n")

if __name__ == "__main__":
    print("\n🧪 Daily Report API Tests\n")
    
    try:
        # Test 1: Preview with GET
        test_preview_report()
        
        # Test 2: Preview with POST
        test_preview_report_post()
        
        # Test 3: Different dates
        test_different_dates()
        
        # Test 4: Send report (commented out by default)
        test_send_report()
        
        print("✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to FastAPI server.")
        print("   Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
