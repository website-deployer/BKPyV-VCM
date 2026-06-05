"""Virtual Cell Model (VCM) - A modular platform for cellular simulation.

This package provides a framework for:
- Mechanistic and ML-based cell simulation
- Plugin architecture for different biological systems
- Experiment tracking and comparison
- Visualization of simulation results
"""

__version__ = "0.1.0"

from vcm.core.models import (
    CellState,
    Gene,
    Protein,
    Metabolite,
    Pathway,
    Perturbation,
    Environment,
    SimulationStep,
    SimulationResult,
    ExperimentConfig,
)

__all__ = [
    "__version__",
    "CellState",
    "Gene",
    "Protein",
    "Metabolite",
    "Pathway",
    "Perturbation",
    "Environment",
    "SimulationStep",
    "SimulationResult",
    "ExperimentConfig",
]
