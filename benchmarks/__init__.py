"""
Benchmark Package for Autonomous Laughter Prediction

Comprehensive framework for loading, preprocessing, and managing
all 9 academic laughter prediction benchmark datasets.

Datasets supported:
1. StandUp4AI - Multimodal stand-up comedy laughter detection
2. UR-FUNNY - Large-scale humor detection from jokes
3. TED Laughter Corpus - Laughter in TED presentations
4. SCRIPTS - TV show script humor detection
5. MHD - Multimodal humor detection
6. Kuznetsova - Cross-domain humor detection
7. Bertero & Fung - Conversational humor detection
8. MuSe-Humor - Multimodal sentiment and humor
9. FunnyNet-W - Web-based humor detection
"""

from .datasets import (
    # Individual dataset classes
    StandUp4AIDataset,
    URFunnyDataset,
    TEDLaughterDataset,
    SCRIPTSDataset,
    MHDDataset,
    KuznetsovaDataset,
    BerteroFungDataset,
    MuSeHumorDataset,
    FunnyNetWDataset,

    # Specialized variants
    StandUp4AIAudioOnlyDataset,
    StandUp4AIVideoOnlyDataset,
    StandUp4AIMultimodalDataset,

    # Utility functions
    get_dataset,
    list_datasets,
    get_dataset_info,
    DATASET_REGISTRY
)

from .utils import (
    # Base classes
    BaseBenchmarkDataset,
    DataSample,
    create_data_loader,

    # Split management
    SplitManager,
    SplitConfig,

    # Preprocessing
    AudioPreprocessor,
    VideoPreprocessor,
    TextPreprocessor,
    MultimodalPreprocessor,
    AudioConfig,
    VideoConfig,
    TextConfig,

    # Validation
    DataValidator,
    DatasetValidationReport,
    ValidationResult,

    # Data management
    DataManager,
    DataLoader,
    CacheConfig
)

__version__ = '1.0.0'
__author__ = 'Agent 1 - Data Infrastructure Specialist'

__all__ = [
    # Version info
    '__version__',
    '__author__',

    # Datasets
    'StandUp4AIDataset',
    'URFunnyDataset',
    'TEDLaughterDataset',
    'SCRIPTSDataset',
    'MHDDataset',
    'KuznetsovaDataset',
    'BerteroFungDataset',
    'MuSeHumorDataset',
    'FunnyNetWDataset',
    'StandUp4AIAudioOnlyDataset',
    'StandUp4AIVideoOnlyDataset',
    'StandUp4AIMultimodalDataset',

    # Dataset utilities
    'get_dataset',
    'list_datasets',
    'get_dataset_info',
    'DATASET_REGISTRY',

    # Base infrastructure
    'BaseBenchmarkDataset',
    'DataSample',
    'create_data_loader',

    # Split management
    'SplitManager',
    'SplitConfig',

    # Preprocessing
    'AudioPreprocessor',
    'VideoPreprocessor',
    'TextPreprocessor',
    'MultimodalPreprocessor',
    'AudioConfig',
    'VideoConfig',
    'TextConfig',

    # Validation
    'DataValidator',
    'DatasetValidationReport',
    'ValidationResult',

    # Data management
    'DataManager',
    'DataLoader',
    'CacheConfig',
]


# Convenience function for quick dataset loading
def quick_load(dataset_name: str,
               data_path: str,
               split: str = 'train',
               **kwargs) -> BaseBenchmarkDataset:
    """
    Quick load a benchmark dataset.

    Args:
        dataset_name: Name of the dataset
        data_path: Path to dataset data
        split: Dataset split to load
        **kwargs: Additional arguments for dataset

    Returns:
        Loaded dataset instance
    """
    return get_dataset(dataset_name,
                      data_path=data_path,
                      split=split,
                      **kwargs)


def get_supported_benchmarks() -> dict:
    """
    Get information about all supported benchmarks.

    Returns:
        Dictionary mapping benchmark names to their information
    """
    benchmark_names = [
        'standup4ai', 'ur_funny', 'ted_laughter', 'scripts', 'mhd',
        'kuznetsova', 'bertero_fung', 'muse_humor', 'funnynet_w'
    ]

    return {name: get_dataset_info(name) for name in benchmark_names}


# Package-level information
PACKAGE_INFO = {
    'name': 'autonomous_laughter_prediction_benchmarks',
    'version': __version__,
    'description': 'Universal framework for laughter prediction academic benchmarks',
    'supported_benchmarks': 9,
    'modalities_supported': ['text', 'audio', 'video', 'multimodal'],
    'features': [
        'Universal data loading for 9 academic benchmarks',
        'Standardized preprocessing pipeline',
        'Proper train/val/test split protocols',
        'Data quality validation and integrity checks',
        'Efficient caching and data management',
        'Speaker/show/comedian-independent splits',
        'Cross-domain evaluation support',
        'Comprehensive data augmentation'
    ],
    'author': __author__,
    'license': 'MIT'
}