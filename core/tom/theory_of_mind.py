"""
Compatibility wrapper for the canonical Theory of Mind implementation.
"""

from training.theory_ofMind_layer import (
    EMOTION_LABELS,
    HUMOR_MECHANISMS,
    HitEmotionTrajectory,
    TheoryOfMindLayer,
    ToMConfig,
    test_theory_of_mind,
)

__all__ = [
    "EMOTION_LABELS",
    "HUMOR_MECHANISMS",
    "HitEmotionTrajectory",
    "TheoryOfMindLayer",
    "ToMConfig",
    "test_theory_of_mind",
]
