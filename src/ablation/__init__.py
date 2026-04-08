"""
Ablation Study Package

Tests each biosemiotic component independently to determine
whether the 4% improvement over BERT baseline is due to:
1. General BERT fine-tuning (baseline)
2. Duchenne laughter detection
3. GCACU incongruity detection
4. Theory of Mind modeling
5. Cultural adaptation
6. Full biosemiotic integration

Run with:
    python -m src.ablation.run_ablation
"""

from .baseline_model import BaselineBERT
from .duchenne_only import DuchenneOnly
from .gcacu_only import GCACUOnly
from .tom_only import TOMOnly
from .cultural_only import CulturalOnly
from .full_model import FullBiosemiotic

__all__ = [
    "BaselineBERT",
    "DuchenneOnly",
    "GCACUOnly",
    "TOMOnly",
    "CulturalOnly",
    "FullBiosemiotic",
]