"""
Benchmark Datasets Package

Implementation of all 9 academic laughter prediction benchmark datasets:
1. StandUp4AI
2. UR-FUNNY
3. TED Laughter Corpus
4. SCRIPTS
5. MHD (Multimodal Humor Detection)
6. Kuznetsova
7. Bertero & Fung
8. MuSe-Humor
9. FunnyNet-W
"""

from .standup4ai import (
    StandUp4AIDataset,
    StandUp4AIAudioOnlyDataset,
    StandUp4AIVideoOnlyDataset,
    StandUp4AIMultimodalDataset
)
from .ur_funny import URFunnyDataset
from .ted_laughter import TEDLaughterDataset
from .multimodal_humor import (
    SCRIPTSDataset,
    MHDDataset,
    KuznetsovaDataset
)
from .humor_detection import (
    BerteroFungDataset,
    MuSeHumorDataset,
    FunnyNetWDataset
)

# Dataset registry for easy access
DATASET_REGISTRY = {
    # Primary benchmarks
    'standup4ai': StandUp4AIDataset,
    'ur_funny': URFunnyDataset,
    'ted_laughter': TEDLaughterDataset,

    # Multimodal humor datasets
    'scripts': SCRIPTSDataset,
    'mhd': MHDDataset,
    'kuznetsova': KuznetsovaDataset,

    # Additional humor detection datasets
    'bertero_fung': BerteroFungDataset,
    'muse_humor': MuSeHumorDataset,
    'funnynet_w': FunnyNetWDataset,

    # Specialized variants
    'standup4ai_audio': StandUp4AIAudioOnlyDataset,
    'standup4ai_video': StandUp4AIVideoOnlyDataset,
    'standup4ai_multimodal': StandUp4AIMultimodalDataset,
}

def get_dataset(dataset_name: str, **kwargs):
    """
    Get dataset class by name.

    Args:
        dataset_name: Name of the dataset
        **kwargs: Arguments to pass to dataset constructor

    Returns:
        Dataset instance

    Raises:
        ValueError: If dataset name is not recognized
    """
    dataset_name = dataset_name.lower().replace('-', '_')

    if dataset_name not in DATASET_REGISTRY:
        available = ', '.join(DATASET_REGISTRY.keys())
        raise ValueError(f"Unknown dataset: {dataset_name}. Available: {available}")

    dataset_class = DATASET_REGISTRY[dataset_name]
    return dataset_class(**kwargs)


def list_datasets() -> list:
    """List all available datasets"""
    return list(DATASET_REGISTRY.keys())


def get_dataset_info(dataset_name: str) -> dict:
    """
    Get information about a dataset.

    Args:
        dataset_name: Name of the dataset

    Returns:
        Dictionary with dataset information
    """
    dataset_info = {
        'standup4ai': {
            'name': 'StandUp4AI',
            'type': 'Multimodal (Audio, Video, Text)',
            'task': 'Laughter Detection',
            'description': 'Stand-up comedy laughter annotations with multimodal features',
            'modalities': ['audio', 'video', 'text'],
            'size': '~50 hours of comedy performances'
        },
        'ur_funny': {
            'name': 'UR-FUNNY',
            'type': 'Text',
            'task': 'Humor Detection',
            'description': 'Large-scale humor detection from stand-up comedy jokes',
            'modalities': ['text'],
            'size': '~22K jokes'
        },
        'ted_laughter': {
            'name': 'TED Laughter Corpus',
            'type': 'Audio + Text',
            'task': 'Laughter Detection',
            'description': 'Laughter annotations from TED presentations',
            'modalities': ['audio', 'text'],
            'size': 'Multiple TED talks'
        },
        'scripts': {
            'name': 'SCRIPTS',
            'type': 'Text',
            'task': 'Humor Detection',
            'description': 'Humor detection from TV show scripts',
            'modalities': ['text'],
            'size': 'TV show script excerpts'
        },
        'mhd': {
            'name': 'MHD (Multimodal Humor Detection)',
            'type': 'Multimodal (Audio, Video, Text)',
            'task': 'Humor Detection',
            'description': 'Multimodal content for humor detection',
            'modalities': ['audio', 'video', 'text'],
            'size': 'Multimodal humor samples'
        },
        'kuznetsova': {
            'name': 'Kuznetsova',
            'type': 'Text',
            'task': 'Humor Detection',
            'description': 'Humorous texts from various sources',
            'modalities': ['text'],
            'size': 'News, jokes, quotes'
        },
        'bertero_fung': {
            'name': 'Bertero & Fung',
            'type': 'Text',
            'task': 'Humor Detection',
            'description': 'Humor detection in conversational dialogue context',
            'modalities': ['text'],
            'size': 'Conversational dialogues'
        },
        'muse_humor': {
            'name': 'MuSe-Humor',
            'type': 'Multimodal (Audio, Video, Text)',
            'task': 'Humor Recognition',
            'description': 'Multimodal sentiment and humor recognition',
            'modalities': ['audio', 'video', 'text'],
            'size': 'Multimodal humor samples'
        },
        'funnynet_w': {
            'name': 'FunnyNet-W',
            'type': 'Text',
            'task': 'Humor Detection',
            'description': 'Web-based humor detection dataset',
            'modalities': ['text'],
            'size': 'Web content samples'
        }
    }

    dataset_name = dataset_name.lower().replace('-', '_')
    return dataset_info.get(dataset_name, {})


__all__ = [
    # Dataset classes
    'StandUp4AIDataset',
    'URFunnyDataset',
    'TEDLaughterDataset',
    'SCRIPTSDataset',
    'MHDDataset',
    'KuznetsovaDataset',
    'BerteroFungDataset',
    'MuSeHumorDataset',
    'FunnyNetWDataset',

    # Specialized variants
    'StandUp4AIAudioOnlyDataset',
    'StandUp4AIVideoOnlyDataset',
    'StandUp4AIMultimodalDataset',

    # Utility functions
    'get_dataset',
    'list_datasets',
    'get_dataset_info',

    # Registry
    'DATASET_REGISTRY',
]