#!/usr/bin/env python3
"""
Essential Project Extractor for Autonomous Laughter Prediction
Creates streamlined project structure with only essential files for continued development
"""

import subprocess
import json
import os
from pathlib import Path
import shutil
from datetime import datetime

class EssentialProjectExtractor:
    def __init__(self):
        self.source_dir = Path("~/autonomous_laughter_prediction").expanduser()
        self.essential_dir = Path("~/autonomous_laughter_prediction_essential").expanduser()
        self.backup_dir = Path("~/autonomous_laughter_prediction_backup").expanduser()

        # Essential files based on training plan analysis
        self.essential_files = {
            "core_architecture": [
                "theory_of_mind_layer.py",
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
                "utils.py",
                "data_processor.py",
                "prepare_data.py"
            ],
            "documentation": [
                "FINAL_REPORT.md",
                "NEXT_STEPS.md",
                "README.md",
                "TRAINING_PLAN.md"
            ],
            "testing": [
                "test_individual_components.py"
            ],
            "data": [
                "data/",
            ]
        }

        # Files to exclude from essential project
        self.exclude_patterns = [
            "*.pth", "*.pt", "*.ckpt", "*.safetensors",  # Model checkpoints (can be regenerated)
            "__pycache__", "*.pyc", "*.pyo",              # Python cache
            "*.log", "*.tb", "events.*",                  # TensorBoard logs
            "*.backup", "*.old", "*.bak",                 # Backup files
            "*.tmp", "*.temp",                            # Temp files
            "results/", "outputs/",                       # Output directories (can be regenerated)
            ".git/",                                      # Git history
            "*.h5", "*.hdf5"                              # Additional checkpoint formats
        ]

    def analyze_current_project(self):
        """Analyze current project structure and size"""
        print("📊 ANALYZING CURRENT PROJECT...")

        total_size = 0
        essential_size = 0
        checkpoint_size = 0
        log_size = 0
        other_size = 0

        # Walk through all files
        for file_path in self.source_dir.rglob("*"):
            if file_path.is_file():
                file_size = file_path.stat().st_size
                total_size += file_size

                # Categorize file
                if file_path.suffix in ['.pth', '.pt', '.ckpt', '.safetensors', '.h5', '.hdf5']:
                    checkpoint_size += file_size
                elif file_path.suffix in ['.log', '.tb'] or 'events' in file_path.name:
                    log_size += file_size
                elif any(file_path.name.endswith(essential) for essentials in self.essential_files.values() for essential in essentials):
                    essential_size += file_size
                else:
                    other_size += file_size

        stats = {
            "total_size_gb": total_size / (1024**3),
            "essential_size_gb": essential_size / (1024**3),
            "checkpoint_size_gb": checkpoint_size / (1024**3),
            "log_size_gb": log_size / (1024**3),
            "other_size_gb": other_size / (1024**3),
            "potential_savings_gb": (checkpoint_size + log_size) / (1024**3)
        }

        print(f"📊 PROJECT SIZE ANALYSIS:")
        print(f"Total Size: {stats['total_size_gb']:.2f} GB")
        print(f"Essential Files: {stats['essential_size_gb']:.2f} GB")
        print(f"Model Checkpoints: {stats['checkpoint_size_gb']:.2f} GB")
        print(f"Logs: {stats['log_size_gb']:.2f} GB")
        print(f"Other Files: {stats['other_size_gb']:.2f} GB")
        print(f"💰 Potential Savings: {stats['potential_savings_gb']:.2f} GB")

        return stats

    def create_essential_project(self):
        """Create essential project structure"""
        print(f"\n📁 CREATING ESSENTIAL PROJECT STRUCTURE...")

        if self.essential_dir.exists():
            shutil.rmtree(self.essential_dir)
        self.essential_dir.mkdir()

        copied_files = 0
        for category, file_patterns in self.essential_files.items():
            print(f"  📂 Processing {category}...")

            for pattern in file_patterns:
                # Handle directories vs files
                if pattern.endswith('/'):
                    # Copy directory
                    src_dir = self.source_dir / pattern.rstrip('/')
                    if src_dir.exists() and src_dir.is_dir():
                        dest_dir = self.essential_dir / pattern.rstrip('/')
                        shutil.copytree(src_dir, dest_dir, ignore=shutil.ignore_patterns(
                            '*.pth', '*.pt', '*.ckpt', '*.safetensors', '__pycache__', '*.log'
                        ))
                        print(f"    ✅ Copied directory: {pattern}")
                else:
                    # Copy individual file
                    for file_path in self.source_dir.rglob(pattern):
                        if file_path.is_file():
                            dest_file = self.essential_dir / file_path.name
                            shutil.copy2(file_path, dest_file)
                            copied_files += 1

        print(f"✅ Essential project created with {copied_files} files")
        return self.essential_dir

    def backup_large_files(self):
        """Backup large files to local storage before cloud upload"""
        print(f"\n💾 CREATING LOCAL BACKUP OF LARGE FILES...")

        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        self.backup_dir.mkdir()

        # Backup checkpoints, logs, and other large files
        backed_up_size = 0

        for pattern in ["*.pth", "*.pt", "*.ckpt", "*.safetensors", "*.log", "*.tb"]:
            for file_path in self.source_dir.rglob(pattern):
                if file_path.is_file():
                    # Create relative path structure
                    rel_path = file_path.relative_to(self.source_dir)
                    dest_path = self.backup_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest_path)
                    backed_up_size += file_path.stat().st_size

        print(f"💾 Local backup created: {backed_up_size / (1024**3):.2f} GB")
        return backed_up_size

    def use_treequest_for_analysis(self):
        """Use TreeQuest AI for intelligent file analysis"""
        print(f"\n🤖 USING TREEQUEST AI FOR INTELLIGENT ANALYSIS...")

        try:
            # Use treequest to analyze what files are truly essential
            result = subprocess.run([
                "treequest", "query", "--provider", "anthropic",
                f"Analyze this autonomous laughter prediction project at {self.source_dir} "
                "and identify which files are absolutely essential for continued development. "
                "Focus on working components mentioned in the training plan: Theory of Mind Layer, "
                "GCACU Network, TurboQuant, and Engram Memory."
            ], capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                print("✅ TreeQuest analysis completed")
                return result.stdout
            else:
                print(f"⚠️ TreeQuest analysis failed: {result.stderr}")
                return None

        except Exception as e:
            print(f"⚠️ TreeQuest analysis error: {e}")
            return None

    def generate_project_report(self, stats):
        """Generate comprehensive project report"""
        print(f"\n📄 GENERATING PROJECT REPORT...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "project_analysis": {
                "source_dir": str(self.source_dir),
                "essential_dir": str(self.essential_dir),
                "backup_dir": str(self.backup_dir),
                "stats": stats
            },
            "recommendations": [
                "Keep essential project for active development",
                "Move backup directory to cloud storage",
                "Remove large checkpoints and logs from source project",
                "Focus on individual component development per training plan"
            ],
            "next_steps": [
                f"Use rclone to backup {self.backup_dir} to cloud",
                f"Replace {self.source_dir} with streamlined {self.essential_dir}",
                "Continue development on individual components",
                "Regenerate checkpoints as needed during training"
            ]
        }

        report_file = Path("~/project_extraction_report.json").expanduser()
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📄 Report saved to {report_file}")
        return report

    def execute_extraction_plan(self):
        """Execute the complete extraction plan"""
        print("🚀 AUTONOMOUS LAUGHTER PREDICTION - ESSENTIAL PROJECT EXTRACTOR")
        print("=" * 70)

        # Step 1: Analyze current project
        stats = self.analyze_current_project()

        # Step 2: Use AI for intelligent analysis
        ai_analysis = self.use_treequest_for_analysis()

        # Step 3: Create essential project
        essential_dir = self.create_essential_project()

        # Step 4: Backup large files locally
        backup_size = self.backup_large_files()

        # Step 5: Generate report
        report = self.generate_project_report(stats)

        print(f"\n🎉 EXTRACTION COMPLETED SUCCESSFULLY!")
        print(f"📁 Essential Project: {essential_dir}")
        print(f"💾 Local Backup: {self.backup_dir} ({backup_size / (1024**3):.2f} GB)")
        print(f"💰 Space Savings: ~{stats['potential_savings_gb']:.1f} GB")

        print(f"\n📋 NEXT STEPS:")
        print(f"1. Review essential project: ls -la {essential_dir}")
        print(f"2. Test functionality: cd {essential_dir} && python3 test_individual_components.py")
        print(f"3. Backup to cloud: rclone copy {self.backup_dir} gdrive:/backups/")
        print(f"4. Replace original: mv {self.source_dir} {self.source_dir}_full && mv {essential_dir} {self.source_dir}")

        return {
            "essential_dir": essential_dir,
            "backup_dir": self.backup_dir,
            "stats": stats,
            "report": report
        }

def main():
    extractor = EssentialProjectExtractor()
    results = extractor.execute_extraction_plan()

if __name__ == "__main__":
    main()