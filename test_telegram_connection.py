#!/usr/bin/env python3
"""
Quick Test for Telegram API Connection
Tests if your credentials work and can connect to Telegram
"""

import os
import asyncio
from telethon import TelegramClient

async def test_telegram_connection():
    """Test if Telegram API credentials work"""

    print("🔍 Testing Telegram API Connection")
    print("=" * 40)

    # Get API credentials
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')

    # Check if credentials are provided
    missing_credentials = []
    if not api_id:
        missing_credentials.append("TELEGRAM_API_ID")
    if not api_hash:
        missing_credentials.append("TELEGRAM_API_HASH")
    if not phone:
        missing_credentials.append("TELEGRAM_PHONE")

    if missing_credentials:
        print("❌ Missing Environment Variables:")
        for var in missing_credentials:
            print(f"   • {var}")

        print("\n📋 How to set them:")
        print("export TELEGRAM_API_ID='your_api_id'")
        print("export TELEGRAM_API_HASH='your_api_hash'")
        print("export TELEGRAM_PHONE='+1234567890'")
        print("\n📖 Get API credentials: https://my.telegram.org/")
        return False

    try:
        # Convert api_id to integer
        api_id = int(api_id)
        print(f"✅ API ID: {api_id}")
        print(f"✅ API Hash: {api_hash[:10]}...")
        print(f"✅ Phone: {phone}")

    except ValueError:
        print("❌ TELEGRAM_API_ID must be a number")
        return False

    try:
        # Create Telegram client
        print("\n🔧 Connecting to Telegram...")
        client = TelegramClient('test_session', api_id, api_hash)

        # Try to connect
        await client.connect()

        # Check if we're authorized
        if await client.is_user_authorized():
            print("✅ Successfully connected to Telegram!")

            # Get self info
            me = await client.get_me()
            print(f"✅ Logged in as: {me.first_name} (@{me.username})")
            print(f"✅ User ID: {me.id}")

            # Try to access the target channel
            print("\n🔍 Checking access to target channel...")
            try:
                target_channel = await client.get_entity(-2127259353)
                print(f"✅ Found channel: {target_channel.title}")

                # Get recent message count
                messages = await client.get_messages(target_channel, limit=5)
                print(f"✅ Channel has recent messages (found {len(messages)} recent)")

                if messages:
                    latest_msg = messages[0]
                    print(f"✅ Latest message: {latest_msg.text[:50]}...")
                    print(f"✅ Latest message date: {latest_msg.date}")

                print("\n🎉 SUCCESS! You can now run the full scraper:")
                print("   python3 telegram_api_scraper.py")

            except Exception as e:
                print(f"⚠️  Cannot access target channel: {e}")
                print("💡 Make sure you're a member of the channel first")
                print("   Channel: https://web.telegram.org/k/#-2127259353")

            await client.disconnect()
            return True

        else:
            print("❌ Not authorized. Need to log in first.")
            print("💡 Try running with phone verification:")
            print("   await client.start(phone)")

            await client.disconnect()
            return False

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("• Check your API credentials are correct")
        print("• Make sure you have internet connection")
        print("• Try again in a few minutes")
        return False

def main():
    """Main function"""
    try:
        result = asyncio.run(test_telegram_connection())
        if result:
            print("\n🚀 Ready to start scraping!")
        else:
            print("\n⚠️  Fix the issues above before running the scraper")
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()