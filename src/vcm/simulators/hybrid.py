"""Hybrid simulator combining mechanistic and ML-based approaches."""

import copy
from typing import Any, Dict, Optional

from vcm.core.models import (
    CellState,
    Environment,
    Perturbation,
    SimulationResult,
    SimulationStep,
)
from vcm.simulators.base import BaseSimulator
from vcm.simulators.mechanistic import MechanisticSimulator
from vcm.simulators.ml_based import MLBasedSimulator


class HybridSimulator(BaseSimulator):
    """Hybrid simulator that combines mechanistic and ML-based approaches.

    This simulator uses the mechanistic approach for well-understood processes
    (e.g., basic metabolism) and ML-based approach for complex, less-understood
    processes (e.g., signaling networks, gene regulation).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the hybrid simulator.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.mechanistic_weight = config.get("mechanistic_weight", 0.7) if config else 0.7
        self.ml_weight = config.get("ml_weight", 0.3) if config else 0.3

        # Initialize sub-simulators
        self.mechanistic_sim = MechanisticSimulator(config)
        self.ml_sim = MLBasedSimulator(config)

    def simulate(
        self,
        initial_state: CellState,
        perturbation: Optional[Perturbation] = None,
        environment: Optional[Environment] = None,
        n_steps: int = 100,
        timestep: float = 1.0,
    ) -> SimulationResult:
        """Run a full simulation.

        Args:
            initial_state: Starting cell state
            perturbation: Optional perturbation to apply
            environment: Environmental conditions
            n_steps: Number of simulation steps
            timestep: Time step size

        Returns:
            SimulationResult with full trajectory
        """
        if environment is None:
            environment = Environment()

        result = SimulationResult(
            experiment_id=f"hybrid_{initial_state.cell_id}",
            simulator_type="hybrid",
            plugin=initial_state.cell_type,
            config_id="default",
        )

        current_state = copy.deepcopy(initial_state)
        current_state.timestamp = 0.0

        for step_num in range(n_steps):
            # Apply perturbation at the right time
            active_perturbations = []
            if perturbation and perturbation.timing is not None:
                if (
                    perturbation.timing <= current_state.timestamp
                    and (
                        perturbation.duration is None
                        or current_state.timestamp < perturbation.timing + perturbation.duration
                    )
                ):
                    active_perturbations.append(perturbation)

            # Store current step
            step = SimulationStep(
                step_number=step_num,
                timestamp=current_state.timestamp,
                cell_state=copy.deepcopy(current_state),
                applied_perturbations=active_perturbations,
                environment=environment,
            )
            result.steps.append(step)

            # Update state using hybrid approach
            current_state = self.step(current_state, perturbation, environment, timestep)

        result.final_state = current_state
        return result

    def step(
        self,
        current_state: CellState,
        perturbation: Optional[Perturbation] = None,
        environment: Optional[Environment] = None,
        timestep: float = 1.0,
    ) -> CellState:
        """Perform a single simulation step using hybrid approach.

        Args:
            current_state: Current cell state
            perturbation: Optional perturbation to apply
            environment: Environmental conditions
            timestep: Time step size

        Returns:
            Updated cell state
        """
        if environment is None:
            environment = Environment()

        # Get predictions from both simulators
        mechanistic_state = self.mechanistic_sim.step(current_state, perturbation, environment, timestep)
        ml_state = self.ml_sim.step(current_state, perturbation, environment, timestep)

        # Combine predictions based on weights
        new_state = copy.deepcopy(current_state)
        new_state.timestamp += timestep

        # Combine gene expressions
        for gene_id in new_state.genes:
            mech_expr = mechanistic_state.genes[gene_id].expression_level
            ml_expr = ml_state.genes[gene_id].expression_level
            new_state.genes[gene_id].expression_level = (
                self.mechanistic_weight * mech_expr + self.ml_weight * ml_expr
            )

        # Combine protein concentrations
        for protein_id in new_state.proteins:
            mech_conc = mechanistic_state.proteins[protein_id].concentration
            ml_conc = ml_state.proteins[protein_id].concentration
            new_state.proteins[protein_id].concentration = (
                self.mechanistic_weight * mech_conc + self.ml_weight * ml_conc
            )

        # Combine metabolite concentrations
        for metabolite_id in new_state.metabolites:
            mech_conc = mechanistic_state.metabolites[metabolite_id].concentration
            ml_conc = ml_state.metabolites[metabolite_id].concentration
            new_state.metabolites[metabolite_id].concentration = (
                self.mechanistic_weight * mech_conc + self.ml_weight * ml_conc
            )

        # Combine pathway fluxes
        for pathway_id in new_state.pathways:
            mech_flux = mechanistic_state.pathways[pathway_id].flux
            ml_flux = ml_state.pathways[pathway_id].flux
            new_state.pathways[pathway_id].flux = (
                self.mechanistic_weight * mech_flux + self.ml_weight * ml_flux
            )

        new_state.update_state_vector()
        return new_state
