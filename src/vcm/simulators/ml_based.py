"""ML-based simulator implementation using neural network-like updates."""

import copy
from typing import Any, Dict, Optional

import numpy as np

from vcm.core.models import (
    CellState,
    Environment,
    Perturbation,
    SimulationResult,
    SimulationStep,
)
from vcm.simulators.base import BaseSimulator


class MLBasedSimulator(BaseSimulator):
    """ML-based simulator using neural network-like state transitions.

    This simulator uses a simple neural network architecture to predict
    state transitions. In a real implementation, this would use trained
    ML models (e.g., neural networks, random forests, etc.).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the ML-based simulator.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.hidden_size = config.get("hidden_size", 64) if config else 64
        self.learning_rate = config.get("learning_rate", 0.01) if config else 0.01
        # Initialize random weights for the "neural network"
        np.random.seed(42 if config is None else config.get("seed", 42))
        self.weights = {
            "W1": np.random.randn(self.hidden_size, 100) * 0.01,
            "W2": np.random.randn(100, self.hidden_size) * 0.01,
        }

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
            experiment_id=f"ml_based_{initial_state.cell_id}",
            simulator_type="ml_based",
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

            # Update state
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
        """Perform a single simulation step using neural network-like update.

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

        new_state = copy.deepcopy(current_state)
        new_state.timestamp += timestep

        # Get state vector
        state_vector = np.array(current_state.get_state_vector())

        # Pad or truncate to fixed size
        if len(state_vector) < 100:
            padded = np.zeros(100)
            padded[: len(state_vector)] = state_vector
            state_vector = padded
        elif len(state_vector) > 100:
            state_vector = state_vector[:100]

        # Apply "neural network" transformation
        hidden = np.tanh(np.dot(self.weights["W1"], state_vector))
        output = np.dot(self.weights["W2"], hidden)

        # Apply perturbation effect
        if perturbation and perturbation.timing is not None:
            if perturbation.timing <= current_state.timestamp:
                perturbation_effect = np.ones_like(output) * perturbation.magnitude
                output += perturbation_effect * 0.1

        # Apply environmental modulation
        env_factor = (environment.temperature - 37.0) / 37.0
        output *= (1.0 + env_factor * 0.1)

        # Update genes
        gene_count = len(new_state.genes)
        if gene_count > 0:
            gene_updates = output[:gene_count]
            for i, (gene_id, gene) in enumerate(new_state.genes.items()):
                if i < len(gene_updates):
                    gene.expression_level = max(0.0, gene.expression_level + gene_updates[i] * timestep * 0.1)

        # Update proteins
        protein_count = len(new_state.proteins)
        if protein_count > 0:
            protein_start = gene_count
            protein_updates = output[protein_start : protein_start + protein_count]
            for i, (protein_id, protein) in enumerate(new_state.proteins.items()):
                if i < len(protein_updates):
                    protein.concentration = max(0.0, protein.concentration + protein_updates[i] * timestep * 0.1)

        # Update metabolites
        metabolite_count = len(new_state.metabolites)
        if metabolite_count > 0:
            metabolite_start = gene_count + protein_count
            metabolite_updates = output[metabolite_start : metabolite_start + metabolite_count]
            for i, (metabolite_id, metabolite) in enumerate(new_state.metabolites.items()):
                if i < len(metabolite_updates):
                    metabolite.concentration = max(
                        0.0, metabolite.concentration + metabolite_updates[i] * timestep * 0.05
                    )

        # Update pathways
        pathway_count = len(new_state.pathways)
        if pathway_count > 0:
            pathway_start = gene_count + protein_count + metabolite_count
            pathway_updates = output[pathway_start : pathway_start + pathway_count]
            for i, (pathway_id, pathway) in enumerate(new_state.pathways.items()):
                if i < len(pathway_updates):
                    pathway.flux = max(0.0, pathway.flux + pathway_updates[i] * timestep * 0.1)

        new_state.update_state_vector()
        return new_state
