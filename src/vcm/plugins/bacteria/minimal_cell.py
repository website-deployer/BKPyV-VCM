"""Minimal bacterial cell plugin."""

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


class MinimalCellPlugin(BasePlugin):
    """Plugin for a minimal bacterial cell (e.g., Mycoplasma).

    This represents a simplified bacterial cell with essential genes,
    basic metabolism, and minimal pathways.
    """

    def __init__(self):
        """Initialize the minimal cell plugin."""
        super().__init__()
        self.plugin_id = "bacteria.minimal_cell"
        self.plugin_name = "Minimal Bacterial Cell"
        self.description = "A minimal bacterial cell model (e.g., Mycoplasma-like)"

    def get_default_config(self) -> ExperimentConfig:
        """Get default experiment configuration.

        Returns:
            Default ExperimentConfig
        """
        return ExperimentConfig(
            experiment_id="minimal_cell_default",
            plugin=self.plugin_id,
            simulator="mechanistic",
            simulation_length=50.0,
            timestep=0.5,
            output_path="outputs/minimal_cell/",
        )

    def create_initial_state(self, config: Optional[Dict[str, Any]] = None) -> CellState:
        """Create initial cell state for minimal bacterium.

        Args:
            config: Optional configuration overrides

        Returns:
            Initial CellState
        """
        # Define essential genes
        genes = {
            "dnaA": Gene(id="dnaA", name="DNA replication initiator", expression_level=2.0, is_essential=True),
            "rpoB": Gene(id="rpoB", name="RNA polymerase beta", expression_level=1.5, is_essential=True),
            "gyrA": Gene(id="gyrA", name="DNA gyrase", expression_level=1.0, is_essential=True),
            "ftsZ": Gene(id="ftsZ", name="Cell division protein", expression_level=1.0, is_essential=True),
            "groEL": Gene(id="groEL", name="Chaperonin", expression_level=0.8, is_essential=False),
            "atpD": Gene(id="atpD", name="ATP synthase", expression_level=1.2, is_essential=True),
            "tufA": Gene(id="tufA", name="Elongation factor Tu", expression_level=1.5, is_essential=True),
        }

        # Define proteins
        proteins = {
            "DnaA": Protein(id="DnaA", name="DNA replication initiator", concentration=2.0, gene_id="dnaA"),
            "RpoB": Protein(id="RpoB", name="RNA polymerase", concentration=1.5, gene_id="rpoB"),
            "GyrA": Protein(id="GyrA", name="DNA gyrase", concentration=1.0, gene_id="gyrA"),
            "FtsZ": Protein(id="FtsZ", name="Cell division protein", concentration=1.0, gene_id="ftsZ"),
            "GroEL": Protein(id="GroEL", name="Chaperonin", concentration=0.8, gene_id="groEL"),
            "AtpD": Protein(id="AtpD", name="ATP synthase", concentration=1.2, gene_id="atpD"),
            "TufA": Protein(id="TufA", name="Elongation factor", concentration=1.5, gene_id="tufA"),
        }

        # Define metabolites
        metabolites = {
            "glucose": Metabolite(id="glucose", name="Glucose", concentration=5.0, is_essential=True),
            "atp": Metabolite(id="atp", name="ATP", concentration=3.0, is_essential=True),
            "adp": Metabolite(id="adp", name="ADP", concentration=1.0, is_essential=True),
            "nadh": Metabolite(id="nadh", name="NADH", concentration=0.5, is_essential=True),
            "amino_acids": Metabolite(id="amino_acids", name="Amino acids", concentration=2.0, is_essential=True),
        }

        # Define pathways
        pathways = {
            "glycolysis": Pathway(
                id="glycolysis",
                name="Glycolysis",
                proteins=["AtpD"],
                metabolites=["glucose", "atp", "adp", "nadh"],
                flux=2.0,
            ),
            "translation": Pathway(
                id="translation",
                name="Translation",
                proteins=["TufA", "GroEL"],
                metabolites=["atp", "amino_acids"],
                flux=1.5,
            ),
            "replication": Pathway(
                id="replication",
                name="DNA replication",
                proteins=["DnaA", "GyrA"],
                metabolites=["atp"],
                flux=1.0,
            ),
        }

        return CellState(
            cell_id="minimal_cell_001",
            cell_type="minimal_bacterium",
            genes=genes,
            proteins=proteins,
            metabolites=metabolites,
            pathways=pathways,
        )

    def get_supported_perturbations(self) -> List[Perturbation]:
        """Get supported perturbations for minimal cell.

        Returns:
            List of Perturbation objects
        """
        return [
            Perturbation(
                id="knockout_dnaA",
                name="DNAA knockout",
                perturbation_type=PerturbationType.GENE_KNOCKOUT,
                target_id="dnaA",
                magnitude=1.0,
            ),
            Perturbation(
                id="inhibit_translation",
                name="Translation inhibition",
                perturbation_type=PerturbationType.PROTEIN_INHIBITION,
                target_id="TufA",
                magnitude=0.9,
            ),
            Perturbation(
                id="glucose_depletion",
                name="Glucose depletion",
                perturbation_type=PerturbationType.METABOLITE_DEPLETION,
                target_id="glucose",
                magnitude=0.8,
            ),
            Perturbation(
                id="antibiotic_stress",
                name="Antibiotic stress",
                perturbation_type=PerturbationType.ENVIRONMENTAL_CHANGE,
                magnitude=1.0,
            ),
        ]
