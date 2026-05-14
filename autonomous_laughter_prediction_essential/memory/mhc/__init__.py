"""
Manifold-Constrained Hyper-Connections (mHC)
"""

from .mhc import (
    ManifoldConstrainedHyperConnections,
    AdaptiveMHC,
    MHCConfig,
    BirkhoffPolytope,
    MHCStabilizer,
    create_mhc_system
)

__all__ = [
    'ManifoldConstrainedHyperConnections',
    'AdaptiveMHC',
    'MHCConfig',
    'BirkhoffPolytope',
    'MHCStabilizer',
    'create_mhc_system'
]