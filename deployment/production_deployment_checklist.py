#!/usr/bin/env python3
"""
Production Deployment Readiness Checklist

Validates all system components for commercial production deployment
of the GCACU autonomous laughter prediction system.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
import time

@dataclass
class ComponentStatus:
    component_name: str
    status: str  # 'ready', 'partial', 'missing'
    description: str
    deployment_ready: bool
    notes: str

class ProductionDeploymentChecker:
    """Comprehensive deployment readiness validation"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.components = []
        self.critical_readiness = False

    def check_all_components(self) -> Dict[str, Any]:
        """Run comprehensive deployment readiness check"""

        print("🚀 GCACU Production Deployment Readiness Check")
        print("=" * 70)
        print(f"Project Root: {self.project_root}")
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # Core Architecture Components
        self.check_gcacu_architecture()
        self.check_cognitive_components()
        self.check_dataset_infrastructure()
        self.check_performance_optimization()
        self.check_multilingual_capabilities()
        self.check_deployment_infrastructure()

        # Generate comprehensive report
        return self.generate_deployment_report()

    def check_gcacu_architecture(self):
        """Check GCACU core architecture components"""
        print("\n🎯 Checking GCACU Architecture...")

        components = [
            ("GCACU Language Adapter", "core/gcacu/gcacu.py", "GCACU architecture implementation"),
            ("XLM-RoBERTa Encoder", "training/xlmr_standup_word_level.py", "Base encoder integration"),
            ("Uncertainty-Aware Pseudo-Labeling", "training/upl_module.py", "UPL confidence-based weighting"),
            ("Domain-Specific Processing", "training/domain_adapter.py", "4 language bucket adaptation")
        ]

        for name, path, description in components:
            status = self.check_component_exists(name, path, description)
            self.components.append(status)

    def check_cognitive_components(self):
        """Check cognitive architecture components"""
        print("\n🧠 Checking Cognitive Architecture...")

        components = [
            ("Theory of Mind Layer", "training/theory_ofMind_layer.py", "Mental state modeling"),
            ("CLoST Framework", "training/clost_reasoning.py", "Setup-punchline causal inference"),
            ("Engram Memory System", "memory/engram/engram.py", "O(1) sparse memory lookup"),
            ("WESR Integration", "training/wesr_integrator.py", "Discrete/continuous laughter classification")
        ]

        for name, path, description in components:
            status = self.check_component_exists(name, path, description)
            self.components.append(status)

    def check_dataset_infrastructure(self):
        """Check dataset infrastructure"""
        print("\n📊 Checking Dataset Infrastructure...")

        datasets = [
            ("StandUp4AI", "data/StandUp4AI/", "EMNLP 2025, 3M+ words, 130K+ labels"),
            ("TIC-TALK", "data/TIC-TALK/", "5,400+ segments, kinematic signals"),
            ("UR-FUNNY", "data/UR-FUNNY/", "TED talks, P2FA forced alignment"),
            ("YouTube Comedy", "data/training/youtube_comedy_augmented/", "42K+ examples"),
            ("Indian Comedy", "data/training/hindi_hinglish/", "Hinglish code-mixing")
        ]

        for name, path, description in datasets:
            status = self.check_dataset_exists(name, path, description)
            self.components.append(status)

    def check_performance_optimization(self):
        """Check performance optimization components"""
        print("\n⚡ Checking Performance Optimization...")

        components = [
            ("MLX Integration", "training/mlx_optimized.py", "Apple Silicon optimization"),
            ("TurboQuant", "memory/turboquant.py", "3-bit KV cache compression"),
            ("VDPG Adapter", "training/vdpg_adapter.py", "Few-shot domain adaptation"),
            ("Memory Optimization", "memory/engram/mhc.py", "Manifold-constrained hyper-connections")
        ]

        for name, path, description in components:
            status = self.check_component_exists(name, path, description)
            self.components.append(status)

    def check_multilingual_capabilities(self):
        """Check multilingual processing capabilities"""
        print("\n🌍 Checking Multilingual Capabilities...")

        components = [
            ("English Specialist", "training/language_adapters/english.py", "US/UK English comedy"),
            ("Hinglish Processor", "training/language_adapters/hinglish.py", "Hindi-English code-mixing"),
            ("Indian Comedy Expert", "training/indian_comedy_specialist.py", "Cultural nuance understanding"),
            ("Cross-Cultural Adapter", "training/cross_cultural_adapter.py", "Global comedy intelligence")
        ]

        for name, path, description in components:
            status = self.check_component_exists(name, path, description)
            self.components.append(status)

    def check_deployment_infrastructure(self):
        """Check deployment infrastructure"""
        print("\n🚀 Checking Deployment Infrastructure...")

        components = [
            ("API Interface", "api/laughter_prediction_api.py", "REST API endpoint"),
            ("Docker Configuration", "Dockerfile", "Container deployment"),
            ("Monitoring System", "monitoring/performance_monitor.py", "Production metrics"),
            ("Health Checks", "deployment/health_checks.py", "System validation")
        ]

        for name, path, description in components:
            status = self.check_component_exists(name, path, description)
            self.components.append(status)

    def check_component_exists(self, name: str, path: str, description: str) -> ComponentStatus:
        """Check if component file exists and is valid"""
        full_path = self.project_root / path

        if full_path.exists():
            with open(full_path, 'r') as f:
                content = f.read()
                if len(content) > 100:  # Basic validation
                    print(f"  ✅ {name}: READY")
                    return ComponentStatus(
                        component_name=name,
                        status='ready',
                        description=description,
                        deployment_ready=True,
                        notes=f"Implemented at {path}"
                    )
                else:
                    print(f"  ⚠️  {name}: PARTIAL (incomplete implementation)")
                    return ComponentStatus(
                        component_name=name,
                        status='partial',
                        description=description,
                        deployment_ready=False,
                        notes=f"Incomplete implementation at {path}"
                    )
        else:
            print(f"  ❌ {name}: MISSING")
            return ComponentStatus(
                component_name=name,
                status='missing',
                description=description,
                deployment_ready=False,
                notes=f"File not found: {path}"
            )

    def check_dataset_exists(self, name: str, path: str, description: str) -> ComponentStatus:
        """Check if dataset exists and has content"""
        full_path = self.project_root / path

        if full_path.exists() and full_path.is_dir():
            files = list(full_path.rglob('*'))
            if len(files) > 5:  # Has substantial content
                print(f"  ✅ {name}: READY ({len(files)} files)")
                return ComponentStatus(
                    component_name=name,
                    status='ready',
                    description=description,
                    deployment_ready=True,
                    notes=f"Dataset with {len(files)} files"
                )
            else:
                print(f"  ⚠️  {name}: PARTIAL (limited data)")
                return ComponentStatus(
                    component_name=name,
                    status='partial',
                    description=description,
                    deployment_ready=False,
                    notes=f"Limited dataset: {len(files)} files"
                )
        else:
            print(f"  ❌ {name}: MISSING")
            return ComponentStatus(
                component_name=name,
                status='missing',
                description=description,
                deployment_ready=False,
                notes=f"Dataset not found: {path}"
            )

    def generate_deployment_report(self) -> Dict[str, Any]:
        """Generate comprehensive deployment readiness report"""

        print("\n" + "=" * 70)
        print("📋 DEPLOYMENT READINESS SUMMARY")
        print("=" * 70)

        ready_count = sum(1 for c in self.components if c.deployment_ready)
        partial_count = sum(1 for c in self.components if c.status == 'partial')
        missing_count = sum(1 for c in self.components if c.status == 'missing')
        total_count = len(self.components)

        readiness_percentage = (ready_count / total_count) * 100 if total_count > 0 else 0

        print(f"\n📊 Component Status:")
        print(f"   ✅ Ready: {ready_count}/{total_count} ({readiness_percentage:.1f}%)")
        print(f"   ⚠️  Partial: {partial_count}/{total_count}")
        print(f"   ❌ Missing: {missing_count}/{total_count}")

        self.critical_readiness = readiness_percentage >= 80

        print(f"\n🚀 Deployment Readiness: {'✅ PRODUCTION READY' if self.critical_readiness else '⚠️  NEEDS WORK'}")

        if self.critical_readiness:
            print(f"\n🎉 System meets production deployment criteria!")
            print(f"   Ready for commercial deployment")
        else:
            print(f"\n⚠️  System needs additional work before production deployment")
            missing_components = [c.component_name for c in self.components if not c.deployment_ready]
            print(f"   Missing/Partial: {', '.join(missing_components)}")

        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'readiness_percentage': readiness_percentage,
            'production_ready': self.critical_readiness,
            'components': {
                'ready': ready_count,
                'partial': partial_count,
                'missing': missing_count,
                'total': total_count
            },
            'component_details': [
                {
                    'name': c.component_name,
                    'status': c.status,
                    'description': c.description,
                    'deployment_ready': c.deployment_ready,
                    'notes': c.notes
                }
                for c in self.components
            ]
        }

        return report

def main():
    """Main deployment check entry point"""

    project_root = "/Users/Subho/autonomous_laughter_prediction"

    if len(sys.argv) > 1:
        project_root = sys.argv[1]

    checker = ProductionDeploymentChecker(project_root)
    report = checker.check_all_components()

    # Save report
    report_file = Path(project_root) / "deployment_readiness_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📁 Deployment report saved to: {report_file}")

    # Exit with appropriate code
    sys.exit(0 if report['production_ready'] else 1)

if __name__ == "__main__":
    main()