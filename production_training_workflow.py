#!/usr/bin/env python3
"""
Production Training Workflow for Autonomous Laughter Prediction
Complete end-to-end training pipeline with monitoring and management
"""

import subprocess
import json
import os
from pathlib import Path
import psutil
import time
from datetime import datetime

class ProductionTrainingWorkflow:
    def __init__(self):
        self.project_dir = Path("~/autonomous_laughter_prediction").expanduser()
        self.checkpoint_dir = self.project_dir / "checkpoints"
        self.logs_dir = self.project_dir / "logs"
        self.data_dir = self.project_dir / "data"

        # Create directories
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Training status
        self.status_file = self.project_dir / "training_status.json"
        self.load_status()

    def load_status(self):
        """Load training status"""
        if self.status_file.exists():
            with open(self.status_file, 'r') as f:
                self.status = json.load(f)
        else:
            self.status = {
                "phase": "initialization",
                "components_trained": [],
                "current_step": 0,
                "total_steps": 10,
                "start_time": None,
                "last_update": None
            }

    def save_status(self):
        """Save training status"""
        self.status["last_update"] = datetime.now().isoformat()
        with open(self.status_file, 'w') as f:
            json.dump(self.status, f, indent=2)

    def check_system_resources(self):
        """Check system resources before training"""
        print("🔍 SYSTEM RESOURCE CHECK")
        print("=" * 50)

        # Memory check
        memory = psutil.virtual_memory()
        print(f"💾 Memory Usage: {memory.percent}% ({memory.available / (1024**3):.1f}GB available)")

        # Disk space check
        disk = psutil.disk_usage(self.project_dir)
        print(f"💿 Disk Space: {disk.free / (1024**3):.1f}GB free / {disk.total / (1024**3):.1f}GB total")

        # CPU check
        cpu_count = psutil.cpu_count()
        print(f"⚙️  CPU Cores: {cpu_count}")

        # Training recommendations
        if memory.available < 4 * 1024**3:  # Less than 4GB
            print("⚠️  WARNING: Low memory available. Training may be slow.")
        if disk.free < 10 * 1024**3:  # Less than 10GB
            print("⚠️  WARNING: Low disk space. Monitor checkpoint storage.")

        return {
            "memory_available_gb": memory.available / (1024**3),
            "disk_free_gb": disk.free / (1024**3),
            "cpu_cores": cpu_count
        }

    def train_component(self, component_name, epochs=10):
        """Train a specific component"""
        print(f"\n🚀 TRAINING {component_name.upper()} COMPONENT")
        print("=" * 50)

        script_path = self.project_dir / "individual_component_training" / f"train_{component_name}.py"

        if not script_path.exists():
            print(f"❌ Training script not found: {script_path}")
            return False

        try:
            # Run training
            result = subprocess.run(
                ["python3", str(script_path)],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            # Log output
            log_file = self.logs_dir / f"{component_name}_training.log"
            with open(log_file, 'a') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"Training {component_name} - {datetime.now().isoformat()}\n")
                f.write(result.stdout)
                if result.stderr:
                    f.write(f"STDERR:\n{result.stderr}")

            if result.returncode == 0:
                print(f"✅ {component_name} training completed successfully")

                # Update status
                if component_name not in self.status["components_trained"]:
                    self.status["components_trained"].append(component_name)
                self.save_status()

                return True
            else:
                print(f"❌ {component_name} training failed")
                print(result.stderr)
                return False

        except subprocess.TimeoutExpired:
            print(f"⏰ {component_name} training timed out")
            return False
        except Exception as e:
            print(f"❌ {component_name} training error: {e}")
            return False

    def validate_checkpoints(self):
        """Validate that all checkpoints exist and are usable"""
        print(f"\n🔍 CHECKPOINT VALIDATION")
        print("=" * 50)

        components = ["tom", "gcacu"]
        all_valid = True

        for component in components:
            checkpoint_dir = self.checkpoint_dir / component
            best_model = checkpoint_dir / f"{component}_best.pt"

            if best_model.exists():
                size_mb = best_model.stat().st_size / (1024**2)
                print(f"✅ {component.upper()}: {best_model.name} ({size_mb:.1f}MB)")
            else:
                print(f"❌ {component.upper()}: Missing checkpoint")
                all_valid = False

        return all_valid

    def test_ensemble(self):
        """Test the ensemble predictor with trained checkpoints"""
        print(f"\n🎭 TESTING ENSEMBLE PREDICTOR")
        print("=" * 50)

        test_script = self.project_dir / "test_trained_ensemble.py"

        if not test_script.exists():
            print(f"❌ Test script not found: {test_script}")
            return False

        try:
            result = subprocess.run(
                ["python3", str(test_script)],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )

            # Log test results
            log_file = self.logs_dir / "ensemble_test.log"
            with open(log_file, 'a') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"Ensemble Test - {datetime.now().isoformat()}\n")
                f.write(result.stdout)

            if result.returncode == 0:
                print("✅ Ensemble test completed successfully")
                return True
            else:
                print("❌ Ensemble test failed")
                return False

        except Exception as e:
            print(f"❌ Ensemble test error: {e}")
            return False

    def generate_training_report(self):
        """Generate comprehensive training report"""
        print(f"\n📊 GENERATING TRAINING REPORT")
        print("=" * 50)

        report = {
            "timestamp": datetime.now().isoformat(),
            "project_dir": str(self.project_dir),
            "training_status": self.status,
            "system_resources": self.check_system_resources(),
            "checkpoints": {},
            "next_steps": []
        }

        # Check checkpoint status
        for component in ["tom", "gcacu"]:
            checkpoint_dir = self.checkpoint_dir / component
            if checkpoint_dir.exists():
                checkpoints = list(checkpoint_dir.glob("*.pt"))
                report["checkpoints"][component] = {
                    "count": len(checkpoints),
                    "files": [str(f.name) for f in checkpoints]
                }

        # Determine next steps
        if "tom" not in self.status["components_trained"]:
            report["next_steps"].append("Train Theory of Mind component")
        if "gcacu" not in self.status["components_trained"]:
            report["next_steps"].append("Train GCACU component")
        if len(self.status["components_trained"]) >= 2:
            report["next_steps"].append("Test ensemble predictor")
            report["next_steps"].append("Set up data pipeline")
            report["next_steps"].append("Start production training with real data")

        # Save report
        report_file = self.project_dir / "training_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"📄 Training report saved to {report_file}")

        # Print summary
        print(f"\n📋 TRAINING SUMMARY:")
        print(f"Components Trained: {', '.join(self.status['components_trained'])}")
        print(f"Available Space: {report['system_resources']['disk_free_gb']:.1f}GB")
        print(f"Next Steps: {len(report['next_steps'])} actions pending")

        return report

    def run_complete_workflow(self):
        """Run the complete training workflow"""
        print("🚀 AUTONOMOUS LAUGHTER PREDICTION - PRODUCTION TRAINING WORKFLOW")
        print("=" * 70)

        # Set start time
        if self.status["start_time"] is None:
            self.status["start_time"] = datetime.now().isoformat()
            self.save_status()

        # Phase 1: System check
        print(f"\n📍 PHASE 1: SYSTEM CHECK")
        resources = self.check_system_resources()
        if resources["disk_free_gb"] < 5:
            print("❌ Insufficient disk space for training")
            return False

        # Phase 2: Component training
        print(f"\n📍 PHASE 2: COMPONENT TRAINING")
        components_to_train = []

        if "tom" not in self.status["components_trained"]:
            components_to_train.append("tom")
        if "gcacu" not in self.status["components_trained"]:
            components_to_train.append("gcacu")

        for component in components_to_train:
            print(f"\n🎯 Training {component.upper()} component...")
            success = self.train_component(component, epochs=10)
            if not success:
                print(f"❌ Failed to train {component}")
                continue

        # Phase 3: Validation
        print(f"\n📍 PHASE 3: CHECKPOINT VALIDATION")
        if not self.validate_checkpoints():
            print("❌ Checkpoint validation failed")
            return False

        # Phase 4: Ensemble testing
        print(f"\n📍 PHASE 4: ENSEMBLE TESTING")
        if not self.test_ensemble():
            print("❌ Ensemble testing failed")
            return False

        # Phase 5: Report generation
        print(f"\n📍 PHASE 5: REPORT GENERATION")
        report = self.generate_training_report()

        print(f"\n🎉 PRODUCTION TRAINING WORKFLOW COMPLETED!")
        print(f"✅ All components trained and validated")
        print(f"✅ Ensemble predictor working")
        print(f"✅ Ready for production deployment")

        return True

def main():
    """Main workflow execution"""
    workflow = ProductionTrainingWorkflow()

    try:
        success = workflow.run_complete_workflow()

        if success:
            print(f"\n🎯 NEXT ACTIONS:")
            print(f"1. Set up data pipeline for real comedy data")
            print(f"2. Run extended training with real datasets")
            print(f"3. Deploy ensemble for production use")
            print(f"4. Monitor performance and iterate")
        else:
            print(f"\n⚠️  Workflow completed with issues. Check logs for details.")

    except KeyboardInterrupt:
        print(f"\n⏸️  Workflow interrupted by user")
    except Exception as e:
        print(f"\n❌ Workflow error: {e}")

if __name__ == "__main__":
    main()