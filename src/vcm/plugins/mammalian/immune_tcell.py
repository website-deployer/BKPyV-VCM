"""Immune T-cell plugin."""

from typing import Any, Dict, List, Optional

from vcm.core.models import (
    CellState,
    ExperimentConfig,
    Gene,
    Metabolite,
    Pathway,
    Perturbation,
    PerturbationType,
    Protein,
)
from vcm.plugins.base import BasePlugin


class ImmuneTCellPlugin(BasePlugin):
    """Plugin for immune T-cell model.

    This represents a simplified T-cell model including T-cell receptor signaling,
    activation, and effector functions.
    """

    def __init__(self):
        """Initialize the immune T-cell plugin."""
        super().__init__()
        self.plugin_id = "mammalian.immune_tcell"
        self.plugin_name = "Immune T-Cell"
        self.description = "T-cell activation and response model"

    def get_default_config(self) -> ExperimentConfig:
        """Get default experiment configuration.

        Returns:
            Default ExperimentConfig
        """
        return ExperimentConfig(
            experiment_id="tcell_default",
            plugin=self.plugin_id,
            simulator="mechanistic",
            simulation_length=75.0,
            timestep=0.5,
            output_path="outputs/tcell/",
        )

    def create_initial_state(self, config: Optional[Dict[str, Any]] = None) -> CellState:
        """Create initial cell state for T-cell model.

        Args:
            config: Optional configuration overrides

        Returns:
            Initial CellState
        """
        # Define T-cell signaling genes
        genes = {
            "CD3E": Gene(id="CD3E", name="CD3 epsilon", expression_level=1.5, is_essential=True),
            "CD4": Gene(id="CD4", name="CD4 co-receptor", expression_level=1.0, is_essential=False),
            "CD8A": Gene(id="CD8A", name="CD8 alpha", expression_level=0.5, is_essential=False),
            "ZAP70": Gene(id="ZAP70", name="ZAP70 kinase", expression_level=1.0, is_essential=True),
            "LCK": Gene(id="LCK", name="LCK kinase", expression_level=1.2, is_essential=True),
            "NFATC1": Gene(id="NFATC1", name="NFAT transcription factor", expression_level=0.8, is_essential=False),
            "IL2": Gene(id="IL2", name="Interleukin-2", expression_level=0.3, is_essential=False),
            "IFNG": Gene(id="IFNG", name="Interferon-gamma", expression_level=0.3, is_essential=False),
            "PD1": Gene(id="PD1", name="PD-1 checkpoint", expression_level=0.5, is_essential=False),
            "CTLA4": Gene(id="CTLA4", name="CTLA-4 checkpoint", expression_level=0.3, is_essential=False),
        }

        # Define T-cell proteins
        proteins = {
            "CD3": Protein(id="CD3", name="CD3 complex", concentration=1.5, gene_id="CD3E"),
            "CD4": Protein(id="CD4", name="CD4 receptor", concentration=1.0, gene_id="CD4"),
            "CD8": Protein(id="CD8", name="CD8 receptor", concentration=0.5, gene_id="CD8A"),
            "ZAP70": Protein(id="ZAP70", name="ZAP70 kinase", concentration=1.0, gene_id="ZAP70"),
            "LCK": Protein(id="LCK", name="LCK kinase", concentration=1.2, gene_id="LCK"),
            "NFAT": Protein(id="NFAT", name="NFAT", concentration=0.8, gene_id="NFATC1"),
            "IL2": Protein(id="IL2", name="IL-2 cytokine", concentration=0.3, gene_id="IL2"),
            "IFNG": Protein(id="IFNG", name="IFN-gamma", concentration=0.3, gene_id="IFNG"),
            "PD1": Protein(id="PD1", name="PD-1", concentration=0.5, gene_id="PD1"),
            "CTLA4": Protein(id="CTLA4", name="CTLA-4", concentration=0.3, gene_id="CTLA4"),
        }

        # Define metabolites
        metabolites = {
            "atp": Metabolite(id="atp", name="ATP", concentration=3.0, is_essential=True),
            "calcium": Metabolite(id="calcium", name="Calcium ions", concentration=0.1, is_essential=True),
            "camp": Metabolite(id="camp", name="cAMP", concentration=0.05, is_essential=False),
        }

        # Define pathways
        pathways = {
            "tcr_signaling": Pathway(
                id="tcr_signaling",
                name="TCR signaling",
                proteins=["CD3", "ZAP70", "LCK"],
                metabolites=["calcium"],
                flux=0.5,
            ),
            "activation": Pathway(
                id="activation",
                name="T-cell activation",
                proteins=["NFAT", "LCK"],
                metabolites=["calcium", "atp"],
                flux=0.3,
            ),
            "effector_function": Pathway(
                id="effector_function",
                name="Effector function",
                proteins=["IL2", "IFNG"],
                metabolites=["atp"],
                flux=0.3,
            ),
            "checkpoint_inhibition": Pathway(
                id="checkpoint_inhibition",
                name="Checkpoint inhibition",
                proteins=["PD1", "CTLA4"],
                metabolites=[],
                flux=0.1,
            ),
        }

        return CellState(
            cell_id="tcell_001",
            cell_type="immune_tcell",
            genes=genes,
            proteins=proteins,
            metabolites=metabolites,
            pathways=pathways,
            metadata={"activation_status": "naive", "proliferation_rate": 0.0},
        )

    def get_supported_perturbations(self) -> List[Perturbation]:
        """Get supported perturbations for T-cell model.

        Returns:
            List of Perturbation objects
        """
        return [
            Perturbation(
                id="tcr_stimulation",
                name="TCR stimulation",
                perturbation_type=PerturbationType.GENE_OVEREXPRESSION,
                target_id="CD3E",
                magnitude=2.0,
                timing=5.0,
            ),
            Perturbation(
                id="checkpoint_inhibition",
                name="PD-1 blockade",
                perturbation_type=PerturbationType.PROTEIN_INHIBITION,
                target_id="PD1",
                magnitude=0.95,
            ),
            Perturbation(
                id="il2_treatment",
                name="IL-2 treatment",
                perturbation_type=PerturbationType.GENE_OVEREXPRESSION,
                target_id="IL2",
                magnitude=3.0,
            ),
            Perturbation(
                id="calcium_flux",
                name="Calcium flux increase",
                perturbation_type=PerturbationType.METABOLITE_ADDITION,
                target_id="calcium",
                magnitude=0.5,
            ),
        ]
