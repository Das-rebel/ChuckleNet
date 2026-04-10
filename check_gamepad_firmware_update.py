#!/usr/bin/env python3
"""
Gamepad Firmware Update Checker
Detects device model and checks for available firmware updates
"""

import subprocess
import sys
import json
import re
from typing import Dict, Optional, Tuple

# Vendor ID to Manufacturer mapping
VENDOR_ID_MAP = {
    '0x1949': 'Unknown/Generic',
    '0x0810': 'Xbox',
    '0x045e': 'Microsoft',
    '0x054c': 'Sony (PlayStation)',
    '0x057e': 'Nintendo',
    '0x20d6': '8BitDo',
    '0x28de': 'Valve (Steam Controller)',
    '0x2dc8': '8BitDo',
    '0x0079': 'DragonRise',
    '0x081f': 'Logitech',
    '0x046d': 'Logitech',
}

def run_command(cmd: str, timeout: int = 30) -> Tuple[bool, str, str]:
    """Run a command and return success, stdout, stderr"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return False, "", str(e)

def get_detailed_device_info() -> Optional[Dict]:
    """Get detailed device information using multiple methods"""
    info = {}
    
    # Method 1: Bluetooth system profiler - get the actual Gamepad-igs entry
    success, output, _ = run_command("system_profiler SPBluetoothDataType")
    if success and 'Gamepad-igs' in output:
        lines = output.split('\n')
        in_gamepad_section = False
        indent_level = 0
        
        for i, line in enumerate(lines):
            # Look for the Gamepad-igs entry - it should be indented and have colon
            if 'Gamepad-igs:' in line:
                in_gamepad_section = True
                # Get the indent level of the gamepad entry
                indent_level = len(line) - len(line.lstrip())
                continue
            
            if in_gamepad_section:
                current_indent = len(line) - len(line.lstrip()) if line.strip() else 999
                
                # Stop when we hit another device at same or higher level
                if line.strip() and current_indent <= indent_level and 'Gamepad-igs' not in line:
                    break
                
                # Only process lines that are part of Gamepad-igs section (indented more)
                if current_indent <= indent_level and line.strip() and ':' not in line:
                    continue
                
                # Extract info from this section
                if 'Address:' in line:
                    info['address'] = line.split('Address:')[1].strip()
                elif 'Vendor ID:' in line:
                    vid = line.split('Vendor ID:')[1].strip()
                    info['vendor_id'] = vid
                    info['vendor_id_hex'] = vid
                    # Convert to decimal
                    try:
                        if vid.startswith('0x') or vid.startswith('0X'):
                            info['vendor_id_decimal'] = str(int(vid, 16))
                        else:
                            info['vendor_id_decimal'] = vid
                    except:
                        pass
                elif 'Product ID:' in line:
                    pid = line.split('Product ID:')[1].strip()
                    info['product_id'] = pid
                    info['product_id_hex'] = pid
                    # Convert to decimal
                    try:
                        if pid.startswith('0x') or pid.startswith('0X'):
                            info['product_id_decimal'] = str(int(pid, 16))
                        else:
                            info['product_id_decimal'] = pid
                    except:
                        pass
                elif 'Firmware Version:' in line:
                    info['firmware_version'] = line.split('Firmware Version:')[1].strip()
                elif 'Minor Type:' in line:
                    info['device_type'] = line.split('Minor Type:')[1].strip()
                elif 'RSSI:' in line:
                    info['rssi'] = line.split('RSSI:')[1].strip()
    
    # Method 2: IORegistry (more detailed)
    success, output, _ = run_command("ioreg -p IOHID -w0 -l | grep -A 20 -i 'gamepad\\|joystick\\|controller'")
    if success and output:
        # Extract USB/Bluetooth identifiers
        vid_match = re.search(r'VendorID.*?(\d+)', output)
        pid_match = re.search(r'ProductID.*?(\d+)', output)
        if vid_match:
            info['vendor_id_decimal'] = vid_match.group(1)
        if pid_match:
            info['product_id_decimal'] = pid_match.group(1)
    
    # Method 3: USB device info (if connected via USB)
    success, output, _ = run_command("system_profiler SPUSBDataType | grep -A 20 -i 'gamepad\\|joystick\\|controller'")
    if success and output:
        # Extract manufacturer info
        manufacturer_match = re.search(r'Manufacturer:\s*(.+)', output)
        product_match = re.search(r'Product ID:\s*(.+)', output)
        if manufacturer_match:
            info['manufacturer_name'] = manufacturer_match.group(1).strip()
        if product_match:
            info['product_name'] = product_match.group(1).strip()
    
    return info if info else None

def identify_device_model(info: Dict) -> Dict:
    """Identify device model from vendor/product IDs"""
    model_info = {
        'manufacturer': 'Unknown',
        'model': 'Unknown',
        'likely_model': [],
        'update_urls': []
    }
    
    vendor_id = info.get('vendor_id', '').upper() or info.get('vendor_id_hex', '').upper()
    product_id = info.get('product_id', '').upper() or info.get('product_id_hex', '').upper()
    
    # Map vendor ID
    if vendor_id in VENDOR_ID_MAP:
        model_info['manufacturer'] = VENDOR_ID_MAP[vendor_id]
    elif vendor_id.startswith('0X'):
        # Try to look it up
        vid_dec = int(vendor_id, 16) if vendor_id.startswith('0X') else None
        if vid_dec:
            model_info['vendor_id_decimal'] = str(vid_dec)
    
    # Common gamepad identification patterns
    if vendor_id == '0x1949' or vendor_id.upper() == '0X1949':
        model_info['manufacturer'] = 'Generic/Unknown Chinese Manufacturer (Possible IGS/Third-party)'
        if info.get('product_id') == '0x0402':
            model_info['likely_model'] = [
                'IGS Gamepad (Vendor ID 0x1949, Product ID 0x0402)',
                'Generic Bluetooth Gamepad',
                'Third-party Bluetooth controller',
                'Possible AliExpress/Amazon generic gamepad'
            ]
            model_info['update_urls'] = [
                'Search: "0x1949 0x0402 gamepad firmware update"',
                'Search: "IGS gamepad firmware update"',
                'Check AliExpress/Amazon product page for firmware',
                'Contact seller for firmware update tool',
                'Search: "Gamepad-igs firmware update"'
            ]
        else:
            model_info['likely_model'] = [
                'Generic Bluetooth Gamepad',
                'Third-party Bluetooth controller'
            ]
            model_info['update_urls'] = [
                f'Search: "{vendor_id} {product_id} gamepad firmware update"',
                'Check manufacturer website if available'
            ]
    
    # Add product-specific info
    if info.get('manufacturer_name'):
        model_info['manufacturer'] = info['manufacturer_name']
    if info.get('product_name'):
        model_info['model'] = info['product_name']
    
    return model_info

def check_firmware_update_online(info: Dict, model_info: Dict) -> Dict:
    """Check for firmware updates online"""
    update_info = {
        'current_version': info.get('firmware_version', 'Unknown'),
        'latest_version': None,
        'update_available': False,
        'update_methods': [],
        'search_queries': [],
        'download_urls': []
    }
    
    # Build search queries
    queries = []
    
    if model_info['manufacturer'] != 'Unknown':
        queries.append(f"{model_info['manufacturer']} gamepad firmware update")
    
    if info.get('vendor_id') and info.get('product_id'):
        queries.append(f"Vendor ID {info['vendor_id']} Product ID {info['product_id']} firmware")
    
    if 'IGS' in str(model_info.get('likely_model', [])):
        queries.append("IGS gamepad firmware update")
        queries.append("Gamepad-igs firmware update")
    
    if info.get('address'):
        queries.append(f"Gamepad-igs {info['address']} firmware")
    
    update_info['search_queries'] = queries
    
    # Common update methods
    update_info['update_methods'] = [
        {
            'method': 'Windows PC Update Tool',
            'description': 'Most gamepads require Windows PC with manufacturer software',
            'steps': [
                '1. Connect gamepad via USB to Windows PC',
                '2. Download manufacturer firmware update tool',
                '3. Run the update utility',
                '4. Follow on-screen instructions'
            ]
        },
        {
            'method': 'Mobile App Update',
            'description': 'Some manufacturers provide mobile apps for updates',
            'steps': [
                '1. Install manufacturer mobile app',
                '2. Connect gamepad via Bluetooth',
                '3. Check for firmware updates in app settings',
                '4. Follow update instructions'
            ]
        },
        {
            'method': 'USB Connection Update',
            'description': 'USB connection is more reliable for firmware updates',
            'steps': [
                '1. Connect gamepad via USB cable',
                '2. Use manufacturer update tool',
                '3. Ensure stable connection during update',
                '4. Do not disconnect during update process'
            ]
        }
    ]
    
    # Manufacturer-specific update URLs
    if '0x1949' in str(info.get('vendor_id', '')):
        update_info['download_urls'] = [
            'Search Google: "IGS gamepad firmware update"',
            'Check AliExpress/Amazon product page for firmware',
            'Contact seller for firmware update tool',
            'Search for "0x1949 0x0402 firmware update"'
        ]
    
    return update_info

def search_usb_id_database(vendor_id: str, product_id: str) -> Dict:
    """Search USB ID database for device information"""
    result = {
        'found': False,
        'device_name': None,
        'manufacturer': None,
        'url': None
    }
    
    # Convert hex to decimal if needed
    try:
        if vendor_id.startswith('0x') or vendor_id.startswith('0X'):
            vid_dec = int(vendor_id, 16)
        else:
            vid_dec = int(vendor_id)
        
        if product_id.startswith('0x') or product_id.startswith('0X'):
            pid_dec = int(product_id, 16)
        else:
            pid_dec = int(product_id)
        
        # USB ID database URL
        result['url'] = f"https://devicehunt.com/all?vid={vid_dec:04X}&pid={pid_dec:04X}"
        result['usb_id_url'] = f"https://www.the-sz.com/products/usbid/index.php?v=0x{vid_dec:04X}&p=0x{pid_dec:04X}"
        
    except ValueError:
        pass
    
    return result

def print_update_report(info: Dict, model_info: Dict, update_info: Dict, usb_info: Dict):
    """Print comprehensive update report"""
    print("\n" + "="*70)
    print("?? FIRMWARE UPDATE CHECK REPORT")
    print("="*70)
    
    print("\n?? DEVICE INFORMATION:")
    print(f"   Name: Gamepad-igs")
    print(f"   Address: {info.get('address', 'Unknown')}")
    print(f"   Vendor ID: {info.get('vendor_id', 'Unknown')} (Decimal: {info.get('vendor_id_decimal', 'Unknown')})")
    print(f"   Product ID: {info.get('product_id', 'Unknown')} (Decimal: {info.get('product_id_decimal', 'Unknown')})")
    print(f"   Current Firmware: {info.get('firmware_version', 'Unknown')}")
    print(f"   Device Type: {info.get('device_type', 'Unknown')}")
    
    print("\n?? MANUFACTURER & MODEL:")
    print(f"   Manufacturer: {model_info['manufacturer']}")
    print(f"   Model: {model_info['model']}")
    if model_info['likely_model']:
        print(f"   Possible Models:")
        for model in model_info['likely_model']:
            print(f"     - {model}")
    
    print("\n?? CURRENT FIRMWARE STATUS:")
    print(f"   Version: {update_info['current_version']}")
    if update_info['latest_version']:
        print(f"   Latest Available: {update_info['latest_version']}")
        if update_info['update_available']:
            print("   ? Update Available!")
        else:
            print("   ? You're on the latest version")
    else:
        print("   ??  Could not determine latest version")
        print("   (Manual search required)")
    
    if usb_info.get('url'):
        print("\n?? USB ID DATABASE LINKS:")
        print(f"   Device Hunt: {usb_info['url']}")
        if usb_info.get('usb_id_url'):
            print(f"   USB ID Database: {usb_info['usb_id_url']}")
    
    print("\n?? RECOMMENDED SEARCH QUERIES:")
    for i, query in enumerate(update_info['search_queries'], 1):
        print(f"   {i}. {query}")
    
    print("\n?? UPDATE METHODS:")
    for i, method in enumerate(update_info['update_methods'], 1):
        print(f"\n   {i}. {method['method']}")
        print(f"      {method['description']}")
        for step in method['steps']:
            print(f"      {step}")
    
    if update_info.get('download_urls'):
        print("\n?? DOWNLOAD/UPDATE SOURCES:")
        for i, url in enumerate(update_info['download_urls'], 1):
            print(f"   {i}. {url}")
    
    print("\n" + "="*70)
    print("?? NEXT STEPS:")
    print("="*70)
    print("\n1. Search the recommended queries above")
    print("2. Check USB ID database links for device details")
    print("3. Look for manufacturer's official update tool")
    print("4. Check product page on AliExpress/Amazon/eBay")
    print("5. Contact seller/manufacturer for firmware update")
    print("\n??  IMPORTANT: Always use official update tools")
    print("   Incorrect firmware updates can brick your device!")

def main():
    print("="*70)
    print("?? GAMEPAD FIRMWARE UPDATE CHECKER")
    print("="*70)
    
    print("\n1?? Detecting device information...")
    info = get_detailed_device_info()
    
    if not info:
        print("? Could not detect gamepad device")
        print("   Make sure your gamepad is connected via Bluetooth or USB")
        return
    
    print("? Device information collected")
    
    print("\n2?? Identifying device model...")
    model_info = identify_device_model(info)
    print(f"? Manufacturer: {model_info['manufacturer']}")
    
    print("\n3?? Checking for firmware updates...")
    update_info = check_firmware_update_online(info, model_info)
    
    print("\n4?? Looking up USB ID database...")
    vendor_id = info.get('vendor_id', '') or info.get('vendor_id_hex', '')
    product_id = info.get('product_id', '') or info.get('product_id_hex', '')
    usb_info = search_usb_id_database(vendor_id, product_id)
    
    print("\n5?? Generating update report...")
    print_update_report(info, model_info, update_info, usb_info)
    
    # Save report to file
    report = {
        'timestamp': subprocess.check_output(['date', '+%Y-%m-%d %H:%M:%S']).decode().strip(),
        'device_info': info,
        'model_info': model_info,
        'update_info': update_info,
        'usb_info': usb_info
    }
    
    report_file = 'gamepad_firmware_update_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n?? Report saved to: {report_file}")

if __name__ == "__main__":
    main()
