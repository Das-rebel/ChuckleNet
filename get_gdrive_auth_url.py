#!/usr/bin/env python3
"""
Simple script to get Google Drive OAuth URL for rclone
"""

import webbrowser
from urllib.parse import urlencode

# rclone's Google OAuth configuration
CLIENT_ID = "202264815068.apps.googleusercontent.com"
REDIRECT_URI = "http://127.0.0.1:53682/"
SCOPE = "https://www.googleapis.com/auth/drive"

# Build the OAuth URL
params = {
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    "response_type": "code",
    "access_type": "offline"
}

auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

print("=" * 70)
print("Google Drive OAuth Authentication URL")
print("=" * 70)
print()
print("Please visit this URL to authorize rclone:")
print()
print(auth_url)
print()
print("=" * 70)
print("Instructions:")
print("=" * 70)
print("1. Copy the URL above and paste it in your browser")
print("2. Sign in with: meghamukherjeedas@gmail.com")
print("3. Click 'Allow' to grant rclone access")
print("4. After authorizing, you'll be redirected to localhost")
print("5. Copy the authorization code from the URL")
print("6. Return here and we'll complete the setup")
print()

# Try to open the URL automatically
try:
    print("Attempting to open browser automatically...")
    webbrowser.open(auth_url)
    print("✓ Browser opened")
except:
    print("⚠️  Could not open browser automatically")
    print("   Please copy the URL above manually")
