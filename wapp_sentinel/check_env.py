#!/usr/bin/env python3
"""
Quick environment variables checker
"""
import os
from dotenv import load_dotenv

load_dotenv()

required_vars = [
    "GREEN_API_ID_INSTANCE",
    "GREEN_API_TOKEN", 
    "OPENAI_API_KEY",
    "MAIN_GROUP_CHAT_ID",
    "DATABASE_URL"
]

optional_vars = [
    "OPERATIONAL_GROUP_CHAT_ID",
    "TESTING_MODE"
]

print("🔍 ENVIRONMENT VARIABLES CHECK")
print("=" * 40)

print("\n✅ REQUIRED VARIABLES:")
missing_required = []
for var in required_vars:
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        if "TOKEN" in var or "KEY" in var:
            display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
        elif "ID" in var:
            display_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else value
        else:
            display_value = value
        print(f"  ✅ {var}: {display_value}")
    else:
        print(f"  ❌ {var}: NOT SET")
        missing_required.append(var)

print("\n📋 OPTIONAL VARIABLES:")
for var in optional_vars:
    value = os.getenv(var)
    if value:
        print(f"  ✅ {var}: {value}")
    else:
        print(f"  ⚪ {var}: not set (optional)")

if missing_required:
    print(f"\n❌ MISSING REQUIRED VARIABLES: {', '.join(missing_required)}")
    print("\n💡 Create a .env file with these variables:")
    for var in missing_required:
        print(f"   {var}=your_value_here")
else:
    print("\n🎉 ALL REQUIRED VARIABLES ARE SET!")

print(f"\n🔗 Current working directory: {os.getcwd()}")
print(f"📁 Looking for .env file at: {os.path.join(os.getcwd(), '.env')}")

if os.path.exists('.env'):
    print("✅ .env file exists")
else:
    print("❌ .env file not found")
    print("\n💡 Create .env file with:")
    print("GREEN_API_ID_INSTANCE=your_instance_id")
    print("GREEN_API_TOKEN=your_token")
    print("OPENAI_API_KEY=your_openai_key")
    print("MAIN_GROUP_CHAT_ID=120363272114174001@g.us")
    print("OPERATIONAL_GROUP_CHAT_ID=your_operational_group_id@g.us")
    print("DATABASE_URL=postgresql://admin:admin@localhost:5411/napoleon-sentinel-db")
    print("TESTING_MODE=true")
