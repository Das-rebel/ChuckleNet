#!/usr/bin/env python3
"""
QUICK TELETHON SETUP
Simple setup for Telegram API credentials
"""

import os
from dotenv import load_dotenv

def create_env_file():
    """Create .env file with template"""
    env_content = """# TELEGRAM API CREDENTIALS
# Get these from https://my.telegram.org/

TELEGRAM_API_ID=YOUR_API_ID_HERE
TELEGRAM_API_HASH=YOUR_API_HASH_HERE
TELEGRAM_PHONE=YOUR_PHONE_NUMBER_HERE

# Example format:
# TELEGRAM_API_ID=12345678
# TELEGRAM_API_HASH=abcdef123456789abcdef123456789
# TELEGRAM_PHONE=+1234567890
"""

    with open('.env', 'w') as f:
        f.write(env_content)

    print("✅ Created .env file with template")
    print("📝 Please edit .env file with your actual credentials")

def check_credentials():
    """Check if credentials are properly set"""
    load_dotenv()

    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')

    print("\n🔍 CHECKING CREDENTIALS:")
    print("-" * 30)

    if api_id and api_id != 'YOUR_API_ID_HERE':
        print(f"✅ API ID: {api_id}")
    else:
        print("❌ API ID: Missing or invalid")

    if api_hash and api_hash != 'YOUR_API_HASH_HERE':
        print(f"✅ API Hash: {'*' * len(api_hash)} (hidden for security)")
    else:
        print("❌ API Hash: Missing or invalid")

    if phone and phone != 'YOUR_PHONE_NUMBER_HERE':
        print(f"✅ Phone: {phone}")
    else:
        print("❌ Phone: Missing or invalid")

    all_set = (api_id and api_id != 'YOUR_API_ID_HERE' and
               api_hash and api_hash != 'YOUR_API_HASH_HERE' and
               phone and phone != 'YOUR_PHONE_NUMBER_HERE')

    if all_set:
        print("\n🎉 All credentials are properly set!")
        print("🚀 You can now run: python3 enhanced_telethon_trader.py")
    else:
        print("\n❌ Please complete your credentials in .env file")
        print("💡 Get API credentials from: https://my.telegram.org/")

    return all_set

def setup_instructions():
    """Print setup instructions"""
    print("""
🚀 TELETHON API SETUP INSTRUCTIONS
==================================

STEP 1: GET API CREDENTIALS
----------------------------
1. Go to: https://my.telegram.org/
2. Sign in with your phone number
3. Click "API development tools"
4. Fill out the form:
   • App title: Trading Monitor
   • Short name: trading_monitor
   • Platform: Desktop
   • Description: Trading signal monitor
5. Click "Create application"
6. Copy your API ID and API Hash

STEP 2: CONFIGURE CREDENTIALS
-----------------------------
1. Edit the .env file (will be created)
2. Replace the placeholder values:
   - YOUR_API_ID_HERE → your actual API ID
   - YOUR_API_HASH_HERE → your actual API Hash
   - YOUR_PHONE_NUMBER_HERE → your phone with country code

STEP 3: RUN THE MONITOR
-----------------------
python3 enhanced_telethon_trader.py

💡 Your API credentials are kept private and are used only for
   accessing your own Telegram account for monitoring purposes.
""")

def main():
    """Main setup function"""
    print("🚀 QUICK TELETHON SETUP")
    print("=" * 40)

    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        create_env_file()
    else:
        print("📁 .env file already exists")

    # Show instructions
    setup_instructions()

    # Check credentials
    check_credentials()

if __name__ == "__main__":
    main()