#!/usr/bin/env python3
"""
Continuous Second Brain Android Project Monitoring
Runs monitoring every 5 minutes and updates implementation plan
"""

import os
import time
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path

class ContinuousMonitor:
    def __init__(self):
        self.monitoring_script = Path("/Users/Subho/PROJECT_MONITORING_SCRIPT.py")
        self.log_file = Path("/Users/Subho/.monitor_log.json")
        self.check_interval = 300  # 5 minutes

    def log_monitoring_result(self, result):
        """Log monitoring results with timestamp"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "overall_progress": result.get("overall_progress", 0),
            "component_count": result.get("component_count", 0),
            "new_files": result.get("new_files", 0),
            "features_detected": result.get("features_detected", [])
        }

        # Read existing log
        logs = []
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                logs = json.load(f)

        # Add new entry
        logs.append(log_entry)

        # Keep only last 100 entries
        logs = logs[-100:]

        # Save updated log
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2)

    def check_for_significant_changes(self, current_result):
        """Check if changes are significant enough to warrant attention"""
        if not self.log_file.exists():
            return True  # First run

        with open(self.log_file, 'r') as f:
            logs = json.load(f)

        if not logs:
            return True

        last_result = logs[-1]

        # Significant changes criteria
        progress_change = abs(current_result.get("overall_progress", 0) - last_result.get("overall_progress", 0))
        new_files_added = current_result.get("new_files", 0) > 0
        new_features = len(current_result.get("features_detected", [])) > len(last_result.get("features_detected", []))

        return progress_change >= 5.0 or new_files_added or new_features

    def run_continuous_monitoring(self):
        """Run continuous monitoring loop"""
        print(f"🔄 Starting continuous monitoring at {datetime.now()}")
        print(f"📊 Checking every {self.check_interval/60} minutes...")

        while True:
            try:
                print(f"\n🔍 Running monitoring cycle at {datetime.now()}")

                # Run monitoring script
                result = subprocess.run(
                    ["python3", str(self.monitoring_script)],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    # Parse result from stdout (simple extraction)
                    output_lines = result.stdout.strip().split('\n')
                    progress_line = [line for line in output_lines if "Overall Progress:" in line]
                    files_line = [line for line in output_lines if "Total Kotlin files:" in line]

                    monitoring_result = {}
                    if progress_line:
                        progress_str = progress_line[0].split("Overall Progress: ")[1].rstrip('%')
                        monitoring_result["overall_progress"] = float(progress_str)

                    if files_line:
                        files_str = files_line[0].split("Total Kotlin files: ")[1]
                        monitoring_result["component_count"] = int(files_str)

                    # Check for significant changes
                    if self.check_for_significant_changes(monitoring_result):
                        print("🚨 Significant changes detected!")
                        print(f"📈 Progress: {monitoring_result.get('overall_progress', 0):.1f}%")
                        print(f"📁 Files: {monitoring_result.get('component_count', 0)}")
                    else:
                        print("✅ No significant changes detected")

                    # Log the result
                    self.log_monitoring_result(monitoring_result)

                else:
                    print(f"❌ Monitoring script failed: {result.stderr}")

            except Exception as e:
                print(f"🔥 Error during monitoring: {e}")

            # Wait for next cycle
            print(f"⏳ Sleeping for {self.check_interval/60} minutes...")
            time.sleep(self.check_interval)

    def generate_progress_report(self):
        """Generate a progress report from the logs"""
        if not self.log_file.exists():
            return "No monitoring data available"

        with open(self.log_file, 'r') as f:
            logs = json.load(f)

        if not logs:
            return "No monitoring data available"

        # Get recent logs (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_logs = [
            log for log in logs
            if datetime.fromisoformat(log["timestamp"]) > cutoff_time
        ]

        if not recent_logs:
            return "No recent monitoring data available"

        # Generate report
        latest = recent_logs[-1]
        earliest = recent_logs[0]

        progress_change = latest["overall_progress"] - earliest["overall_progress"]
        files_change = latest["component_count"] - earliest["component_count"]

        report = f"""
📊 24-Hour Progress Report ({datetime.now().strftime('%Y-%m-%d %H:%M')})

Current Status:
- Overall Progress: {latest['overall_progress']:.1f}%
- Total Files: {latest['component_count']}

Changes in Last 24 Hours:
- Progress Change: {progress_change:+.1f}%
- Files Added: {files_change:+d}
- Monitoring Cycles: {len(recent_logs)}

Latest Features Detected:
{chr(10).join(f'- {feature}' for feature in latest.get('features_detected', []))}

Trend: {'📈 Increasing' if progress_change > 0 else '📉 Stable' if progress_change == 0 else '📉 Decreasing'}
"""
        return report

def main():
    """Main function"""
    import sys

    monitor = ContinuousMonitor()

    if len(sys.argv) > 1 and sys.argv[1] == "report":
        print(monitor.generate_progress_report())
    else:
        monitor.run_continuous_monitoring()

if __name__ == "__main__":
    main()