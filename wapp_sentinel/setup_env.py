#!/usr/bin/env python3
"""
Quick .env file setup for Napoleon WhatsApp Automation
"""
import os

def create_env_template():
    """Create .env template file"""
    
    env_template = """# GreenAPI Configuration
GREEN_API_ID_INSTANCE=your_instance_id_here
GREEN_API_TOKEN=your_token_here

# OpenAI Configuration  
OPENAI_API_KEY=your_openai_api_key_here

# WhatsApp Group IDs
MAIN_GROUP_CHAT_ID=120363272114174001@g.us
OPERATIONAL_GROUP_CHAT_ID=your_operational_group_id@g.us

# Database Configuration
DATABASE_URL=postgresql://admin:admin@localhost:5411/napoleon-sentinel-db

# Testing mode (set to "true" to avoid sending real messages)
TESTING_MODE=true
"""

    if os.path.exists('.env'):
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("❌ Cancelled. Existing .env file preserved.")
            return
    
    with open('.env', 'w') as f:
        f.write(env_template)
    
    print("✅ Created .env file template!")
    print("\n📝 Next steps:")
    print("1. Edit .env file with your actual values:")
    print("   - Get GreenAPI credentials from https://green-api.com")
    print("   - Get OpenAI API key from https://platform.openai.com")
    print("   - Add your operational group chat ID")
    print("\n2. Test the setup:")
    print("   python check_env.py")
    print("\n3. Start the system:")
    print("   python test_mvp_workflow.py status")

if __name__ == "__main__":
    print("🚀 NAPOLEON WHATSAPP AUTOMATION - ENV SETUP")
    print("=" * 50)
    create_env_template()
