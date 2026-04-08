"""
Biosemioticai: Biosemiotic Framework for Laughter and Humor Recognition

The first biosemiotic approach to computational humor recognition,
integrating evolutionary theories of laughter with transformer-based ML.
"""

__version__ = "0.1.0"

from .models import BiosemioticClassifier
from .data import HumorDataset

__all__ = ["BiosemioticClassifier", "HumorDataset"]
