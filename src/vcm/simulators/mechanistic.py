"""Mechanistic simulator implementation using deterministic update rules."""

import copy
import math
from typing import Any, Dict, Optional

import numpy as np

from vcm.core.models import (
    CellState,
    Environment,
    Gene,
    Metabolite,
    Perturbation,
    Protein,
    SimulationResult,
    SimulationStep,
)
from vcm.simulators.base import BaseSimulator


class MechanisticSimulator(BaseSimulator):
    """Deterministic mechanistic simulator with toy update rules.

    This simulator uses simple mathematical rules to update cellular states.
    In a real implementation, these would be replaced by ODE systems or
    other mechanistic models.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the mechanistic simulator.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.decay_rate = config.get("decay_rate", 0.05) if config else 0.05
        self.growth_rate = config.get("growth_rate", 0.1) if config else 0.1

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
            experiment_id=f"mechanistic_{initial_state.cell_id}",
            simulator_type="mechanistic",
            plugin=initial_state.cell_type,
            config_id="default",
        )

        current_state = copy.deepcopy(initial_state)
        current_state.timestamp = 0.0

        perturbations_applied = [perturbation] if perturbation else []

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
        """Perform a single simulation step.

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

        # Apply perturbation effects
        if perturbation and perturbation.timing is not None:
            if perturbation.timing <= current_state.timestamp:
                self._apply_perturbation(new_state, perturbation)

        # Update genes
        for gene_id, gene in new_state.genes.items():
            # Simple logistic growth with noise
            delta = self.growth_rate * gene.expression_level * (1 - gene.expression_level / 10.0)
            # Add environmental effect
            temp_effect = 1.0 - abs(environment.temperature - 37.0) / 37.0
            delta *= temp_effect
            gene.expression_level = max(0.0, gene.expression_level + delta * timestep)

        # Update proteins (follow genes with delay and decay)
        for protein_id, protein in new_state.proteins.items():
            if protein.gene_id and protein.gene_id in new_state.genes:
                gene_expr = new_state.genes[protein.gene_id].expression_level
                target = gene_expr * 0.5  # Protein level tracks gene expression
                delta = (target - protein.concentration) * 0.1
                protein.concentration = max(0.0, protein.concentration + delta * timestep)

        # Update metabolites
        for metabolite_id, metabolite in new_state.metabolites.items():
            # Simple decay with replenishment based on environment
            decay = self.decay_rate * metabolite.concentration
            replenishment = environment.glucose_concentration * 0.01
            metabolite.concentration = max(0.0, metabolite.concentration + (replenishment - decay) * timestep)

        # Update pathway fluxes based on component levels
        for pathway_id, pathway in new_state.pathways.items():
            # Calculate pathway activity based on components
            activity = 1.0
            if pathway.proteins:
                protein_levels = [
                    new_state.proteins[p].concentration
                    for p in pathway.proteins
                    if p in new_state.proteins
                ]
                if protein_levels:
                    activity *= min(protein_levels) / (sum(protein_levels) / len(protein_levels) + 0.1)
            pathway.flux = max(0.0, activity * 5.0)

        new_state.update_state_vector()
        return new_state

    def _apply_perturbation(self, state: CellState, perturbation: Perturbation) -> None:
        """Apply a perturbation to the cell state.

        Args:
            state: Cell state to modify
            perturbation: Perturbation to apply
        """
        magnitude = perturbation.magnitude
        target_id = perturbation.target_id

        if perturbation.perturbation_type.value == "gene_knockout" and target_id:
            if target_id in state.genes:
                state.genes[target_id].expression_level *= (1.0 - magnitude)

        elif perturbation.perturbation_type.value == "gene_overexpression" and target_id:
            if target_id in state.genes:
                state.genes[target_id].expression_level *= (1.0 + magnitude * 5.0)

        elif perturbation.perturbation_type.value == "protein_inhibition" and target_id:
            if target_id in state.proteins:
                state.proteins[target_id].concentration *= (1.0 - magnitude)
                state.proteins[target_id].active = False

        elif perturbation.perturbation_type.value == "metabolite_addition" and target_id:
            if target_id in state.metabolites:
                state.metabolites[target_id].concentration += magnitude

        elif perturbation.perturbation_type.value == "metabolite_depletion" and target_id:
            if target_id in state.metabolites:
                state.metabolites[target_id].concentration *= (1.0 - magnitude)
