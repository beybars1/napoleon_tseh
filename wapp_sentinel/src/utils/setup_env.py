"""
Environment setup utilities for Napoleon WhatsApp Automation
"""
import os

def setup_environment():
    """Set up the environment by creating .env file if it doesn't exist"""
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
        return False
    
    try:
        with open('.env', 'w') as f:
            f.write(env_template)
        
        print("✅ Created .env file template!")
        print("\n📝 Next steps:")
        print("1. Edit .env file with your actual values:")
        print("   - Get GreenAPI credentials from https://green-api.com")
        print("   - Get OpenAI API key from https://platform.openai.com")
        print("   - Add your operational group chat ID")
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def create_env_template():
    """Create .env template file with user confirmation"""
    print("🚀 NAPOLEON WHATSAPP AUTOMATION - ENV SETUP")
    print("=" * 50)
    
    if os.path.exists('.env'):
        response = input("⚠️  .env file already exists! Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("❌ Cancelled. Existing .env file preserved.")
            return False
    
    return setup_environment()