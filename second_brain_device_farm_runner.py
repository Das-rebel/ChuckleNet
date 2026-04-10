#!/usr/bin/env python3
"""
Second Brain V6 Android App - Multi-Device Testing Orchestrator

This script orchestrates UI testing across multiple Android devices/emulators
for comprehensive device compatibility validation.
"""

import subprocess
import json
import threading
import time
import argparse
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
import queue

class DeviceFarmOrchestrator:
    """Orchestrates UI testing across multiple Android devices."""

    def __init__(self, app_package: str = "com.secondbrain.app"):
        self.app_package = app_package
        self.results = {}
        self.test_queue = queue.Queue()
        self.devices = []

    def discover_devices(self) -> List[Dict]:
        """Discover all connected Android devices and emulators."""
        print("Discovering connected devices...")

        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')[1:]  # Skip header

            devices = []
            for line in lines:
                if 'device' in line and not line.startswith('*'):
                    device_id = line.split()[0]
                    device_info = self.get_device_info(device_id)
                    devices.append(device_info)

            print(f"Found {len(devices)} devices")
            for device in devices:
                print(f"  - {device['id']}: {device['model']} (Android {device['android_version']})")

            return devices

        except subprocess.CalledProcessError as e:
            print(f"Error discovering devices: {e}")
            return []

    def get_device_info(self, device_id: str) -> Dict:
        """Get detailed information about a device."""
        try:
            # Get device properties
            props = {}
            for prop in ['ro.product.model', 'ro.build.version.release', 'ro.product.manufacturer',
                        'ro.build.version.sdk', 'ro.product.device']:
                result = subprocess.run(['adb', '-s', device_id, 'shell', 'getprop', prop],
                                      capture_output=True, text=True, check=True)
                props[prop] = result.stdout.strip()

            # Get screen info
            screen_size_result = subprocess.run(['adb', '-s', device_id, 'shell', 'wm', 'size'],
                                              capture_output=True, text=True, check=True)
            screen_size = screen_size_result.stdout.split(':')[-1].strip() if screen_size_result.stdout else "Unknown"

            density_result = subprocess.run(['adb', '-s', device_id, 'shell', 'wm', 'density'],
                                          capture_output=True, text=True, check=True)
            density = density_result.stdout.split(':')[-1].strip() if density_result.stdout else "Unknown"

            return {
                'id': device_id,
                'model': props.get('ro.product.model', 'Unknown'),
                'manufacturer': props.get('ro.product.manufacturer', 'Unknown'),
                'android_version': props.get('ro.build.version.release', 'Unknown'),
                'sdk_version': props.get('ro.build.version.sdk', 'Unknown'),
                'device_name': props.get('ro.product.device', 'Unknown'),
                'screen_size': screen_size,
                'density': density,
                'is_emulator': 'emulator' in device_id
            }

        except subprocess.CalledProcessError as e:
            print(f"Error getting device info for {device_id}: {e}")
            return {
                'id': device_id,
                'model': 'Unknown',
                'manufacturer': 'Unknown',
                'android_version': 'Unknown',
                'error': str(e)
            }

    def prepare_device(self, device_id: str) -> bool:
        """Prepare a device for testing."""
        try:
            print(f"Preparing device {device_id}...")

            # Wake up device
            subprocess.run(['adb', '-s', device_id, 'shell', 'input', 'keyevent', 'KEYCODE_WAKEUP'],
                          check=True, capture_output=True)

            # Unlock device (basic swipe up)
            subprocess.run(['adb', '-s', device_id, 'shell', 'input', 'swipe', '360', '1000', '360', '300'],
                          check=True, capture_output=True)

            # Set screen timeout to 30 minutes
            subprocess.run(['adb', '-s', device_id, 'shell', 'settings', 'put', 'system', 'screen_off_timeout', '1800000'],
                          check=True, capture_output=True)

            # Force stop app if running
            subprocess.run(['adb', '-s', device_id, 'shell', 'am', 'force-stop', self.app_package],
                          check=True, capture_output=True)

            return True

        except subprocess.CalledProcessError as e:
            print(f"Error preparing device {device_id}: {e}")
            return False

    def run_test_on_device(self, device_info: Dict, test_config: Dict) -> Dict:
        """Run UI test suite on a specific device."""
        device_id = device_info['id']
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"Starting test on {device_id} ({device_info['model']})...")

        result = {
            'device_id': device_id,
            'device_info': device_info,
            'test_config': test_config,
            'timestamp': timestamp,
            'status': 'running',
            'screenshots': [],
            'errors': [],
            'start_time': datetime.now().isoformat()
        }

        try:
            # Prepare device
            if not self.prepare_device(device_id):
                result['status'] = 'failed'
                result['errors'].append('Device preparation failed')
                return result

            # Create device-specific output directory
            output_dir = Path(f"device_farm_results/{device_id}_{timestamp}")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save device info
            with open(output_dir / "device_info.json", 'w') as f:
                json.dump(device_info, f, indent=2)

            # Run the main test script for this device
            test_script_path = Path("second_brain_ui_test_suite.sh")
            if not test_script_path.exists():
                result['status'] = 'failed'
                result['errors'].append('Test script not found')
                return result

            # Prepare environment variables for the test script
            env = {
                'ADB_DEVICE_ID': device_id,
                'SCREENSHOT_DIR': str(output_dir.parent),
                'TEST_SESSION_NAME': f"{device_id}_{timestamp}"
            }

            # Run test script with device-specific parameters
            cmd = [
                'bash', str(test_script_path),
                test_config.get('test_type', 'full')
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**env, **dict(os.environ) if 'os' in globals() else {}}
            )

            stdout, stderr = process.communicate(timeout=test_config.get('timeout', 1800))  # 30 min timeout

            if process.returncode == 0:
                result['status'] = 'completed'
                result['stdout'] = stdout
            else:
                result['status'] = 'failed'
                result['stderr'] = stderr
                result['errors'].append(f'Test script failed with code {process.returncode}')

            # Collect screenshots
            screenshots = list(output_dir.glob("**/*.png"))
            result['screenshots'] = [str(s) for s in screenshots]
            result['screenshot_count'] = len(screenshots)

        except subprocess.TimeoutExpired:
            process.kill()
            result['status'] = 'timeout'
            result['errors'].append('Test timed out')

        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(str(e))

        finally:
            result['end_time'] = datetime.now().isoformat()
            result['duration'] = (datetime.fromisoformat(result['end_time']) -
                                datetime.fromisoformat(result['start_time'])).total_seconds()

        print(f"Test completed on {device_id}: {result['status']}")
        return result

    def run_parallel_tests(self, devices: List[Dict], test_config: Dict, max_workers: int = None) -> Dict:
        """Run tests on multiple devices in parallel."""
        if not devices:
            print("No devices available for testing")
            return {}

        if max_workers is None:
            max_workers = min(len(devices), 4)  # Limit to 4 concurrent tests

        print(f"Running tests on {len(devices)} devices with {max_workers} workers...")

        results = {}
        start_time = datetime.now()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all test jobs
            future_to_device = {
                executor.submit(self.run_test_on_device, device, test_config): device
                for device in devices
            }

            # Collect results as they complete
            for future in as_completed(future_to_device):
                device = future_to_device[future]
                try:
                    result = future.result()
                    results[device['id']] = result
                except Exception as e:
                    results[device['id']] = {
                        'device_id': device['id'],
                        'device_info': device,
                        'status': 'error',
                        'errors': [str(e)],
                        'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S")
                    }

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Generate summary
        summary = {
            'total_devices': len(devices),
            'successful_tests': sum(1 for r in results.values() if r['status'] == 'completed'),
            'failed_tests': sum(1 for r in results.values() if r['status'] == 'failed'),
            'error_tests': sum(1 for r in results.values() if r['status'] == 'error'),
            'timeout_tests': sum(1 for r in results.values() if r['status'] == 'timeout'),
            'total_duration': duration,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }

        print(f"\n=== Device Farm Test Summary ===")
        print(f"Total Devices: {summary['total_devices']}")
        print(f"Successful: {summary['successful_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Errors: {summary['error_tests']}")
        print(f"Timeouts: {summary['timeout_tests']}")
        print(f"Duration: {duration:.2f} seconds")

        return {
            'summary': summary,
            'results': results
        }

    def generate_device_farm_report(self, test_results: Dict, output_path: Path):
        """Generate comprehensive device farm test report."""
        summary = test_results['summary']
        results = test_results['results']

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Second Brain V6 - Device Farm Test Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f7fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .summary-card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }}
        .metric-value {{ font-size: 36px; font-weight: bold; margin-bottom: 8px; }}
        .metric-label {{ color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .device-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 25px; }}
        .device-card {{ background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }}
        .device-header {{ padding: 20px; border-bottom: 1px solid #eee; }}
        .device-body {{ padding: 20px; }}
        .status-completed {{ border-left: 5px solid #10b981; }}
        .status-failed {{ border-left: 5px solid #ef4444; }}
        .status-error {{ border-left: 5px solid #f59e0b; }}
        .status-timeout {{ border-left: 5px solid #8b5cf6; }}
        .status-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; text-transform: uppercase; }}
        .badge-completed {{ background-color: #d1fae5; color: #065f46; }}
        .badge-failed {{ background-color: #fee2e2; color: #991b1b; }}
        .badge-error {{ background-color: #fef3c7; color: #92400e; }}
        .badge-timeout {{ background-color: #e9d5ff; color: #581c87; }}
        .device-specs {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 15px 0; font-size: 14px; }}
        .spec-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f3f4f6; }}
        .screenshot-gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 15px; margin-top: 20px; }}
        .screenshot-thumb {{ width: 100%; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .error-list {{ background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 15px; margin: 15px 0; }}
        .error-item {{ color: #dc2626; margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Second Brain V6 - Device Farm Test Report</h1>
            <p>Multi-device UI testing results across Android ecosystem</p>
            <p><strong>Test Completed:</strong> {datetime.fromisoformat(summary['end_time']).strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Total Duration:</strong> {summary['total_duration']:.1f} seconds</p>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <div class="metric-value" style="color: #3b82f6;">{summary['total_devices']}</div>
                <div class="metric-label">Total Devices</div>
            </div>
            <div class="summary-card">
                <div class="metric-value" style="color: #10b981;">{summary['successful_tests']}</div>
                <div class="metric-label">Successful</div>
            </div>
            <div class="summary-card">
                <div class="metric-value" style="color: #ef4444;">{summary['failed_tests']}</div>
                <div class="metric-label">Failed</div>
            </div>
            <div class="summary-card">
                <div class="metric-value" style="color: #f59e0b;">{summary['error_tests']}</div>
                <div class="metric-label">Errors</div>
            </div>
            <div class="summary-card">
                <div class="metric-value" style="color: #8b5cf6;">{summary['timeout_tests']}</div>
                <div class="metric-label">Timeouts</div>
            </div>
        </div>

        <h2>Device Test Results</h2>
        <div class="device-grid">
"""

        for device_id, result in results.items():
            device_info = result['device_info']
            status = result['status']

            status_class = f"status-{status}"
            badge_class = f"badge-{status}"

            html_content += f"""
            <div class="device-card {status_class}">
                <div class="device-header">
                    <h3>{device_info['model']}</h3>
                    <span class="status-badge {badge_class}">{status}</span>
                </div>
                <div class="device-body">
                    <div class="device-specs">
                        <div class="spec-item">
                            <span>Device ID:</span>
                            <span>{device_id}</span>
                        </div>
                        <div class="spec-item">
                            <span>Manufacturer:</span>
                            <span>{device_info.get('manufacturer', 'Unknown')}</span>
                        </div>
                        <div class="spec-item">
                            <span>Android Version:</span>
                            <span>{device_info.get('android_version', 'Unknown')}</span>
                        </div>
                        <div class="spec-item">
                            <span>Screen Size:</span>
                            <span>{device_info.get('screen_size', 'Unknown')}</span>
                        </div>
                        <div class="spec-item">
                            <span>Density:</span>
                            <span>{device_info.get('density', 'Unknown')}</span>
                        </div>
                        <div class="spec-item">
                            <span>Type:</span>
                            <span>{'Emulator' if device_info.get('is_emulator') else 'Physical Device'}</span>
                        </div>
                    </div>
"""

            if result.get('errors'):
                html_content += """
                    <div class="error-list">
                        <h4>Errors:</h4>
"""
                for error in result['errors']:
                    html_content += f'<div class="error-item">• {error}</div>'

                html_content += "</div>"

            if result.get('screenshots'):
                html_content += f"""
                    <h4>Screenshots ({len(result['screenshots'])} captured)</h4>
                    <p>Screenshots saved to device-specific directory</p>
"""

            if result.get('duration'):
                html_content += f"<p><strong>Test Duration:</strong> {result['duration']:.1f} seconds</p>"

            html_content += """
                </div>
            </div>
"""

        html_content += """
        </div>

        <div style="margin-top: 50px; padding: 30px; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h2>Device Compatibility Matrix</h2>
            <p>This report shows UI test results across different Android devices and versions. Use this data to:</p>
            <ul>
                <li>Identify device-specific UI issues</li>
                <li>Validate responsive design across screen sizes</li>
                <li>Ensure Android version compatibility</li>
                <li>Compare performance across device types</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

        with open(output_path, 'w') as f:
            f.write(html_content)

    def run_device_farm_test(self, test_config: Dict):
        """Run complete device farm test suite."""
        devices = self.discover_devices()

        if not devices:
            print("No devices found for testing")
            return

        # Filter devices if specified
        if test_config.get('device_filter'):
            devices = [d for d in devices if test_config['device_filter'] in d['model'].lower()]

        # Run tests
        results = self.run_parallel_tests(devices, test_config)

        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(f"device_farm_results/farm_run_{timestamp}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save raw results
        with open(output_dir / "raw_results.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)

        # Generate report
        report_path = output_dir / "device_farm_report.html"
        self.generate_device_farm_report(results, report_path)

        print(f"\nDevice farm test completed!")
        print(f"Results saved to: {output_dir}")
        print(f"Report available at: {report_path}")

        return results


def main():
    parser = argparse.ArgumentParser(description="Second Brain V6 Device Farm Testing")
    parser.add_argument("--app-package", default="com.secondbrain.app", help="App package name")
    parser.add_argument("--test-type", default="full", choices=["full", "portrait", "landscape", "navigation"],
                       help="Type of test to run")
    parser.add_argument("--timeout", type=int, default=1800, help="Timeout per device in seconds")
    parser.add_argument("--max-workers", type=int, help="Maximum parallel test workers")
    parser.add_argument("--device-filter", help="Filter devices by model name")
    parser.add_argument("--list-devices", action="store_true", help="List available devices and exit")

    args = parser.parse_args()

    orchestrator = DeviceFarmOrchestrator(args.app_package)

    if args.list_devices:
        devices = orchestrator.discover_devices()
        if devices:
            print("\nAvailable devices:")
            for device in devices:
                print(f"  {device['id']}: {device['model']} - Android {device['android_version']}")
        return

    test_config = {
        'test_type': args.test_type,
        'timeout': args.timeout,
        'device_filter': args.device_filter
    }

    orchestrator.run_device_farm_test(test_config)

if __name__ == "__main__":
    import os
    main()