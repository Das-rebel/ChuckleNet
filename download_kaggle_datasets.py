#!/usr/bin/env python3
"""
Automated Kaggle Dataset Acquisition for Biosemotic Laughter Detection
Downloads all priority humor detection datasets with validation
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import subprocess

class KaggleDatasetDownloader:
    """Automated Kaggle dataset downloader with validation"""

    def __init__(self):
        self.download_dir = Path('~/datasets/kaggle_humor').expanduser()
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.datasets = [
            {
                'name': 'short-jokes',
                'path': 'abhinavmoudgil95/short-jokes',
                'target_size': 200000,
                'description': '200,000+ short jokes with user ratings',
                'priority': 'HIGH'
            },
            {
                'name': 'reddit-humor',
                'path': 'ernestitus/reddit-humor-dataset',
                'target_size': 50000,
                'description': '50,000+ Reddit posts labeled as humor/non-humor',
                'priority': 'HIGH'
            },
            {
                'name': 'twitter-humor',
                'path': 'wit真空/humor-detection',
                'target_size': 100000,
                'description': '100,000+ tweets with humor labels',
                'priority': 'MEDIUM'
            }
        ]

        self.download_results = []

    def check_kaggle_api(self):
        """Check if Kaggle API is configured"""
        try:
            result = subprocess.run(['kaggle', 'datasets', 'list'],
                                  capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                print("✅ Kaggle API is properly configured")
                return True
            else:
                print("❌ Kaggle API not configured. Please run:")
                print("   1. Go to https://www.kaggle.com/settings")
                print("   2. Click 'Create New API Token'")
                print("   3. Place kaggle.json in ~/.kaggle/")
                return False

        except FileNotFoundError:
            print("❌ Kaggle CLI not found. Installing...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'kaggle'], check=True)
            print("✅ Kaggle CLI installed")
            return True

    def download_dataset(self, dataset_info):
        """Download a single dataset with validation"""
        name = dataset_info['name']
        path = dataset_info['path']
        target_size = dataset_info['target_size']

        print(f"\n📥 Downloading {name}...")
        print(f"   Path: {path}")
        print(f"   Target: {target_size:,} samples")

        try:
            # Create dataset directory
            dataset_dir = self.download_dir / name
            dataset_dir.mkdir(exist_ok=True)

            # Download dataset
            cmd = ['kaggle', 'datasets', 'download', '-d', path, '-p', str(dataset_dir), '--unzip']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                print(f"❌ Failed to download {name}")
                print(f"   Error: {result.stderr}")
                return False

            # Find and validate CSV files
            csv_files = list(dataset_dir.glob('*.csv'))

            if not csv_files:
                print(f"❌ No CSV files found in {name}")
                return False

            # Analyze downloaded files
            total_samples = 0
            file_info = []

            for csv_file in csv_files:
                try:
                    df = pd.read_csv(csv_file)
                    sample_count = len(df)
                    total_samples += sample_count

                    file_info.append({
                        'file': csv_file.name,
                        'samples': sample_count,
                        'columns': list(df.columns),
                        'size_mb': csv_file.stat().st_size / (1024 * 1024)
                    })

                except Exception as e:
                    print(f"⚠️  Could not read {csv_file.name}: {e}")

            # Success validation
            success_rate = (total_samples / target_size) * 100 if target_size > 0 else 0

            print(f"✅ Successfully downloaded {name}")
            print(f"   Files: {len(csv_files)}")
            print(f"   Samples: {total_samples:,}")
            print(f"   Target achievement: {success_rate:.1f}%")

            result_record = {
                'name': name,
                'success': True,
                'samples': total_samples,
                'target': target_size,
                'achievement_rate': success_rate,
                'files': file_info,
                'download_time': datetime.now().isoformat()
            }

            self.download_results.append(result_record)
            return True

        except subprocess.TimeoutExpired:
            print(f"❌ Timeout downloading {name}")
            return False
        except Exception as e:
            print(f"❌ Error downloading {name}: {e}")
            return False

    def download_all_datasets(self):
        """Download all priority datasets"""
        print("🚀 AUTOMATED KAGGLE DATASET ACQUISITION")
        print("=" * 50)
        print(f"Target Directory: {self.download_dir}")
        print(f"Datasets to Download: {len(self.datasets)}")
        print(f"Total Target Samples: {sum(d['target_size'] for d in self.datasets):,}")

        # Check Kaggle API
        if not self.check_kaggle_api():
            return False

        # Download each dataset
        success_count = 0
        total_samples = 0

        for dataset in self.datasets:
            if self.download_dataset(dataset):
                success_count += 1
                total_samples += self.download_results[-1]['samples']

        # Summary
        self.print_download_summary(success_count, total_samples)
        self.save_download_report()

        return success_count > 0

    def print_download_summary(self, success_count, total_samples):
        """Print download summary"""
        print("\n" + "=" * 50)
        print("📊 DOWNLOAD SUMMARY")
        print("=" * 50)

        print(f"✅ Successfully Downloaded: {success_count}/{len(self.datasets)} datasets")
        print(f"📈 Total Samples Acquired: {total_samples:,}")
        print(f"📁 Download Directory: {self.download_dir}")

        if self.download_results:
            print("\n📋 Dataset Details:")
            for result in self.download_results:
                if result['success']:
                    print(f"  • {result['name']}: {result['samples']:,} samples ({result['achievement_rate']:.1f}% of target)")

    def save_download_report(self):
        """Save download report to JSON"""
        report_path = self.download_dir / 'download_report.json'

        report = {
            'download_time': datetime.now().isoformat(),
            'total_datasets': len(self.datasets),
            'successful_downloads': len([r for r in self.download_results if r['success']]),
            'total_samples': sum(r['samples'] for r in self.download_results if r['success']),
            'download_directory': str(self.download_dir),
            'datasets': self.download_results
        }

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Download report saved: {report_path}")

def main():
    """Main execution function"""
    print("🎯 BIOSEMIOTIC LAUGHTER DETECTION - KAGGLE DATASET ACQUISITION")
    print("=" * 60)

    downloader = KaggleDatasetDownloader()
    success = downloader.download_all_datasets()

    if success:
        print("\n🎉 DATASET ACQUISITION COMPLETE!")
        print("📈 Ready for enhanced model training")
        print("🚀 Next step: Transformer fine-tuning phase")
        return 0
    else:
        print("\n❌ DATASET ACQUISITION FAILED")
        print("Please check Kaggle API configuration and internet connection")
        return 1

if __name__ == "__main__":
    sys.exit(main())