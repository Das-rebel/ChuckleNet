#!/usr/bin/env python3
"""
OpenClaw Browser Relay Extension Updater
Updates Simplify Copilot extension configuration for enhanced browser relay capabilities
"""

import json
import os
import shutil
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Extension paths
EXTENSION_ID = "pbanhockgagggenencehbnadejlgchfc"
EXTENSION_VERSION = "2.3.1"
EXTENSION_DIR = f"/Users/Subho/Library/Application Support/BraveSoftware/Brave-Browser/Default/Extensions/{EXTENSION_ID}/{EXTENSION_VERSION}_0"
CONFIG_FILE = os.path.join(EXTENSION_DIR, "remoteConfig.json")
MANIFEST_FILE = os.path.join(EXTENSION_DIR, "manifest.json")

class ExtensionUpdater:
    def __init__(self):
        self.config = None
        self.manifest = None

    def load_config(self):
        """Load extension configuration"""
        try:
            if os.path.exists(CONFIG_FILE):
                logger.info(f"📂 Loading configuration from: {CONFIG_FILE}")
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info("✅ Configuration loaded successfully")
                return True
            else:
                logger.error(f"❌ Configuration file not found: {CONFIG_FILE}")
                return False
        except Exception as e:
            logger.error(f"❌ Error loading configuration: {e}")
            return False

    def load_manifest(self):
        """Load extension manifest"""
        try:
            if os.path.exists(MANIFEST_FILE):
                logger.info(f"📄 Loading manifest from: {MANIFEST_FILE}")
                with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
                    self.manifest = json.load(f)
                logger.info("✅ Manifest loaded successfully")
                return True
            else:
                logger.error(f"❌ Manifest file not found: {MANIFEST_FILE}")
                return False
        except Exception as e:
            logger.error(f"❌ Error loading manifest: {e}")
            return False

    def backup_config(self):
        """Create backup of current configuration"""
        try:
            if os.path.exists(CONFIG_FILE):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"{CONFIG_FILE}.backup_{timestamp}"
                shutil.copy2(CONFIG_FILE, backup_file)
                logger.info(f"💾 Backup created: {backup_file}")
                return backup_file
            return None
        except Exception as e:
            logger.error(f"❌ Error creating backup: {e}")
            return None

    def update_ats_config(self, company_name, urls, extractors=None):
        """Update ATS configuration for a company"""
        try:
            if not self.config or 'ATS' not in self.config:
                logger.error("❌ Invalid configuration structure")
                return False

            logger.info(f"🔄 Updating ATS configuration for: {company_name}")

            # Update or create company configuration
            if company_name.upper() not in self.config['ATS']:
                self.config['ATS'][company_name.upper()] = {}
                logger.info(f"  📝 Creating new company config")

            company_config = self.config['ATS'][company_name.upper()]

            # Update URLs
            if urls:
                company_config['urls'] = urls
                logger.info(f"  🔗 Updated {len(urls)} URL patterns")

            # Update extractors
            if extractors:
                company_config['trackedObjExtractors'] = extractors
                logger.info(f"  📊 Updated {len(extractors)} extractors")

            logger.info("✅ ATS configuration updated")
            return True

        except Exception as e:
            logger.error(f"❌ Error updating ATS config: {e}")
            return False

    def update_relay_settings(self, settings):
        """Update browser relay settings"""
        try:
            if not self.config:
                return False

            logger.info("🔄 Updating relay settings...")

            # Add or update OpenClaw relay configuration
            if 'OpenClaw_Relay' not in self.config:
                self.config['OpenClaw_Relay'] = {}

            self.config['OpenClaw_Relay'].update(settings)

            logger.info("✅ Relay settings updated")
            return True

        except Exception as e:
            logger.error(f"❌ Error updating relay settings: {e}")
            return False

    def add_custom_ats(self, company_name, config_data):
        """Add custom ATS configuration"""
        try:
            if not self.config or 'ATS' not in self.config:
                return False

            logger.info(f"➕ Adding custom ATS config for: {company_name}")

            self.config['ATS'][company_name.upper()] = config_data

            logger.info(f"✅ Custom ATS added: {company_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Error adding custom ATS: {e}")
            return False

    def enable_debug_mode(self, enabled=True):
        """Enable or disable debug mode"""
        try:
            if not self.config:
                return False

            if 'debug' not in self.config:
                self.config['debug'] = {}

            self.config['debug']['enabled'] = enabled
            self.config['debug']['timestamp'] = datetime.now().isoformat()

            logger.info(f"✅ Debug mode: {'enabled' if enabled else 'disabled'}")
            return True

        except Exception as e:
            logger.error(f"❌ Error setting debug mode: {e}")
            return False

    def update_permissions(self, additional_permissions):
        """Update extension permissions in manifest"""
        try:
            if not self.manifest or 'permissions' not in self.manifest:
                logger.error("❌ Invalid manifest structure")
                return False

            logger.info("🔄 Updating permissions...")

            current_permissions = set(self.manifest['permissions'])
            new_permissions = current_permissions.union(set(additional_permissions))

            self.manifest['permissions'] = list(new_permissions)

            logger.info(f"✅ Permissions updated: {len(self.manifest['permissions'])} total")
            logger.info(f"   Added: {', '.join(additional_permissions)}")
            return True

        except Exception as e:
            logger.error(f"❌ Error updating permissions: {e}")
            return False

    def update_version(self, new_version):
        """Update extension version"""
        try:
            if not self.manifest:
                return False

            logger.info(f"🔄 Updating version to: {new_version}")

            self.manifest['version'] = new_version

            logger.info("✅ Version updated")
            return True

        except Exception as e:
            logger.error(f"❌ Error updating version: {e}")
            return False

    def save_config(self):
        """Save updated configuration"""
        try:
            if not self.config:
                logger.error("❌ No configuration to save")
                return False

            # Create backup first
            self.backup_config()

            # Write updated configuration
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            logger.info("💾 Configuration saved successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Error saving configuration: {e}")
            return False

    def save_manifest(self):
        """Save updated manifest"""
        try:
            if not self.manifest:
                logger.error("❌ No manifest to save")
                return False

            # Backup manifest
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{MANIFEST_FILE}.backup_{timestamp}"
            shutil.copy2(MANIFEST_FILE, backup_file)
            logger.info(f"💾 Manifest backup: {backup_file}")

            # Write updated manifest
            with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.manifest, f, indent=2, ensure_ascii=False)

            logger.info("💾 Manifest saved successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Error saving manifest: {e}")
            return False

    def get_current_stats(self):
        """Get current configuration statistics"""
        try:
            if not self.config:
                return {}

            stats = {
                'total_ats_configs': len(self.config.get('ATS', {})),
                'ats_companies': list(self.config.get('ATS', {}).keys()),
                'has_relay_config': 'OpenClaw_Relay' in self.config,
                'debug_enabled': self.config.get('debug', {}).get('enabled', False),
                'config_size_bytes': os.path.getsize(CONFIG_FILE) if os.path.exists(CONFIG_FILE) else 0
            }

            return stats

        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {}

def print_menu():
    """Print interactive menu"""
    print("\n" + "="*70)
    print("🚀 OPENCLAW BROWSER RELAY EXTENSION UPDATER")
    print("="*70)
    print("\n📋 Available Options:")
    print()
    print("1. 📊 View Current Configuration")
    print("2. 🔄 Update ATS Configuration (Company)")
    print("3. ➕ Add Custom ATS Configuration")
    print("4. ⚙️  Update Relay Settings")
    print("5. 🐛 Toggle Debug Mode")
    print("6. 🔐 Update Extension Permissions")
    print("7. 📝 Update Extension Version")
    print("8. 📈 Get Configuration Statistics")
    print("9. 💾 Save Changes & Reload Extension")
    print("0. 🚪 Exit")
    print()
    print("="*70)

def main():
    """Main execution function"""
    updater = ExtensionUpdater()

    # Load configuration
    if not updater.load_config():
        print("❌ Failed to load configuration")
        print(f"   Check extension path: {EXTENSION_DIR}")
        return

    if not updater.load_manifest():
        print("❌ Failed to load manifest")
        print(f"   Check extension path: {EXTENSION_DIR}")
        return

    # Show current stats
    stats = updater.get_current_stats()
    print("\n📊 Current Configuration:")
    print(f"   • ATS Configs: {stats['total_ats_configs']}")
    print(f"   • Companies: {len(stats['ats_companies'])}")
    print(f"   • Relay Config: {'✅' if stats['has_relay_config'] else '❌'}")
    print(f"   • Debug Mode: {'✅' if stats['debug_enabled'] else '❌'}")
    print(f"   • Config Size: {stats['config_size_bytes']:,} bytes")

    # Interactive menu
    while True:
        print_menu()
        choice = input("\n👉 Select option (0-9): ").strip()

        if choice == '1':
            # View current configuration
            print("\n📊 Current ATS Configurations:")
            for company, config in updater.config.get('ATS', {}).items():
                urls_count = len(config.get('urls', []))
                print(f"\n   🏢 {company}")
                print(f"      URL Patterns: {urls_count}")
                print(f"      Extractors: {len(config.get('trackedObjExtractors', []))}")

        elif choice == '2':
            # Update ATS configuration
            print("\n🔄 Update ATS Configuration")
            company = input("   Company name (e.g., ADP, Workday): ").strip()
            if not company:
                continue

            print("\n   Update options:")
            print("   1. Add URLs")
            print("   2. Add Extractors")
            print("   3. Both")
            subchoice = input("   Select (1-3): ").strip()

            urls = None
            extractors = None

            if subchoice in ['1', '3']:
                url_input = input("   Enter URL patterns (comma-separated): ").strip()
                urls = [u.strip() for u in url_input.split(',') if u.strip()]

            if subchoice in ['2', '3']:
                print("   Enter extractor config (JSON format, or press Enter to skip):")
                extractor_input = input("   > ").strip()
                if extractor_input:
                    try:
                        extractors = json.loads(extractor_input)
                    except:
                        print("   ❌ Invalid JSON, skipping extractors")

            if urls or extractors:
                updater.update_ats_config(company, urls, extractors)
            else:
                print("   ⚠️  Nothing to update")

        elif choice == '3':
            # Add custom ATS
            print("\n➕ Add Custom ATS Configuration")
            company = input("   Company name: ").strip()
            if not company:
                continue

            print("\n   Enter configuration (JSON):")
            print("   Example:")
            print('   {')
            print('     "urls": ["*://example.com/*"],')
            print('     "defaultMethod": "standard",')
            print('     "trackedObjExtractors": [...]')
            print('   }')
            config_input = input("   > ").strip()

            try:
                config_data = json.loads(config_input)
                updater.add_custom_ats(company, config_data)
            except Exception as e:
                print(f"   ❌ Invalid JSON: {e}")

        elif choice == '4':
            # Update relay settings
            print("\n⚙️  Update Relay Settings")
            print("   Current relay settings:")
            print(json.dumps(updater.config.get('OpenClaw_Relay', {}), indent=2))

            print("\n   Enter settings (JSON format):")
            print("   Example:")
            print('   {')
            print('     "relay_enabled": true,')
            print('     "relay_url": "ws://localhost:18789",')
            print('     "auto_fill_enabled": true,')
            print('     "tracking_enabled": true')
            print('   }')
            settings_input = input("   > ").strip()

            try:
                settings = json.loads(settings_input)
                updater.update_relay_settings(settings)
                print("   ✅ Relay settings updated")
            except Exception as e:
                print(f"   ❌ Invalid JSON: {e}")

        elif choice == '5':
            # Toggle debug mode
            current_debug = updater.config.get('debug', {}).get('enabled', False)
            new_debug = not current_debug
            updater.enable_debug_mode(new_debug)

        elif choice == '6':
            # Update permissions
            print("\n🔐 Update Permissions")
            print("   Current permissions:")
            print(', '.join(updater.manifest.get('permissions', [])))

            perms_input = input("\n   Add permissions (comma-separated): ").strip()
            if perms_input:
                new_perms = [p.strip() for p in perms_input.split(',') if p.strip()]
                updater.update_permissions(new_perms)

        elif choice == '7':
            # Update version
            print("\n📝 Update Version")
            print(f"   Current version: {updater.manifest.get('version', 'unknown')}")
            new_version = input("   Enter new version: ").strip()
            if new_version:
                updater.update_version(new_version)

        elif choice == '8':
            # Get statistics
            stats = updater.get_current_stats()
            print("\n📈 Configuration Statistics:")
            print(f"   Total ATS Configurations: {stats['total_ats_configs']}")
            print(f"   Companies Configured: {len(stats['ats_companies'])}")
            if stats['ats_companies']:
                print("\n   Configured Companies:")
                for company in sorted(stats['ats_companies']):
                    print(f"      • {company}")
            print(f"\n   Relay Configured: {'Yes' if stats['has_relay_config'] else 'No'}")
            print(f"   Debug Mode: {'Enabled' if stats['debug_enabled'] else 'Disabled'}")
            print(f"   Configuration File Size: {stats['config_size_bytes']:,} bytes")

        elif choice == '9':
            # Save and reload
            print("\n💾 Saving Changes...")

            config_saved = updater.save_config()
            manifest_saved = updater.save_manifest()

            if config_saved and manifest_saved:
                print("✅ Configuration and manifest saved!")

                print("\n🔄 To reload the extension:")
                print("   1. Open Brave Browser")
                print("   2. Go to: brave://extensions")
                print("   3. Find 'Simplify Copilot' extension")
                print("   4. Click the reload icon (↻)")
                print("\n   Or restart Brave Browser completely")
            else:
                print("❌ Failed to save changes")

        elif choice == '0':
            print("\n👋 Exiting...")
            break

        else:
            print("\n❌ Invalid choice, try again")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
