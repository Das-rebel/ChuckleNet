#!/usr/bin/env python3
"""
Quick Extension Update - Non-interactive CLI for programmatic updates
"""

import sys
import json
import argparse
from update_extension_relay import ExtensionUpdater

def main():
    parser = argparse.ArgumentParser(
        description='Quick OpenClaw Extension Update Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--relay', action='store_true',
                    help='Enable OpenClaw relay')
    parser.add_argument('--relay-url', type=str,
                    help='Set relay WebSocket URL')
    parser.add_argument('--debug', action='store_true',
                    help='Enable debug mode')
    parser.add_argument('--disable-debug', action='store_true',
                    help='Disable debug mode')
    parser.add_argument('--add-permission', type=str, action='append',
                    help='Add permission (can use multiple times)')
    parser.add_argument('--version', type=str,
                    help='Set extension version')
    parser.add_argument('--save', action='store_true',
                    help='Save changes and reload')

    args = parser.parse_args()

    updater = ExtensionUpdater()

    if not updater.load_config():
        print("❌ Failed to load configuration")
        sys.exit(1)

    if not updater.load_manifest():
        print("❌ Failed to load manifest")
        sys.exit(1)

    changes_made = False

    # Handle relay settings
    if args.relay or args.relay_url:
        relay_settings = {}
        if args.relay:
            relay_settings['relay_enabled'] = True
        if args.relay_url:
            relay_settings['relay_url'] = args.relay_url

        if relay_settings:
            updater.update_relay_settings(relay_settings)
            changes_made = True

    # Handle debug mode
    if args.debug:
        updater.enable_debug_mode(True)
        changes_made = True
    elif args.disable_debug:
        updater.enable_debug_mode(False)
        changes_made = True

    # Handle permissions
    if args.add_permission:
        updater.update_permissions(args.add_permission)
        changes_made = True

    # Handle version
    if args.version:
        updater.update_version(args.version)
        changes_made = True

    # Save if requested
    if args.save:
        updater.save_config()
        updater.save_manifest()
        print("\n✅ Changes saved!")
        print("\n🔄 Reload extension in Brave:")
        print("   brave://extensions → Click reload icon (↻)")
    elif changes_made:
        print("\n⚠️  Changes made but not saved")
        print("   Add --save flag to persist changes")

if __name__ == "__main__":
    main()
