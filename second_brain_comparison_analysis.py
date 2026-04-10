#!/usr/bin/env python3
"""
Second Brain V6 Android App - Advanced Screenshot Comparison & Analysis Tool

This script provides automated visual comparison, regression testing,
and UI validation for the Second Brain Android app screenshots.
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import hashlib

try:
    from PIL import Image, ImageDraw, ImageFont, ImageChops
    import cv2
    import numpy as np
    from skimage.metrics import structural_similarity as ssim
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError as e:
    print(f"Missing required packages. Install with:")
    print("pip install Pillow opencv-python scikit-image matplotlib seaborn numpy")
    print(f"Error: {e}")
    exit(1)

class ScreenshotAnalyzer:
    """Advanced screenshot analysis and comparison tool."""

    def __init__(self, base_dir: str = "second_brain_screenshots"):
        self.base_dir = Path(base_dir)
        self.results = {}
        self.comparison_threshold = 0.95  # SSIM threshold for "identical" images

    def find_test_sessions(self) -> List[Path]:
        """Find all test session directories."""
        if not self.base_dir.exists():
            print(f"Base directory not found: {self.base_dir}")
            return []

        sessions = []
        for item in self.base_dir.iterdir():
            if item.is_dir() and item.name.startswith("test_session_"):
                sessions.append(item)

        return sorted(sessions, key=lambda x: x.name)

    def load_device_info(self, session_dir: Path) -> Dict:
        """Load device information from test session."""
        info_file = session_dir / "device_info.txt"
        device_info = {}

        if info_file.exists():
            with open(info_file, 'r') as f:
                for line in f:
                    if ':' in line and not line.startswith('='):
                        key, value = line.strip().split(':', 1)
                        device_info[key.strip()] = value.strip()

        return device_info

    def calculate_image_hash(self, image_path: Path) -> str:
        """Calculate MD5 hash of image for quick comparison."""
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def compare_images(self, img1_path: Path, img2_path: Path) -> Dict:
        """Compare two images using multiple metrics."""
        try:
            # Load images
            img1 = cv2.imread(str(img1_path))
            img2 = cv2.imread(str(img2_path))

            if img1 is None or img2 is None:
                return {"error": "Could not load images"}

            # Resize to same dimensions if different
            if img1.shape != img2.shape:
                img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

            # Convert to grayscale for SSIM
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

            # Calculate SSIM
            ssim_score = ssim(gray1, gray2)

            # Calculate MSE
            mse = np.mean((img1 - img2) ** 2)

            # Calculate histogram comparison
            hist1 = cv2.calcHist([img1], [0, 1, 2], None, [256, 256, 256], [0, 256, 0, 256, 0, 256])
            hist2 = cv2.calcHist([img2], [0, 1, 2], None, [256, 256, 256], [0, 256, 0, 256, 0, 256])
            hist_correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

            return {
                "ssim": float(ssim_score),
                "mse": float(mse),
                "histogram_correlation": float(hist_correlation),
                "identical": ssim_score > self.comparison_threshold,
                "similarity_percentage": float(ssim_score * 100)
            }

        except Exception as e:
            return {"error": str(e)}

    def create_diff_image(self, img1_path: Path, img2_path: Path, output_path: Path) -> bool:
        """Create a visual difference image highlighting changes."""
        try:
            img1 = Image.open(img1_path).convert('RGB')
            img2 = Image.open(img2_path).convert('RGB')

            # Resize to same dimensions
            if img1.size != img2.size:
                img2 = img2.resize(img1.size)

            # Create difference image
            diff = ImageChops.difference(img1, img2)

            # Enhance differences
            diff = diff.point(lambda x: x * 3 if x < 128 else 255)

            # Create composite showing original, new, and diff
            composite_width = img1.width * 3
            composite = Image.new('RGB', (composite_width, img1.height))

            composite.paste(img1, (0, 0))
            composite.paste(img2, (img1.width, 0))
            composite.paste(diff, (img1.width * 2, 0))

            # Add labels
            draw = ImageDraw.Draw(composite)
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()

            draw.text((10, 10), "Original", fill=(255, 0, 0), font=font)
            draw.text((img1.width + 10, 10), "New", fill=(0, 255, 0), font=font)
            draw.text((img1.width * 2 + 10, 10), "Diff", fill=(0, 0, 255), font=font)

            composite.save(output_path)
            return True

        except Exception as e:
            print(f"Error creating diff image: {e}")
            return False

    def analyze_single_session(self, session_dir: Path) -> Dict:
        """Analyze a single test session."""
        print(f"Analyzing session: {session_dir.name}")

        device_info = self.load_device_info(session_dir)

        analysis = {
            "session_name": session_dir.name,
            "timestamp": session_dir.name.split("_")[-2:],
            "device_info": device_info,
            "screenshots": {
                "portrait": [],
                "landscape": []
            },
            "metadata": {}
        }

        # Analyze portrait screenshots
        portrait_dir = session_dir / "portrait"
        if portrait_dir.exists():
            for img_file in sorted(portrait_dir.glob("*.png")):
                img_info = {
                    "filename": img_file.name,
                    "path": str(img_file),
                    "size": img_file.stat().st_size,
                    "hash": self.calculate_image_hash(img_file)
                }

                # Load metadata if available
                metadata_file = portrait_dir / f"{img_file.stem}_metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        img_info["metadata"] = json.load(f)

                analysis["screenshots"]["portrait"].append(img_info)

        # Analyze landscape screenshots
        landscape_dir = session_dir / "landscape"
        if landscape_dir.exists():
            for img_file in sorted(landscape_dir.glob("*.png")):
                img_info = {
                    "filename": img_file.name,
                    "path": str(img_file),
                    "size": img_file.stat().st_size,
                    "hash": self.calculate_image_hash(img_file)
                }

                # Load metadata if available
                metadata_file = landscape_dir / f"{img_file.stem}_metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        img_info["metadata"] = json.load(f)

                analysis["screenshots"]["landscape"].append(img_info)

        return analysis

    def compare_sessions(self, session1: Dict, session2: Dict, output_dir: Path) -> Dict:
        """Compare two test sessions for regressions."""
        print(f"Comparing sessions: {session1['session_name']} vs {session2['session_name']}")

        comparison = {
            "baseline_session": session1["session_name"],
            "comparison_session": session2["session_name"],
            "device_comparison": {
                "same_device": session1["device_info"].get("Model") == session2["device_info"].get("Model"),
                "same_android": session1["device_info"].get("Android Version") == session2["device_info"].get("Android Version")
            },
            "screen_comparisons": {
                "portrait": [],
                "landscape": []
            },
            "summary": {
                "total_screens": 0,
                "identical_screens": 0,
                "changed_screens": 0,
                "missing_screens": 0,
                "new_screens": 0
            }
        }

        # Compare portrait screenshots
        for orientation in ["portrait", "landscape"]:
            baseline_screens = {img["filename"]: img for img in session1["screenshots"][orientation]}
            comparison_screens = {img["filename"]: img for img in session2["screenshots"][orientation]}

            all_screen_names = set(baseline_screens.keys()) | set(comparison_screens.keys())

            for screen_name in all_screen_names:
                comparison["summary"]["total_screens"] += 1

                if screen_name in baseline_screens and screen_name in comparison_screens:
                    # Both sessions have this screen
                    baseline_img = baseline_screens[screen_name]
                    comparison_img = comparison_screens[screen_name]

                    # Compare images
                    img_comparison = self.compare_images(
                        Path(baseline_img["path"]),
                        Path(comparison_img["path"])
                    )

                    screen_result = {
                        "screen_name": screen_name,
                        "status": "identical" if img_comparison.get("identical", False) else "changed",
                        "comparison_metrics": img_comparison,
                        "baseline_hash": baseline_img["hash"],
                        "comparison_hash": comparison_img["hash"]
                    }

                    # Create diff image if changed
                    if not img_comparison.get("identical", False):
                        diff_output = output_dir / f"diff_{orientation}_{screen_name}"
                        self.create_diff_image(
                            Path(baseline_img["path"]),
                            Path(comparison_img["path"]),
                            diff_output
                        )
                        screen_result["diff_image"] = str(diff_output)
                        comparison["summary"]["changed_screens"] += 1
                    else:
                        comparison["summary"]["identical_screens"] += 1

                elif screen_name in baseline_screens:
                    # Screen missing in comparison session
                    screen_result = {
                        "screen_name": screen_name,
                        "status": "missing",
                        "baseline_hash": baseline_screens[screen_name]["hash"]
                    }
                    comparison["summary"]["missing_screens"] += 1

                else:
                    # New screen in comparison session
                    screen_result = {
                        "screen_name": screen_name,
                        "status": "new",
                        "comparison_hash": comparison_screens[screen_name]["hash"]
                    }
                    comparison["summary"]["new_screens"] += 1

                comparison["screen_comparisons"][orientation].append(screen_result)

        return comparison

    def generate_comparison_report(self, comparison: Dict, output_file: Path):
        """Generate detailed HTML comparison report."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Second Brain UI Comparison Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; }}
        .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .metric-card {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .screen-comparison {{ border: 1px solid #ddd; border-radius: 8px; margin: 15px 0; padding: 15px; }}
        .status-identical {{ border-left: 4px solid #27ae60; }}
        .status-changed {{ border-left: 4px solid #e74c3c; }}
        .status-missing {{ border-left: 4px solid #f39c12; }}
        .status-new {{ border-left: 4px solid #3498db; }}
        .diff-image {{ max-width: 100%; border: 1px solid #ccc; margin: 10px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f5f5f5; font-weight: bold; }}
        .percentage {{ font-weight: bold; }}
        .high {{ color: #27ae60; }}
        .medium {{ color: #f39c12; }}
        .low {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Second Brain V6 UI Comparison Report</h1>
        <p>Baseline: {comparison['baseline_session']}</p>
        <p>Comparison: {comparison['comparison_session']}</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="summary">
        <h2>Test Summary</h2>
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">{comparison['summary']['total_screens']}</div>
                <div>Total Screens</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #27ae60;">{comparison['summary']['identical_screens']}</div>
                <div>Identical Screens</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #e74c3c;">{comparison['summary']['changed_screens']}</div>
                <div>Changed Screens</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #f39c12;">{comparison['summary']['missing_screens']}</div>
                <div>Missing Screens</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #3498db;">{comparison['summary']['new_screens']}</div>
                <div>New Screens</div>
            </div>
        </div>
    </div>

    <div class="device-info">
        <h2>Device Compatibility</h2>
        <p><strong>Same Device Model:</strong> {'✅ Yes' if comparison['device_comparison']['same_device'] else '❌ No'}</p>
        <p><strong>Same Android Version:</strong> {'✅ Yes' if comparison['device_comparison']['same_android'] else '❌ No'}</p>
    </div>
"""

        # Add screen comparisons
        for orientation in ["portrait", "landscape"]:
            html_content += f"""
    <h2>{orientation.title()} Screen Comparisons</h2>
    <table>
        <thead>
            <tr>
                <th>Screen Name</th>
                <th>Status</th>
                <th>Similarity</th>
                <th>SSIM Score</th>
                <th>MSE</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
"""

            for screen in comparison["screen_comparisons"][orientation]:
                status = screen["status"]
                status_class = f"status-{status}"

                similarity = "N/A"
                ssim_score = "N/A"
                mse = "N/A"

                if "comparison_metrics" in screen:
                    metrics = screen["comparison_metrics"]
                    if "similarity_percentage" in metrics:
                        sim_pct = metrics["similarity_percentage"]
                        similarity = f"{sim_pct:.1f}%"
                        css_class = "high" if sim_pct > 95 else "medium" if sim_pct > 80 else "low"
                        similarity = f'<span class="percentage {css_class}">{similarity}</span>'

                    if "ssim" in metrics:
                        ssim_score = f"{metrics['ssim']:.4f}"

                    if "mse" in metrics:
                        mse = f"{metrics['mse']:.2f}"

                actions = ""
                if "diff_image" in screen:
                    actions = f'<a href="{screen["diff_image"]}" target="_blank">View Diff</a>'

                html_content += f"""
            <tr class="{status_class}">
                <td>{screen['screen_name']}</td>
                <td>{status.title()}</td>
                <td>{similarity}</td>
                <td>{ssim_score}</td>
                <td>{mse}</td>
                <td>{actions}</td>
            </tr>
"""

            html_content += """
        </tbody>
    </table>
"""

        html_content += """
    <div class="footer" style="margin-top: 40px; padding: 20px; background-color: #f8f9fa; border-radius: 5px;">
        <h3>How to Interpret Results</h3>
        <ul>
            <li><strong>Identical:</strong> Screenshots are visually identical (SSIM > 0.95)</li>
            <li><strong>Changed:</strong> Visual differences detected between versions</li>
            <li><strong>Missing:</strong> Screen exists in baseline but not in comparison</li>
            <li><strong>New:</strong> Screen exists in comparison but not in baseline</li>
        </ul>
        <p><strong>SSIM (Structural Similarity Index):</strong> Values closer to 1.0 indicate higher similarity</p>
        <p><strong>MSE (Mean Squared Error):</strong> Lower values indicate more similar images</p>
    </div>
</body>
</html>
"""

        with open(output_file, 'w') as f:
            f.write(html_content)

    def run_regression_analysis(self, baseline_session: Optional[str] = None):
        """Run complete regression analysis comparing sessions."""
        sessions = self.find_test_sessions()

        if len(sessions) < 2:
            print("Need at least 2 test sessions for comparison")
            return

        print(f"Found {len(sessions)} test sessions")

        # Analyze all sessions
        session_analyses = []
        for session_dir in sessions:
            analysis = self.analyze_single_session(session_dir)
            session_analyses.append(analysis)

        # Determine baseline and comparison sessions
        if baseline_session:
            baseline = next((s for s in session_analyses if baseline_session in s["session_name"]), None)
            if not baseline:
                print(f"Baseline session '{baseline_session}' not found")
                return
            comparison = session_analyses[-1] if session_analyses[-1] != baseline else session_analyses[-2]
        else:
            # Use two most recent sessions
            baseline = session_analyses[-2]
            comparison = session_analyses[-1]

        # Create output directory for comparison results
        output_dir = self.base_dir / f"comparison_{baseline['session_name']}_vs_{comparison['session_name']}"
        output_dir.mkdir(exist_ok=True)

        # Perform comparison
        comparison_result = self.compare_sessions(baseline, comparison, output_dir)

        # Generate reports
        report_file = output_dir / "comparison_report.html"
        self.generate_comparison_report(comparison_result, report_file)

        # Save JSON report
        json_file = output_dir / "comparison_data.json"
        with open(json_file, 'w') as f:
            json.dump(comparison_result, f, indent=2)

        print(f"\n=== Regression Analysis Complete ===")
        print(f"Baseline Session: {baseline['session_name']}")
        print(f"Comparison Session: {comparison['session_name']}")
        print(f"Total Screens Analyzed: {comparison_result['summary']['total_screens']}")
        print(f"Identical Screens: {comparison_result['summary']['identical_screens']}")
        print(f"Changed Screens: {comparison_result['summary']['changed_screens']}")
        print(f"Missing Screens: {comparison_result['summary']['missing_screens']}")
        print(f"New Screens: {comparison_result['summary']['new_screens']}")
        print(f"\nDetailed report: {report_file}")

        return comparison_result

def main():
    parser = argparse.ArgumentParser(description="Second Brain V6 Screenshot Analysis Tool")
    parser.add_argument("--base-dir", default="second_brain_screenshots", help="Base directory for screenshots")
    parser.add_argument("--baseline", help="Specific baseline session name to compare against")
    parser.add_argument("--action", choices=["analyze", "compare", "list"], default="compare", help="Action to perform")

    args = parser.parse_args()

    analyzer = ScreenshotAnalyzer(args.base_dir)

    if args.action == "list":
        sessions = analyzer.find_test_sessions()
        print("Available test sessions:")
        for session in sessions:
            print(f"  - {session.name}")

    elif args.action == "analyze":
        sessions = analyzer.find_test_sessions()
        for session_dir in sessions:
            analysis = analyzer.analyze_single_session(session_dir)
            print(f"\nSession: {analysis['session_name']}")
            print(f"Device: {analysis['device_info'].get('Model', 'Unknown')}")
            print(f"Portrait Screenshots: {len(analysis['screenshots']['portrait'])}")
            print(f"Landscape Screenshots: {len(analysis['screenshots']['landscape'])}")

    elif args.action == "compare":
        analyzer.run_regression_analysis(args.baseline)

if __name__ == "__main__":
    main()