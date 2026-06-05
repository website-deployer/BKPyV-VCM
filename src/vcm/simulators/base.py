"""Base simulator interface for the Virtual Cell Model platform."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from vcm.core.models import CellState, Environment, Perturbation, SimulationResult


class BaseSimulator(ABC):
    """Abstract base class for all simulators.

    All simulator implementations must inherit from this class and implement
    the simulate method. This ensures a consistent interface across different
    simulation approaches (mechanistic, ML-based, hybrid, etc.).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the simulator.

        Args:
            config: Configuration dictionary for the simulator
        """
        self.config = config or {}

    @abstractmethod
    def simulate(
        self,
        initial_state: CellState,
        perturbation: Optional[Perturbation] = None,
        environment: Optional[Environment] = None,
        n_steps: int = 100,
        timestep: float = 1.0,
    ) -> SimulationResult:
        """Run a simulation.

        Args:
            initial_state: Starting cell state
            perturbation: Optional perturbation to apply
            environment: Environmental conditions
            n_steps: Number of simulation steps
            timestep: Time step size

        Returns:
            SimulationResult containing the simulation trajectory
        """
        pass

    @abstractmethod
    def step(
        self,
        current_state: CellState,
        perturbation: Optional[Perturbation] = None,
        environment: Optional[Environment] = None,
        timestep: float = 1.0,
    ) -> CellState:
        """Perform a single simulation step.

        Args:
            current_state: Current cell state
            perturbation: Optional perturbation to apply
            environment: Environmental conditions
            timestep: Time step size

        Returns:
            Updated cell state after one step
        """
        pass

    def get_simulator_info(self) -> Dict[str, Any]:
        """Get information about the simulator."""
        return {
            "simulator_type": self.__class__.__name__,
            "config": self.config,
        }
