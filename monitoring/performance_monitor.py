#!/usr/bin/env python3
"""
Production Performance Monitoring System

Comprehensive monitoring for GCACU laughter prediction system including:
- Real-time performance metrics
- Model accuracy tracking
- System resource monitoring
- TurboQuant compression statistics
- Alert generation for anomalies
"""

import json
import time
import psutil
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import threading

import torch


@dataclass
class PerformanceMetrics:
    """Single performance measurement"""
    timestamp: str
    inference_time_ms: float
    memory_used_mb: float
    cpu_percent: float
    batch_size: int
    sequence_length: int
    turboquant_compression_ratio: float
    prediction_confidence: float
    error_count: int


@dataclass
class SystemHealth:
    """System health snapshot"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    gpu_utilization_percent: float
    gpu_memory_mb: float
    temperature_celsius: float


class PerformanceMonitor:
    """Comprehensive performance monitoring system"""

    def __init__(self, output_dir: str = "monitoring/logs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Metrics storage
        self.metrics_history: List[PerformanceMetrics] = []
        self.health_history: List[SystemHealth] = []
        self.error_counts = defaultdict(int)

        # Configuration
        self.max_history_size = 10000
        self.alert_thresholds = {
            "max_inference_time_ms": 100.0,
            "max_memory_mb": 2000.0,
            "max_cpu_percent": 90.0,
            "min_compression_ratio": 4.0
        }

        # Threading lock for thread safety
        self.lock = threading.Lock()

        # Setup logging
        self._setup_logging()

        logger.info("Performance Monitor initialized")

    def _setup_logging(self):
        """Setup logging system"""

        global logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # File handler
        log_file = self.output_dir / f"performance_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    def record_inference_metrics(
        self,
        inference_time_ms: float,
        batch_size: int,
        sequence_length: int,
        turboquant_compression_ratio: float,
        prediction_confidence: float,
        error_occurred: bool = False
    ):
        """Record metrics from a single inference call"""

        with self.lock:
            # Get system metrics
            memory_info = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Check for CUDA/GPU
            gpu_util = 0.0
            gpu_mem = 0.0
            if torch.cuda.is_available():
                gpu_util = torch.cuda.utilization() / 100.0
                gpu_mem = torch.cuda.memory_allocated() / (1024 ** 2)

            # Create metrics record
            metrics = PerformanceMetrics(
                timestamp=datetime.now().isoformat(),
                inference_time_ms=inference_time_ms,
                memory_used_mb=memory_info.used / (1024 ** 2),
                cpu_percent=cpu_percent,
                batch_size=batch_size,
                sequence_length=sequence_length,
                turboquant_compression_ratio=turboquant_compression_ratio,
                prediction_confidence=prediction_confidence,
                error_count=1 if error_occurred else 0
            )

            # Add to history
            self.metrics_history.append(metrics)

            # Trim history if needed
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history = self.metrics_history[-self.max_history_size:]

            # Track errors
            if error_occurred:
                self.error_counts["inference_errors"] += 1

            # Check for anomalies
            self._check_thresholds(metrics)

            logger.debug(f"Recorded metrics: inference_time={inference_time_ms:.2f}ms, "
                        f"memory={metrics.memory_used_mb:.1f}MB, "
                        f"cpu={cpu_percent:.1f}%")

    def record_system_health(self):
        """Record current system health snapshot"""

        with self.lock:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')

            # GPU metrics
            gpu_util = 0.0
            gpu_mem = 0.0
            temperature = 0.0

            if torch.cuda.is_available():
                gpu_util = torch.cuda.utilization() / 100.0
                gpu_mem = torch.cuda.memory_allocated() / (1024 ** 2)
                # Temperature reading (platform-specific)
                try:
                    temperature = torch.cuda.temperature()
                except:
                    temperature = 0.0

            health = SystemHealth(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_info.percent,
                memory_available_mb=memory_info.available / (1024 ** 2),
                disk_usage_percent=disk_info.percent,
                gpu_utilization_percent=gpu_util * 100,
                gpu_memory_mb=gpu_mem,
                temperature_celsius=temperature
            )

            self.health_history.append(health)

            # Trim history
            if len(self.health_history) > self.max_history_size:
                self.health_history = self.health_history[-self.max_history_size:]

            logger.debug(f"System health: CPU={cpu_percent:.1f}%, "
                        f"Memory={memory_info.percent:.1f}%, "
                        f"GPU={gpu_util*100:.1f}%")

    def _check_thresholds(self, metrics: PerformanceMetrics):
        """Check if metrics exceed thresholds and generate alerts"""

        alerts = []

        if metrics.inference_time_ms > self.alert_thresholds["max_inference_time_ms"]:
            alerts.append(f"High inference time: {metrics.inference_time_ms:.2f}ms")

        if metrics.memory_used_mb > self.alert_thresholds["max_memory_mb"]:
            alerts.append(f"High memory usage: {metrics.memory_used_mb:.1f}MB")

        if metrics.cpu_percent > self.alert_thresholds["max_cpu_percent"]:
            alerts.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")

        if metrics.turboquant_compression_ratio < self.alert_thresholds["min_compression_ratio"]:
            alerts.append(f"Low compression ratio: {metrics.turboquant_compression_ratio:.2f}x")

        if alerts:
            alert_msg = f"Performance alerts: {'; '.join(alerts)}"
            logger.warning(alert_msg)

            # Save alert to file
            alert_file = self.output_dir / "alerts.log"
            with open(alert_file, 'a') as f:
                f.write(f"{datetime.now().isoformat()} - {alert_msg}\n")

    def get_performance_summary(self, minutes: int = 5) -> Dict[str, Any]:
        """Get performance summary for recent time period"""

        with self.lock:
            # Filter recent metrics
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            recent_metrics = [
                m for m in self.metrics_history
                if datetime.fromisoformat(m.timestamp) > cutoff_time
            ]

            if not recent_metrics:
                return {"error": "No metrics available for the specified time period"}

            # Calculate statistics
            inference_times = [m.inference_time_ms for m in recent_metrics]
            memory_usage = [m.memory_used_mb for m in recent_metrics]
            cpu_usage = [m.cpu_percent for m in recent_metrics]
            compression_ratios = [m.turboquant_compression_ratio for m in recent_metrics]

            return {
                "time_period_minutes": minutes,
                "total_inferences": len(recent_metrics),
                "inference_time_ms": {
                    "mean": sum(inference_times) / len(inference_times),
                    "min": min(inference_times),
                    "max": max(inference_times),
                    "median": sorted(inference_times)[len(inference_times) // 2]
                },
                "memory_usage_mb": {
                    "mean": sum(memory_usage) / len(memory_usage),
                    "min": min(memory_usage),
                    "max": max(memory_usage)
                },
                "cpu_usage_percent": {
                    "mean": sum(cpu_usage) / len(cpu_usage),
                    "min": min(cpu_usage),
                    "max": max(cpu_usage)
                },
                "turboquant_compression": {
                    "mean": sum(compression_ratios) / len(compression_ratios),
                    "min": min(compression_ratios),
                    "max": max(compression_ratios)
                },
                "error_count": sum(m.error_count for m in recent_metrics),
                "timestamp": datetime.now().isoformat()
            }

    def save_metrics_to_file(self, filename: Optional[str] = None):
        """Save metrics history to JSON file"""

        with self.lock:
            if filename is None:
                filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            output_path = self.output_dir / filename

            data = {
                "metrics_history": [asdict(m) for m in self.metrics_history],
                "health_history": [asdict(h) for h in self.health_history],
                "error_counts": dict(self.error_counts),
                "generated_at": datetime.now().isoformat()
            }

            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Metrics saved to {output_path}")

    def start_background_monitoring(self, interval_seconds: int = 60):
        """Start background monitoring thread"""

        def monitoring_loop():
            while True:
                try:
                    self.record_system_health()
                    time.sleep(interval_seconds)
                except Exception as e:
                    logger.error(f"Background monitoring error: {e}")
                    time.sleep(interval_seconds)

        thread = threading.Thread(target=monitoring_loop, daemon=True)
        thread.start()
        logger.info(f"Background monitoring started (interval: {interval_seconds}s)")


# Global monitor instance
monitor_instance: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """Get or create global monitor instance"""

    global monitor_instance
    if monitor_instance is None:
        monitor_instance = PerformanceMonitor()
    return monitor_instance


# Convenience function for recording inference
def record_inference(
    inference_time_ms: float,
    batch_size: int = 1,
    sequence_length: int = 128,
    turboquant_compression_ratio: float = 6.0,
    prediction_confidence: float = 0.0,
    error_occurred: bool = False
):
    """Record inference metrics"""

    monitor = get_monitor()
    monitor.record_inference_metrics(
        inference_time_ms=inference_time_ms,
        batch_size=batch_size,
        sequence_length=sequence_length,
        turboquant_compression_ratio=turboquant_compression_ratio,
        prediction_confidence=prediction_confidence,
        error_occurred=error_occurred
    )


if __name__ == "__main__":
    # Test the monitoring system
    monitor = PerformanceMonitor()

    # Start background monitoring
    monitor.start_background_monitoring(interval_seconds=30)

    # Simulate some inference metrics
    for i in range(10):
        record_inference(
            inference_time_ms=15.0 + i * 0.5,
            batch_size=8,
            sequence_length=128,
            turboquant_compression_ratio=6.0,
            prediction_confidence=0.85
        )
        time.sleep(1)

    # Get summary
    summary = monitor.get_performance_summary(minutes=1)
    print(json.dumps(summary, indent=2))

    # Save metrics
    monitor.save_metrics_to_file("test_metrics.json")
    print("Test metrics saved")