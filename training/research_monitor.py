#!/usr/bin/env python3
"""
Research Monitoring and Reporting System for Codex Autoresearch Loop
Real-time monitoring, visualization, and comprehensive reporting
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

# Setup paths
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('research_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics to monitor"""
    PERFORMANCE = "performance"  # F1, IoU-F1, etc.
    MEMORY = "memory"           # Memory usage, GPU usage
    TIME = "time"               # Training time, cycle time
    RESOURCE = "resource"       # CPU, disk usage
    QUALITY = "quality"         # Model quality metrics


class AlertLevel(Enum):
    """Alert levels for monitoring"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricData:
    """Single metric data point"""
    timestamp: float
    value: float
    metric_type: MetricType
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Monitoring alert"""
    timestamp: float
    level: AlertLevel
    message: str
    metric_type: MetricType
    value: float
    threshold: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CycleReport:
    """Comprehensive report for a research cycle"""
    cycle_number: int
    timestamp: str
    duration_seconds: float
    success: bool

    # Performance metrics
    test_f1: float = 0.0
    test_iou_f1: float = 0.0
    improvement_over_baseline: float = 0.0

    # Resource metrics
    max_memory_gb: float = 0.0
    avg_memory_gb: float = 0.0
    max_cpu_percent: float = 0.0

    # Time breakdown
    hypothesis_time: float = 0.0
    compilation_time: float = 0.0
    training_time: float = 0.0
    evaluation_time: float = 0.0
    git_commit_time: float = 0.0

    # Experiment details
    hypotheses_tested: List[str] = field(default_factory=list)
    successful_experiments: int = 0
    failed_experiments: int = 0

    # Additional metadata
    alerts_triggered: List[Dict[str, Any]] = field(default_factory=list)
    notes: str = ""


class PerformanceTracker:
    """Tracks performance metrics over time"""

    def __init__(self, max_history: int = 1000):
        """
        Initialize performance tracker

        Args:
            max_history: Maximum number of data points to keep
        """
        self.max_history = max_history
        self.metrics: Dict[str, List[MetricData]] = {}
        self.baseline_f1 = 0.7222

    def record_metric(self,
                     name: str,
                     value: float,
                     metric_type: MetricType,
                     metadata: Optional[Dict[str, Any]] = None):
        """
        Record a metric data point

        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            metadata: Additional metadata
        """
        if name not in self.metrics:
            self.metrics[name] = []

        metric_data = MetricData(
            timestamp=time.time(),
            value=value,
            metric_type=metric_type,
            metadata=metadata or {}
        )

        self.metrics[name].append(metric_data)

        # Trim history if needed
        if len(self.metrics[name]) > self.max_history:
            self.metrics[name] = self.metrics[name][-self.max_history:]

    def get_metric_history(self, name: str, limit: Optional[int] = None) -> List[MetricData]:
        """
        Get metric history

        Args:
            name: Metric name
            limit: Optional limit on number of data points

        Returns:
            List of metric data points
        """
        if name not in self.metrics:
            return []

        history = self.metrics[name]
        if limit:
            return history[-limit:]

        return history

    def get_current_value(self, name: str) -> Optional[float]:
        """Get most recent value of a metric"""
        if name not in self.metrics or not self.metrics[name]:
            return None

        return self.metrics[name][-1].value

    def get_statistics(self, name: str) -> Dict[str, float]:
        """
        Get statistical summary of a metric

        Args:
            name: Metric name

        Returns:
            Statistical summary
        """
        if name not in self.metrics or not self.metrics[name]:
            return {}

        values = [m.value for m in self.metrics[name]]

        return {
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'median': np.median(values),
            'latest': values[-1],
            'count': len(values)
        }

    def get_improvement_trend(self, metric_name: str, window: int = 10) -> float:
        """
        Calculate improvement trend over recent window

        Args:
            metric_name: Name of metric
            window: Window size for trend calculation

        Returns:
            Improvement rate (positive = improving)
        """
        history = self.get_metric_history(metric_name, limit=window)
        if len(history) < 2:
            return 0.0

        # Calculate linear trend
        values = [m.value for m in history]
        x = np.arange(len(values))
        coeffs = np.polyfit(x, values, 1)

        return coeffs[0]  # Slope indicates trend


class AlertSystem:
    """Manages monitoring alerts based on thresholds"""

    def __init__(self):
        self.alerts: List[Alert] = []
        self.thresholds = self._initialize_thresholds()

    def _initialize_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Initialize alert thresholds"""
        return {
            'memory_usage': {
                'warning': 6.0,      # GB
                'error': 7.0,        # GB
                'critical': 7.5,     # GB
                'metric_type': MetricType.MEMORY
            },
            'cpu_usage': {
                'warning': 80.0,     # Percent
                'error': 90.0,       # Percent
                'critical': 95.0,    # Percent
                'metric_type': MetricType.RESOURCE
            },
            'cycle_time': {
                'warning': 300.0,    # Seconds (5 minutes)
                'error': 360.0,      # Seconds (6 minutes)
                'critical': 420.0,   # Seconds (7 minutes)
                'metric_type': MetricType.TIME
            },
            'f1_score': {
                'warning': 0.70,     # Below this is concerning
                'error': 0.68,       # Below this is error
                'critical': 0.65,    # Below this is critical
                'metric_type': MetricType.PERFORMANCE,
                'direction': 'low'   # Low values are bad
            },
            'training_time': {
                'warning': 180.0,    # Seconds (3 minutes)
                'error': 240.0,      # Seconds (4 minutes)
                'critical': 300.0,   # Seconds (5 minutes)
                'metric_type': MetricType.TIME
            }
        }

    def check_thresholds(self,
                        metric_name: str,
                        value: float,
                        metadata: Optional[Dict[str, Any]] = None) -> Optional[Alert]:
        """
        Check if metric value triggers any alerts

        Args:
            metric_name: Name of metric
            value: Current value
            metadata: Additional metadata

        Returns:
            Alert if threshold triggered, None otherwise
        """
        if metric_name not in self.thresholds:
            return None

        threshold_config = self.thresholds[metric_name]

        # Determine alert level based on value
        alert_level = None
        triggered_threshold = None

        # Check thresholds (assuming higher is worse unless specified)
        direction = threshold_config.get('direction', 'high')

        if direction == 'high':
            # Higher values are worse
            if value >= threshold_config['critical']:
                alert_level = AlertLevel.CRITICAL
                triggered_threshold = threshold_config['critical']
            elif value >= threshold_config['error']:
                alert_level = AlertLevel.ERROR
                triggered_threshold = threshold_config['error']
            elif value >= threshold_config['warning']:
                alert_level = AlertLevel.WARNING
                triggered_threshold = threshold_config['warning']
        else:  # direction == 'low'
            # Lower values are worse
            if value <= threshold_config['critical']:
                alert_level = AlertLevel.CRITICAL
                triggered_threshold = threshold_config['critical']
            elif value <= threshold_config['error']:
                alert_level = AlertLevel.ERROR
                triggered_threshold = threshold_config['error']
            elif value <= threshold_config['warning']:
                alert_level = AlertLevel.WARNING
                triggered_threshold = threshold_config['warning']

        if alert_level:
            alert = Alert(
                timestamp=time.time(),
                level=alert_level,
                message=f"{metric_name} {alert_level.value}: {value:.2f} (threshold: {triggered_threshold:.2f})",
                metric_type=threshold_config['metric_type'],
                value=value,
                threshold=triggered_threshold,
                metadata=metadata or {}
            )

            self.alerts.append(alert)
            logger.warning(f"ALERT: {alert.message}")

            return alert

        return None

    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """
        Get recent alerts

        Args:
            hours: Number of hours to look back

        Returns:
            List of recent alerts
        """
        cutoff_time = time.time() - (hours * 3600)
        return [alert for alert in self.alerts if alert.timestamp >= cutoff_time]

    def get_alert_summary(self) -> Dict[str, int]:
        """Get summary of alerts by level"""
        summary = {level.value: 0 for level in AlertLevel}

        for alert in self.alerts:
            summary[alert.level.value] += 1

        return summary


class ResourceMonitor:
    """Monitors system resources during research"""

    def __init__(self, sample_interval: float = 5.0):
        """
        Initialize resource monitor

        Args:
            sample_interval: Seconds between samples
        """
        self.sample_interval = sample_interval
        self.monitoring = False
        self.resource_history = []

    def start_monitoring(self):
        """Start resource monitoring"""
        self.monitoring = True
        logger.info("Resource monitoring started")

    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        logger.info("Resource monitoring stopped")

    def sample_resources(self) -> Dict[str, float]:
        """
        Sample current resource usage

        Returns:
            Resource usage data
        """
        try:
            import psutil

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_gb = memory.used / (1024**3)
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent

            # Network (optional)
            try:
                network = psutil.net_io_counters()
                network_sent_mb = network.bytes_sent / (1024**2)
                network_recv_mb = network.bytes_recv / (1024**2)
            except:
                network_sent_mb = 0.0
                network_recv_mb = 0.0

            resources = {
                'timestamp': time.time(),
                'cpu_percent': cpu_percent,
                'memory_gb': memory_gb,
                'memory_percent': memory_percent,
                'disk_usage_percent': disk_usage_percent,
                'network_sent_mb': network_sent_mb,
                'network_recv_mb': network_recv_mb
            }

            if self.monitoring:
                self.resource_history.append(resources)

            return resources

        except ImportError:
            logger.warning("psutil not available, resource monitoring disabled")
            return {}

    def get_resource_summary(self, duration_seconds: Optional[float] = None) -> Dict[str, Any]:
        """
        Get resource usage summary

        Args:
            duration_seconds: Optional duration to summarize

        Returns:
            Resource summary
        """
        if not self.resource_history:
            return {}

        # Filter by duration if specified
        if duration_seconds:
            cutoff_time = time.time() - duration_seconds
            history = [r for r in self.resource_history if r['timestamp'] >= cutoff_time]
        else:
            history = self.resource_history

        if not history:
            return {}

        # Calculate statistics
        cpu_values = [r['cpu_percent'] for r in history]
        memory_values = [r['memory_gb'] for r in history]

        return {
            'duration': time.time() - history[0]['timestamp'],
            'samples': len(history),
            'cpu': {
                'mean': np.mean(cpu_values),
                'max': np.max(cpu_values),
                'min': np.min(cpu_values)
            },
            'memory': {
                'mean_gb': np.mean(memory_values),
                'max_gb': np.max(memory_values),
                'min_gb': np.min(memory_values)
            }
        }


class ResearchReporter:
    """Generates comprehensive research reports"""

    def __init__(self,
                 output_dir: Path,
                 performance_tracker: PerformanceTracker,
                 alert_system: AlertSystem,
                 resource_monitor: ResourceMonitor):
        """
        Initialize research reporter

        Args:
            output_dir: Directory for reports
            performance_tracker: Performance tracking instance
            alert_system: Alert system instance
            resource_monitor: Resource monitor instance
        """
        self.output_dir = output_dir
        self.performance_tracker = performance_tracker
        self.alert_system = alert_system
        self.resource_monitor = resource_monitor
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.cycle_reports: List[CycleReport] = []

    def generate_cycle_report(self,
                             cycle_number: int,
                             cycle_data: Dict[str, Any]) -> CycleReport:
        """
        Generate comprehensive cycle report

        Args:
            cycle_number: Cycle number
            cycle_data: Cycle execution data

        Returns:
            Cycle report
        """
        report = CycleReport(
            cycle_number=cycle_number,
            timestamp=datetime.now().isoformat(),
            duration_seconds=cycle_data.get('duration', 0.0),
            success=cycle_data.get('success', False)
        )

        # Performance metrics
        report.test_f1 = cycle_data.get('test_f1', 0.0)
        report.test_iou_f1 = cycle_data.get('test_iou_f1', 0.0)
        report.improvement_over_baseline = report.test_f1 - 0.7222

        # Resource metrics
        resource_summary = self.resource_monitor.get_resource_summary(
            duration_seconds=cycle_data.get('duration', 300)
        )
        if resource_summary:
            report.max_memory_gb = resource_summary.get('memory', {}).get('max_gb', 0.0)
            report.avg_memory_gb = resource_summary.get('memory', {}).get('mean_gb', 0.0)
            report.max_cpu_percent = resource_summary.get('cpu', {}).get('max', 0.0)

        # Time breakdown
        report.hypothesis_time = cycle_data.get('hypothesis_time', 0.0)
        report.compilation_time = cycle_data.get('compilation_time', 0.0)
        report.training_time = cycle_data.get('training_time', 0.0)
        report.evaluation_time = cycle_data.get('evaluation_time', 0.0)
        report.git_commit_time = cycle_data.get('git_commit_time', 0.0)

        # Experiment details
        report.hypotheses_tested = cycle_data.get('hypotheses_tested', [])
        report.successful_experiments = cycle_data.get('successful_experiments', 0)
        report.failed_experiments = cycle_data.get('failed_experiments', 0)

        # Alerts
        recent_alerts = self.alert_system.get_recent_alerts(hours=1)
        report.alerts_triggered = [
            {
                'level': alert.level.value,
                'message': alert.message,
                'timestamp': alert.timestamp
            }
            for alert in recent_alerts
        ]

        # Notes
        report.notes = cycle_data.get('notes', '')

        self.cycle_reports.append(report)

        return report

    def save_report(self, report: CycleReport, format: str = 'json'):
        """
        Save report to file

        Args:
            report: Report to save
            format: Output format ('json', 'markdown', 'html')
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"cycle_{report.cycle_number:04d}_{timestamp}"

        if format == 'json':
            self._save_json_report(report, filename)
        elif format == 'markdown':
            self._save_markdown_report(report, filename)
        elif format == 'html':
            self._save_html_report(report, filename)
        else:
            logger.warning(f"Unknown format: {format}")

    def _save_json_report(self, report: CycleReport, filename: str):
        """Save report as JSON"""
        filepath = self.output_dir / f"{filename}.json"

        with open(filepath, 'w') as f:
            json.dump(asdict(report), f, indent=2)

        logger.info(f"JSON report saved: {filepath}")

    def _save_markdown_report(self, report: CycleReport, filename: str):
        """Save report as Markdown"""
        filepath = self.output_dir / f"{filename}.md"

        markdown = self._generate_markdown_report(report)

        with open(filepath, 'w') as f:
            f.write(markdown)

        logger.info(f"Markdown report saved: {filepath}")

    def _save_html_report(self, report: CycleReport, filename: str):
        """Save report as HTML"""
        filepath = self.output_dir / f"{filename}.html"

        html = self._generate_html_report(report)

        with open(filepath, 'w') as f:
            f.write(html)

        logger.info(f"HTML report saved: {filepath}")

    def _generate_markdown_report(self, report: CycleReport) -> str:
        """Generate Markdown report"""
        md = f"""# Research Cycle Report - Cycle {report.cycle_number}

## Overview
- **Timestamp**: {report.timestamp}
- **Duration**: {report.duration_seconds:.1f} seconds
- **Status**: {'✅ Success' if report.success else '❌ Failed'}

## Performance Metrics
- **Test F1**: {report.test_f1:.4f}
- **Test IoU-F1**: {report.test_iou_f1:.4f}
- **Improvement over Baseline**: {report.improvement_over_baseline:+.4f}
  - Baseline: 0.7222
  - {'✅ Above baseline' if report.test_f1 > 0.7222 else '❌ Below baseline'}

## Resource Usage
- **Max Memory**: {report.max_memory_gb:.2f} GB
- **Avg Memory**: {report.avg_memory_gb:.2f} GB
- **Max CPU**: {report.max_cpu_percent:.1f}%

## Time Breakdown
- **Hypothesis Generation**: {report.hypothesis_time:.1f}s
- **Compilation**: {report.compilation_time:.1f}s
- **Training**: {report.training_time:.1f}s
- **Evaluation**: {report.evaluation_time:.1f}s
- **Git Commit**: {report.git_commit_time:.1f}s

## Experiments
- **Hypotheses Tested**: {len(report.hypotheses_tested)}
- **Successful**: {report.successful_experiments}
- **Failed**: {report.failed_experiments}

### Tested Hypotheses
"""

        for hypothesis in report.hypotheses_tested:
            md += f"- {hypothesis}\n"

        if report.alerts_triggered:
            md += "\n## Alerts Triggered\n"
            for alert in report.alerts_triggered:
                md += f"- **{alert['level'].upper()}**: {alert['message']}\n"

        if report.notes:
            md += f"\n## Notes\n{report.notes}\n"

        return md

    def _generate_html_report(self, report: CycleReport) -> str:
        """Generate HTML report"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Research Cycle {report.cycle_number}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .success {{ color: green; }}
        .failed {{ color: red; }}
        .metric {{ margin: 10px 0; }}
        .alert {{ padding: 10px; margin: 5px 0; border-radius: 5px; }}
        .warning {{ background-color: #fff3cd; }}
        .error {{ background-color: #f8d7da; }}
        .critical {{ background-color: #f5c6cb; }}
    </style>
</head>
<body>
    <h1>Research Cycle Report - Cycle {report.cycle_number}</h1>

    <h2>Overview</h2>
    <div class="metric">
        <strong>Timestamp:</strong> {report.timestamp}<br>
        <strong>Duration:</strong> {report.duration_seconds:.1f} seconds<br>
        <strong>Status:</strong> <span class="{'success' if report.success else 'failed'}">
            {'✅ Success' if report.success else '❌ Failed'}
        </span>
    </div>

    <h2>Performance Metrics</h2>
    <div class="metric">
        <strong>Test F1:</strong> {report.test_f1:.4f}<br>
        <strong>Test IoU-F1:</strong> {report.test_iou_f1:.4f}<br>
        <strong>Improvement over Baseline:</strong> {report.improvement_over_baseline:+.4f}<br>
        <strong>Baseline:</strong> 0.7222<br>
        <strong>Status:</strong> {'✅ Above baseline' if report.test_f1 > 0.7222 else '❌ Below baseline'}
    </div>

    <h2>Resource Usage</h2>
    <div class="metric">
        <strong>Max Memory:</strong> {report.max_memory_gb:.2f} GB<br>
        <strong>Avg Memory:</strong> {report.avg_memory_gb:.2f} GB<br>
        <strong>Max CPU:</strong> {report.max_cpu_percent:.1f}%
    </div>

    <h2>Experiments</h2>
    <div class="metric">
        <strong>Hypotheses Tested:</strong> {len(report.hypotheses_tested)}<br>
        <strong>Successful:</strong> {report.successful_experiments}<br>
        <strong>Failed:</strong> {report.failed_experiments}
    </div>
"""

        if report.alerts_triggered:
            html += "<h2>Alerts Triggered</h2>\n"
            for alert in report.alerts_triggered:
                html += f'<div class="alert {alert["level"]}">{alert["message"]}</div>\n'

        html += "</body></html>"
        return html

    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate summary of all cycles"""
        if not self.cycle_reports:
            return {"error": "No cycle reports available"}

        successful_cycles = [r for r in self.cycle_reports if r.success]

        return {
            "total_cycles": len(self.cycle_reports),
            "successful_cycles": len(successful_cycles),
            "success_rate": len(successful_cycles) / len(self.cycle_reports) if self.cycle_reports else 0,
            "best_f1": max(r.test_f1 for r in self.cycle_reports) if self.cycle_reports else 0.0,
            "worst_f1": min(r.test_f1 for r in self.cycle_reports) if self.cycle_reports else 0.0,
            "average_f1": np.mean([r.test_f1 for r in self.cycle_reports]) if self.cycle_reports else 0.0,
            "total_research_time": sum(r.duration_seconds for r in self.cycle_reports),
            "average_cycle_time": np.mean([r.duration_seconds for r in self.cycle_reports]) if self.cycle_reports else 0.0,
            "total_experiments": sum(r.successful_experiments + r.failed_experiments for r in self.cycle_reports),
            "total_alerts": sum(len(r.alerts_triggered) for r in self.cycle_reports)
        }


class ResearchDashboard:
    """Real-time research dashboard"""

    def __init__(self,
                 performance_tracker: PerformanceTracker,
                 alert_system: AlertSystem,
                 resource_monitor: ResourceMonitor):
        """
        Initialize research dashboard

        Args:
            performance_tracker: Performance tracking instance
            alert_system: Alert system instance
            resource_monitor: Resource monitor instance
        """
        self.performance_tracker = performance_tracker
        self.alert_system = alert_system
        self.resource_monitor = resource_monitor

    def display_status(self):
        """Display current research status"""
        print("\n" + "=" * 80)
        print("🔬 CODEX AUTONOMOUS RESEARCH DASHBOARD")
        print("=" * 80)

        # Performance metrics
        current_f1 = self.performance_tracker.get_current_value('test_f1')
        if current_f1:
            improvement = current_f1 - 0.7222
            print(f"📊 Current F1: {current_f1:.4f} ({improvement:+.4f})")

        # Resource usage
        resources = self.resource_monitor.sample_resources()
        if resources:
            print(f"💾 Memory: {resources.get('memory_gb', 0):.2f} GB")
            print(f"⚡ CPU: {resources.get('cpu_percent', 0):.1f}%")

        # Recent alerts
        recent_alerts = self.alert_system.get_recent_alerts(hours=1)
        if recent_alerts:
            print(f"⚠️  Recent Alerts: {len(recent_alerts)}")

        print("=" * 80 + "\n")

    def display_progress(self, cycle_number: int, phase: str, progress: float):
        """
        Display progress for current cycle

        Args:
            cycle_number: Current cycle number
            phase: Current phase
            progress: Progress percentage (0-100)
        """
        bar_length = 40
        filled = int(bar_length * progress / 100)
        bar = '█' * filled + '░' * (bar_length - filled)

        print(f"\r🔬 Cycle {cycle_number} | {phase} | [{bar}] {progress:.0f}%", end='', flush=True)

        if progress >= 100:
            print()  # New line when complete


def test_monitoring():
    """Test monitoring system"""
    print("🧪 Testing Research Monitoring System")

    # Initialize components
    performance_tracker = PerformanceTracker()
    alert_system = AlertSystem()
    resource_monitor = ResourceMonitor()
    reporter = ResearchReporter(
        Path("test_reports"),
        performance_tracker,
        alert_system,
        resource_monitor
    )
    dashboard = ResearchDashboard(performance_tracker, alert_system, resource_monitor)

    # Test metric recording
    performance_tracker.record_metric('test_f1', 0.73, MetricType.PERFORMANCE)
    performance_tracker.record_metric('memory_usage', 5.5, MetricType.MEMORY)

    # Test alerts
    alert_system.check_thresholds('memory_usage', 6.5)
    alert_system.check_thresholds('test_f1', 0.65)

    # Test resource monitoring
    resource_monitor.start_monitoring()
    resources = resource_monitor.sample_resources()
    resource_monitor.stop_monitoring()

    # Test dashboard
    dashboard.display_status()

    # Test report generation
    cycle_data = {
        'success': True,
        'duration': 300,
        'test_f1': 0.73,
        'test_iou_f1': 0.68,
        'hypotheses_tested': ['gcacu_optimization', 'clost_enhancement'],
        'successful_experiments': 1,
        'failed_experiments': 1,
        'hypothesis_time': 30,
        'compilation_time': 30,
        'training_time': 180,
        'evaluation_time': 30,
        'git_commit_time': 30
    }

    report = reporter.generate_cycle_report(1, cycle_data)
    print(f"✅ Report generated: {report.cycle_number}")

    print("✅ Monitoring system test passed!")
    return True


if __name__ == "__main__":
    test_monitoring()