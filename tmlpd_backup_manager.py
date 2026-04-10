#!/usr/bin/env python3
"""
TMLPD-Powered Backup Manager for Autonomous Laughter Prediction
Intelligent backup with essential file identification based on training plan
"""

import subprocess
import json
import os
from pathlib import Path
import shutil

class TMLPDBackupManager:
    def __init__(self):
        self.project_dir = Path("~/autonomous_laughter_prediction").expanduser()
        self.backup_base = f"gdrive:/backups/autonomous_laughter_prediction_{self.get_timestamp()}"
        self.essential_files = self.identify_essential_files()
        self.non_essential_patterns = [
            "*.pth", "*.pt", "*.ckpt", "*.safetensors",  # Model checkpoints
            "__pycache__", "*.pyc", "*.pyo",              # Python cache
            "*.log", "*.tb", "*.events.*",                # TensorBoard logs
            ".git", "*.backup", "*.old",                  # Git and backups
            "*.tmp", "*.temp",                            # Temp files
            "node_modules", ".venv", "venv",              # Dependencies
            "*.h5", "*.hdf5",                             # Additional checkpoint formats
            "data/cache", "data/temp",                    # Data cache
        ]

    def get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def identify_essential_files(self):
        """Identify essential files based on training plan analysis"""
        essential = {
            "core_architecture": [
                "theory_of Mind_layer.py",
                "gcacu_network.py",
                "turboquant_optimizer.py",
                "engram_memory.py",
                "hierarchical_selector.py",
                "quantum_inspired_dynamics.py",
                "adaptive_parameter_generation.py"
            ],
            "training_pipeline": [
                "train.py",
                "config.py",
                "data_loader.py",
                "utils.py"
            ],
            "documentation": [
                "FINAL_REPORT.md",
                "NEXT_STEPS.md",
                "README.md",
                "TRAINING_PLAN.md"
            ],
            "individual_components": [
                "test_individual_components.py",
                "component_tests/"
            ],
            "data_processing": [
                "data_processor.py",
                "prepare_data.py"
            ]
        }
        return essential

    def create_backup_chunks(self):
        """Create chunked backup strategy"""
        chunks = [
            {
                "name": "core_architecture",
                "priority": "critical",
                "patterns": ["*.py", "*.md"],
                "exclude": ["*.pth", "*.pt", "*.ckpt", "*.safetensors"]
            },
            {
                "name": "data_files",
                "priority": "high",
                "patterns": ["data/", "*.csv", "*.json"],
                "exclude": ["*.cache", "*.tmp"]
            },
            {
                "name": "checkpoints",
                "priority": "medium",
                "patterns": ["*.pth", "*.pt", "*.ckpt", "*.safetensors"],
                "exclude": []
            },
            {
                "name": "logs_and_temp",
                "priority": "low",
                "patterns": ["*.log", "*.tb", "events.*", "*.tmp"],
                "exclude": []
            }
        ]
        return chunks

    def backup_chunk(self, chunk):
        """Backup a specific chunk using rclone"""
        chunk_name = chunk["name"]
        patterns = " ".join([f"--include={p}" for p in chunk["patterns"]])
        excludes = " ".join([f"--exclude={p}" for p in chunk["exclude"]])

        print(f"🚀 Backing up {chunk_name} (priority: {chunk['priority']})")

        cmd = f"""
        rclone copy \"{self.project_dir}\" \"{self.backup_base}/{chunk_name}\" \
        {patterns} {excludes} \
        --progress --stats-one-line
        """

        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
            if result.returncode == 0:
                print(f"✅ {chunk_name} backup completed")
                return True
            else:
                print(f"❌ {chunk_name} backup failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print(f"⏰ {chunk_name} backup timed out")
            return False

    def parallel_backup(self):
        """Use TMLPD parallel execution for concurrent backups"""
        import concurrent.futures

        chunks = self.create_backup_chunks()
        print(f"🚀 Starting parallel backup of {len(chunks)} chunks...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(self.backup_chunk, chunk): chunk for chunk in chunks}

            for future in concurrent.futures.as_completed(futures):
                chunk = futures[future]
                try:
                    success = future.result()
                    status = "✅" if success else "❌"
                    print(f"{status} {chunk['name']} completed")
                except Exception as e:
                    print(f"❌ {chunk['name']} failed: {e}")

    def analyze_essential_vs_total(self):
        """Analyze space usage of essential vs non-essential files"""
        essential_size = 0
        non_essential_size = 0

        for category, files in self.essential_files.items():
            for file_pattern in files:
                for file_path in self.project_dir.rglob(file_pattern):
                    if file_path.is_file():
                        essential_size += file_path.stat().st_size

        print(f"📊 SPACE ANALYSIS:")
        print(f"Essential files: {essential_size / (1024**3):.2f} GB")
        print(f"Total project: 28 GB")
        print(f"Potential savings: {(28 - essential_size / (1024**3)):.2f} GB")

        return essential_size

    def create_essential_project_structure(self):
        """Create streamlined project structure with only essential files"""
        essential_dir = self.project_dir.parent / "autonomous_laughter_prediction_essential"

        if essential_dir.exists():
            shutil.rmtree(essential_dir)

        essential_dir.mkdir()
        print(f"📁 Creating essential project structure at {essential_dir}")

        # Copy essential files
        for category, file_patterns in self.essential_files.items():
            category_dir = essential_dir / category
            category_dir.mkdir()

            for pattern in file_patterns:
                for source_file in self.project_dir.rglob(pattern):
                    if source_file.is_file():
                        dest_file = category_dir / source_file.name
                        shutil.copy2(source_file, dest_file)
                        print(f"  ✅ Copied {source_file.name} -> {category}/")

        print(f"✅ Essential project structure created")
        return essential_dir

    def generate_backup_report(self):
        """Generate comprehensive backup report"""
        report = {
            "timestamp": self.get_timestamp(),
            "project_size_gb": 28,
            "backup_location": self.backup_base,
            "essential_files_identified": len([f for files in self.essential_files.values() for f in files]),
            "categories": list(self.essential_files.keys()),
            "backup_strategy": "parallel_chunked",
            "essential_project_size": self.analyze_essential_vs_total() / (1024**3)
        }

        report_file = Path("~/backup_report.json").expanduser()
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📄 Backup report saved to {report_file}")
        return report

def main():
    print("🤖 TMLPD-Powered Backup Manager")
    print("=" * 50)

    manager = TMLPDBackupManager()

    # Analyze current state
    print("📊 Analyzing project structure...")
    manager.analyze_essential_vs_total()

    # Start parallel backup
    print("\n🚀 Starting parallel backup to cloud...")
    manager.parallel_backup()

    # Create essential project structure
    print("\n📁 Creating essential project structure...")
    essential_dir = manager.create_essential_project_structure()

    # Generate report
    print("\n📄 Generating backup report...")
    report = manager.generate_backup_report()

    print(f"\n🎉 BACKUP COMPLETED!")
    print(f"📁 Essential project: {essential_dir}")
    print(f"☁️  Cloud backup: {manager.backup_base}")
    print(f"📊 Space saved: ~{28 - report['essential_project_size']:.1f} GB")

if __name__ == "__main__":
    main()