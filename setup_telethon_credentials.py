#!/usr/bin/env python3
"""
Quick Setup Script for Telethon API Credentials
Guides you through getting and setting up the necessary API credentials
"""

import os
import subprocess

def print_banner():
    """Print setup banner"""
    print("🚀 TELETHON API CREDENTIALS SETUP")
    print("=" * 50)
    print("This will help you get the API credentials needed for automatic group monitoring")
    print("=" * 50)

def guide_to_my_telegram():
    """Guide user to my.telegram.org"""
    print("\n📖 STEP 1: Get API Credentials")
    print("-" * 30)
    print("1. Open your browser and go to: https://my.telegram.org/")
    print("2. Sign in with your phone number (you'll get a verification code)")
    print("3. Click on 'API development tools'")
    print("4. Fill out the application form:")
    print("   • App title: My App")
    print("   • Short name: my_app")
    print("   • Platform: Desktop")
    print("   • Description: Simple desktop application")
    print("5. Click 'Create application'")
    print("6. You'll get your API ID and API Hash")
    print("\n⚠️  Important: Keep your API Hash secret!")

def get_credentials_from_user():
    """Get credentials from user input"""
    print("\n📝 STEP 2: Enter Your Credentials")
    print("-" * 30)

    while True:
        try:
            api_id = input("🔢 Enter your API ID (numbers only): ").strip()
            if api_id.isdigit():
                break
            print("❌ API ID must be a number. Try again.")
        except KeyboardInterrupt:
            print("\n⚠️ Setup cancelled.")
            return None, None, None

    api_hash = input("🔑 Enter your API Hash (starts with 'v1'): ").strip()
    phone = input("📱 Enter your phone number with country code: ").strip()

    return api_id, api_hash, phone

def set_environment_variables(api_id, api_hash, phone):
    """Set environment variables"""
    print(f"\n⚙️  STEP 3: Setting Environment Variables")
    print("-" * 30)

    # Set for current session
    os.environ['TELEGRAM_API_ID'] = api_id
    os.environ['TELEGRAM_API_HASH'] = api_hash
    os.environ['TELEGRAM_PHONE'] = phone

    print("✅ Environment variables set for current session")

    # Create .env file for future use
    env_file = ".env_telethon"
    with open(env_file, 'w') as f:
        f.write(f"export TELEGRAM_API_ID='{api_id}'\n")
        f.write(f"export TELEGRAM_API_HASH='{api_hash}'\n")
        f.write(f"export TELEGRAM_PHONE='{phone}'\n")

    print(f"💾 Saved to {env_file} for future use")

def test_credentials():
    """Test if credentials are set"""
    print(f"\n🧪 STEP 4: Testing Credentials")
    print("-" * 30)

    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')

    if all([api_id, api_hash, phone]):
        print("✅ All credentials are set!")
        print(f"   API ID: {api_id}")
        print(f"   API Hash: {api_hash[:10]}...")
        print(f"   Phone: {phone}")
        return True
    else:
        print("❌ Missing credentials:")
        if not api_id:
            print("   • TELEGRAM_API_ID")
        if not api_hash:
            print("   • TELEGRAM_API_HASH")
        if not phone:
            print("   • TELEGRAM_PHONE")
        return False

def show_next_steps():
    """Show next steps"""
    print(f"\n🚀 STEP 5: Ready to Monitor!")
    print("-" * 30)
    print("Your credentials are now set up. You can run:")
    print()
    print("📊 For one-time analysis:")
    print("   python3 telethon_group_monitor.py")
    print()
    print("🔄 For continuous monitoring:")
    print("   python3 continuous_monitor.py")
    print()
    print("📋 To test connection:")
    print("   python3 test_telethon_connection.py")
    print()
    print("💡 The monitor will:")
    print("   • Connect using your Telegram account")
    print("   • Read messages from group -2127259353")
    print("   • Analyze for trading signals")
    print("   • Generate comprehensive reports")
    print("   • Save results for analysis")

def main():
    """Main setup function"""
    print_banner()

    try:
        # Check if credentials already exist
        if os.getenv('TELEGRAM_API_ID') and os.getenv('TELEGRAM_API_HASH'):
            print("🔍 Found existing credentials!")
            if test_credentials():
                show_next_steps()
                return

        # Guide to get credentials
        guide_to_my_telegram()

        # Ask if user has credentials
        has_credentials = input("\n❓ Do you have your API credentials ready? (y/n): ").strip().lower()

        if has_credentials != 'y':
            print("\n💡 Get your credentials first, then run this script again.")
            print("📖 Go to: https://my.telegram.org/")
            return

        # Get credentials from user
        api_id, api_hash, phone = get_credentials_from_user()

        if not api_id:
            return

        # Set environment variables
        set_environment_variables(api_id, api_hash, phone)

        # Test credentials
        if test_credentials():
            show_next_steps()
        else:
            print("❌ Setup failed. Please check your credentials and try again.")

    except KeyboardInterrupt:
        print("\n⚠️ Setup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Setup error: {e}")

if __name__ == "__main__":
    main()