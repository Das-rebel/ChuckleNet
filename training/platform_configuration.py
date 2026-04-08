#!/usr/bin/env python3
"""
Platform Configuration Management
=================================

Comprehensive configuration system for the GCACU Unified Platform.
Provides presets, templates, and validation for different deployment scenarios.

Author: GCACU Development Team
Date: 2026-04-03
Version: 1.0.0
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum


class DeploymentPreset(Enum):
    """Pre-configured deployment presets"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
    HIGH_PERFORMANCE = "high_performance"
    MEMORY_CONSTRAINED = "memory_constrained"
    CULTURAL_FOCUSED = "cultural_focused"
    MULTILINGUAL = "multilingual"
    REALTIME = "realtime"
    BATCH = "batch"


@dataclass
class PlatformPresetConfig:
    """Pre-configured platform settings for specific use cases"""
    name: str
    description: str
    config_overrides: Dict[str, Any]
    recommended_use_cases: List[str]
    hardware_requirements: Dict[str, Any]
    expected_performance: Dict[str, Any]


class ConfigurationManager:
    """
    Manages platform configuration with presets and validation.

    Provides:
    - Pre-configured presets for common scenarios
    - Configuration validation and optimization
    - Hardware-specific optimization
    - Use case recommendations
    """

    def __init__(self):
        """Initialize configuration manager"""
        self.presets = self._initialize_presets()
        self.config_templates = self._initialize_templates()

    def _initialize_presets(self) -> Dict[DeploymentPreset, PlatformPresetConfig]:
        """Initialize pre-configured deployment presets"""
        return {
            DeploymentPreset.DEVELOPMENT: PlatformPresetConfig(
                name="Development",
                description="Fast iteration for development and testing",
                config_overrides={
                    'default_mode': 'auto',
                    'enable_cultural_intelligence': True,
                    'enable_multilingual_support': True,
                    'enable_mlx_optimization': False,  # Faster startup
                    'enable_parallel_processing': True,
                    'max_memory_gb': 16.0,
                    'target_batch_size': 8,
                    'max_workers': 2,
                    'enable_performance_monitoring': True,
                    'log_prediction_details': True,
                    'enable_result_caching': True,
                    'cache_ttl_seconds': 300  # 5 minutes for dev
                },
                recommended_use_cases=[
                    "Model development",
                    "Feature testing",
                    "Debugging",
                    "Rapid prototyping"
                ],
                hardware_requirements={
                    'min_memory_gb': 8,
                    'recommended_memory_gb': 16,
                    'cpu_cores': 4,
                    'gpu': 'optional'
                },
                expected_performance={
                    'latency_ms': '200-500',
                    'throughput_per_sec': '10-20',
                    'accuracy': 'high'
                }
            ),

            DeploymentPreset.TESTING: PlatformPresetConfig(
                name="Testing",
                description="Optimized for automated testing and validation",
                config_overrides={
                    'default_mode': 'high_accuracy',
                    'enable_cultural_intelligence': True,
                    'enable_multilingual_support': True,
                    'enable_mlx_optimization': False,
                    'enable_parallel_processing': False,  # Deterministic execution
                    'max_memory_gb': 8.0,
                    'target_batch_size': 4,
                    'max_workers': 1,
                    'enable_performance_monitoring': True,
                    'log_prediction_details': True,
                    'save_intermediate_results': True,  # For debugging
                    'enable_result_caching': False  # Fresh predictions
                },
                recommended_use_cases=[
                    "Unit testing",
                    "Integration testing",
                    "Model validation",
                    "Regression testing"
                ],
                hardware_requirements={
                    'min_memory_gb': 4,
                    'recommended_memory_gb': 8,
                    'cpu_cores': 2,
                    'gpu': 'not_required'
                },
                expected_performance={
                    'latency_ms': '500-1000',
                    'throughput_per_sec': '1-5',
                    'accuracy': 'maximum'
                }
            ),

            DeploymentPreset.PRODUCTION: PlatformPresetConfig(
                name="Production",
                description="Balanced configuration for production deployment",
                config_overrides={
                    'default_mode': 'production',
                    'enable_cultural_intelligence': True,
                    'enable_multilingual_support': True,
                    'enable_mlx_optimization': True,
                    'enable_parallel_processing': True,
                    'max_memory_gb': 8.0,
                    'target_batch_size': 16,
                    'max_workers': 4,
                    'confidence_threshold': 0.7,
                    'enable_uncertainty_estimation': True,
                    'enable_ensemble_voting': True,
                    'enable_performance_monitoring': True,
                    'log_prediction_details': False,  # Reduce logging overhead
                    'enable_result_caching': True,
                    'cache_ttl_seconds': 3600,  # 1 hour
                    'enable_rest_api': True,
                    'enable_batch_processing': True
                },
                recommended_use_cases=[
                    "Web services",
                    "API endpoints",
                    "Real-time applications",
                    "Production workloads"
                ],
                hardware_requirements={
                    'min_memory_gb': 8,
                    'recommended_memory_gb': 16,
                    'cpu_cores': 4,
                    'gpu': 'optional'
                },
                expected_performance={
                    'latency_ms': '100-300',
                    'throughput_per_sec': '20-50',
                    'accuracy': 'high'
                }
            ),

            DeploymentPreset.HIGH_PERFORMANCE: PlatformPresetConfig(
                name="High Performance",
                description="Maximum performance with resource optimization",
                config_overrides={
                    'default_mode': 'high_accuracy',
                    'enable_cultural_intelligence': True,
                    'enable_multilingual_support': True,
                    'enable_mlx_optimization': True,
                    'enable_parallel_processing': True,
                    'max_memory_gb': 16.0,
                    'target_batch_size': 32,
                    'max_workers': 8,
                    'enable_ensemble_voting': True,
                    'enable_performance_monitoring': True,
                    'log_prediction_details': False,
                    'enable_result_caching': True,
                    'cache_ttl_seconds': 7200,  # 2 hours
                    'enable_model_caching': True
                },
                recommended_use_cases=[
                    "High-volume processing",
                    "Batch analytics",
                    "Research workloads",
                    "Enterprise deployments"
                ],
                hardware_requirements={
                    'min_memory_gb': 16,
                    'recommended_memory_gb': 32,
                    'cpu_cores': 8,
                    'gpu': 'recommended'
                },
                expected_performance={
                    'latency_ms': '50-150',
                    'throughput_per_sec': '50-100',
                    'accuracy': 'maximum'
                }
            ),

            DeploymentPreset.MEMORY_CONSTRAINED: PlatformPresetConfig(
                name="Memory Constrained",
                description="Optimized for limited memory environments",
                config_overrides={
                    'default_mode': 'memory_optimized',
                    'enable_cultural_intelligence': False,  # Reduce memory
                    'enable_multilingual_support': False,  # Reduce memory
                    'enable_mlx_optimization': True,  # Memory efficiency
                    'enable_parallel_processing': False,
                    'max_memory_gb': 4.0,
                    'target_batch_size': 2,
                    'max_workers': 1,
                    'enable_ensemble_voting': False,
                    'enable_performance_monitoring': False,
                    'log_prediction_details': False,
                    'enable_result_caching': False,
                    'cache_ttl_seconds': 60,  # Small cache
                    'primary_architecture': 'baseline_xlmr'  # Lighter model
                },
                recommended_use_cases=[
                    "Edge deployment",
                    "IoT devices",
                    "Resource-constrained environments",
                    "Mobile applications"
                ],
                hardware_requirements={
                    'min_memory_gb': 2,
                    'recommended_memory_gb': 4,
                    'cpu_cores': 1,
                    'gpu': 'not_available'
                },
                expected_performance={
                    'latency_ms': '300-800',
                    'throughput_per_sec': '1-3',
                    'accuracy': 'moderate'
                }
            ),

            DeploymentPreset.CULTURAL_FOCUSED: PlatformPresetConfig(
                name="Cultural Focused",
                description="Enhanced cultural intelligence capabilities",
                config_overrides={
                    'default_mode': 'cultural_aware',
                    'enable_cultural_intelligence': True,
                    'enable_multilingual_support': True,
                    'enable_mlx_optimization': True,
                    'enable_parallel_processing': True,
                    'max_memory_gb': 12.0,
                    'target_batch_size': 12,
                    'max_workers': 4,
                    'enable_performance_monitoring': True,
                    'log_prediction_details': True,
                    'enable_result_caching': True,
                    'cache_ttl_seconds': 1800,  # 30 minutes
                    'primary_architecture': 'gcacu_cultural'
                },
                recommended_use_cases=[
                    "Cross-cultural content analysis",
                    "International comedy research",
                    "Cultural adaptation studies",
                    "Multi-regional applications"
                ],
                hardware_requirements={
                    'min_memory_gb': 8,
                    'recommended_memory_gb': 12,
                    'cpu_cores': 4,
                    'gpu': 'optional'
                },
                expected_performance={
                    'latency_ms': '150-400',
                    'throughput_per_sec': '15-30',
                    'accuracy': 'high'
                }
            ),

            DeploymentPreset.MULTILINGUAL: PlatformPresetConfig(
                name="Multilingual",
                description="Optimized for multilingual content processing",
                config_overrides={
                    'default_mode': 'multilingual',
                    'enable_cultural_intelligence': True,
                    'enable_multilingual_support': True,
                    'enable_mlx_optimization': True,
                    'enable_parallel_processing': True,
                    'max_memory_gb': 12.0,
                    'target_batch_size': 10,
                    'max_workers': 4,
                    'enable_performance_monitoring': True,
                    'log_prediction_details': True,
                    'enable_result_caching': True,
                    'cache_ttl_seconds': 1800,
                    'primary_architecture': 'gcacu_multilingual'
                },
                recommended_use_cases=[
                    "Multilingual comedy analysis",
                    "Cross-language studies",
                    "International content processing",
                    "Language adaptation research"
                ],
                hardware_requirements={
                    'min_memory_gb': 8,
                    'recommended_memory_gb': 12,
                    'cpu_cores': 4,
                    'gpu': 'optional'
                },
                expected_performance={
                    'latency_ms': '200-500',
                    'throughput_per_sec': '12-25',
                    'accuracy': 'high'
                }
            ),

            DeploymentPreset.REALTIME: PlatformPresetConfig(
                name="Real-time",
                description="Low-latency configuration for real-time applications",
                config_overrides={
                    'default_mode': 'high_speed',
                    'enable_cultural_intelligence': False,  # Reduce latency
                    'enable_multilingual_support': False,
                    'enable_mlx_optimization': True,
                    'enable_parallel_processing': True,
                    'max_memory_gb': 8.0,
                    'target_batch_size': 1,  # Single item processing
                    'max_workers': 2,
                    'confidence_threshold': 0.5,  # Lower threshold for speed
                    'enable_uncertainty_estimation': False,
                    'enable_ensemble_voting': False,
                    'enable_performance_monitoring': False,  # Reduce overhead
                    'log_prediction_details': False,
                    'enable_result_caching': True,
                    'cache_ttl_seconds': 60,
                    'primary_architecture': 'baseline_xlmr'  # Faster model
                },
                recommended_use_cases=[
                    "Live streaming analysis",
                    "Interactive applications",
                    "Real-time feedback systems",
                    "Low-latency APIs"
                ],
                hardware_requirements={
                    'min_memory_gb': 4,
                    'recommended_memory_gb': 8,
                    'cpu_cores': 2,
                    'gpu': 'optional'
                },
                expected_performance={
                    'latency_ms': '50-100',
                    'throughput_per_sec': '10-20',
                    'accuracy': 'moderate'
                }
            ),

            DeploymentPreset.BATCH: PlatformPresetConfig(
                name="Batch Processing",
                description="High-throughput batch processing configuration",
                config_overrides={
                    'default_mode': 'production',
                    'enable_cultural_intelligence': True,
                    'enable_multilingual_support': True,
                    'enable_mlx_optimization': True,
                    'enable_parallel_processing': True,
                    'max_memory_gb': 16.0,
                    'target_batch_size': 64,
                    'max_workers': 8,
                    'enable_uncertainty_estimation': True,
                    'enable_ensemble_voting': True,
                    'enable_performance_monitoring': True,
                    'log_prediction_details': False,
                    'enable_result_caching': True,
                    'cache_ttl_seconds': 7200,
                    'enable_batch_processing': True,
                    'max_request_size_mb': 500  # Larger batches
                },
                recommended_use_cases=[
                    "Bulk content processing",
                    "Dataset analysis",
                    "Batch analytics",
                    "Offline processing"
                ],
                hardware_requirements={
                    'min_memory_gb': 8,
                    'recommended_memory_gb': 16,
                    'cpu_cores': 8,
                    'gpu': 'recommended'
                },
                expected_performance={
                    'latency_ms': 'N/A',
                    'throughput_per_sec': '100-200',
                    'accuracy': 'high'
                }
            )
        }

    def _initialize_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize configuration templates for custom scenarios"""
        return {
            'default_production': {
                'description': 'Default production configuration',
                'config': {
                    'default_mode': 'production',
                    'enable_cultural_intelligence': True,
                    'enable_multilingual_support': True,
                    'enable_mlx_optimization': True,
                    'max_memory_gb': 8.0,
                    'target_batch_size': 16
                }
            },
            'research': {
                'description': 'Research and experimentation configuration',
                'config': {
                    'default_mode': 'high_accuracy',
                    'enable_cultural_intelligence': True,
                    'enable_multilingual_support': True,
                    'enable_mlx_optimization': False,
                    'max_memory_gb': 16.0,
                    'target_batch_size': 8,
                    'save_intermediate_results': True,
                    'log_prediction_details': True
                }
            },
            'minimal': {
                'description': 'Minimal configuration for basic functionality',
                'config': {
                    'default_mode': 'auto',
                    'enable_cultural_intelligence': False,
                    'enable_multilingual_support': False,
                    'enable_mlx_optimization': False,
                    'max_memory_gb': 4.0,
                    'target_batch_size': 4,
                    'max_workers': 1
                }
            }
        }

    def get_preset(self, preset: DeploymentPreset) -> PlatformPresetConfig:
        """Get configuration preset"""
        return self.presets.get(preset, self.presets[DeploymentPreset.PRODUCTION])

    def get_preset_config(self, preset: DeploymentPreset) -> Dict[str, Any]:
        """Get configuration overrides for a preset"""
        return self.get_preset(preset).config_overrides

    def list_presets(self) -> List[Dict[str, str]]:
        """List all available presets with descriptions"""
        return [
            {
                'name': preset.value,
                'description': config.description,
                'use_cases': ', '.join(config.recommended_use_cases[:3])
            }
            for preset, config in self.presets.items()
        ]

    def recommend_preset(self, use_case: str, hardware_constraints: Optional[Dict[str, Any]] = None) -> DeploymentPreset:
        """Recommend the best preset based on use case and hardware"""
        use_case_lower = use_case.lower()

        # Check hardware constraints first
        if hardware_constraints:
            memory_gb = hardware_constraints.get('memory_gb', 16)
            if memory_gb <= 4:
                return DeploymentPreset.MEMORY_CONSTRAINED

        # Use case matching
        use_case_keywords = {
            DeploymentPreset.DEVELOPMENT: ['develop', 'test', 'debug', 'prototype'],
            DeploymentPreset.TESTING: ['test', 'validation', 'unit test', 'integration'],
            DeploymentPreset.PRODUCTION: ['production', 'api', 'service', 'web'],
            DeploymentPreset.HIGH_PERFORMANCE: ['performance', 'fast', 'enterprise', 'batch'],
            DeploymentPreset.MEMORY_CONSTRAINED: ['memory', 'edge', 'iot', 'mobile', 'constrained'],
            DeploymentPreset.CULTURAL_FOCUSED: ['cultural', 'cross-cultural', 'international', 'adaptation'],
            DeploymentPreset.MULTILINGUAL: ['multilingual', 'language', 'translation', 'multi-language'],
            DeploymentPreset.REALTIME: ['real-time', 'realtime', 'live', 'streaming', 'interactive'],
            DeploymentPreset.BATCH: ['batch', 'bulk', 'offline', 'async', 'background']
        }

        for preset, keywords in use_case_keywords.items():
            if any(keyword in use_case_lower for keyword in keywords):
                return preset

        # Default recommendation
        return DeploymentPreset.PRODUCTION

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate configuration parameters"""
        errors = []

        # Required parameters
        required_params = ['default_mode', 'max_memory_gb', 'target_batch_size']
        for param in required_params:
            if param not in config:
                errors.append(f"Missing required parameter: {param}")

        # Value validation
        if 'max_memory_gb' in config:
            if config['max_memory_gb'] < 1 or config['max_memory_gb'] > 128:
                errors.append("max_memory_gb must be between 1 and 128")

        if 'target_batch_size' in config:
            if config['target_batch_size'] < 1 or config['target_batch_size'] > 128:
                errors.append("target_batch_size must be between 1 and 128")

        if 'confidence_threshold' in config:
            threshold = config['confidence_threshold']
            if threshold < 0.0 or threshold > 1.0:
                errors.append("confidence_threshold must be between 0.0 and 1.0")

        # Mode validation
        valid_modes = ['auto', 'high_accuracy', 'high_speed', 'memory_optimized',
                      'cultural_aware', 'multilingual', 'production']
        if 'default_mode' in config and config['default_mode'] not in valid_modes:
            errors.append(f"default_mode must be one of {valid_modes}")

        return len(errors) == 0, errors

    def save_config(self, config: Dict[str, Any], filepath: str, format: str = 'yaml'):
        """Save configuration to file"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if format == 'yaml':
            with open(filepath, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        else:  # json
            with open(filepath, 'w') as f:
                json.dump(config, f, indent=2)

    def load_config(self, filepath: str) -> Dict[str, Any]:
        """Load configuration from file"""
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")

        if filepath.suffix in ['.yaml', '.yml']:
            with open(filepath, 'r') as f:
                return yaml.safe_load(f)
        else:  # json
            with open(filepath, 'r') as f:
                return json.load(f)

    def create_custom_config(self, base_preset: DeploymentPreset,
                            custom_overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Create custom configuration based on preset"""
        base_config = self.get_preset_config(base_preset)
        custom_config = base_config.copy()
        custom_config.update(custom_overrides)

        # Validate the custom configuration
        is_valid, errors = self.validate_config(custom_config)
        if not is_valid:
            raise ValueError(f"Invalid configuration: {errors}")

        return custom_config


def create_deployment_config(deployment_scenario: str,
                            memory_gb: float = 8.0,
                            custom_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create deployment configuration for specific scenarios.

    Args:
        deployment_scenario: Description of deployment scenario
        memory_gb: Available memory in GB
        custom_settings: Optional custom configuration overrides

    Returns:
        Complete configuration dictionary
    """
    manager = ConfigurationManager()

    # Get recommended preset
    preset = manager.recommend_preset(deployment_scenario, {'memory_gb': memory_gb})
    base_config = manager.get_preset_config(preset)

    # Apply custom settings
    if custom_settings:
        base_config.update(custom_settings)

    # Validate final configuration
    is_valid, errors = manager.validate_config(base_config)
    if not is_valid:
        raise ValueError(f"Invalid configuration: {errors}")

    return base_config


# Example usage and testing
if __name__ == "__main__":
    # Test configuration manager
    manager = ConfigurationManager()

    print("Available Presets:")
    print("=" * 50)
    for preset_info in manager.list_presets():
        print(f"{preset_info['name']}: {preset_info['description']}")
        print(f"  Use cases: {preset_info['use_cases']}")
        print()

    # Test preset recommendation
    print("Preset Recommendations:")
    print("=" * 50)
    test_scenarios = [
        "API deployment for production",
        "Development and testing",
        "Real-time laughter detection in live streaming",
        "Batch processing of comedy datasets",
        "Edge deployment on IoT devices"
    ]

    for scenario in test_scenarios:
        recommended = manager.recommend_preset(scenario)
        print(f"Scenario: {scenario}")
        print(f"Recommended: {recommended.value}")
        print()