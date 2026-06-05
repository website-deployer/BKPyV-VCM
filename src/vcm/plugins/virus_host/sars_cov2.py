"""SARS-CoV-2 virus-host interaction plugin."""

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


class SARSCoV2Plugin(BasePlugin):
    """Plugin for SARS-CoV-2 virus-host interaction.

    This represents a simplified model of SARS-CoV-2 infection in a host cell,
    including viral entry, replication, and host response pathways.
    """

    def __init__(self):
        """Initialize the SARS-CoV-2 plugin."""
        super().__init__()
        self.plugin_id = "virus_host.sars_cov2"
        self.plugin_name = "SARS-CoV-2 Virus-Host"
        self.description = "SARS-CoV-2 virus-host interaction model"

    def get_default_config(self) -> ExperimentConfig:
        """Get default experiment configuration.

        Returns:
            Default ExperimentConfig
        """
        return ExperimentConfig(
            experiment_id="sars_cov2_default",
            plugin=self.plugin_id,
            simulator="hybrid",
            simulation_length=100.0,
            timestep=1.0,
            output_path="outputs/sars_cov2/",
        )

    def create_initial_state(self, config: Optional[Dict[str, Any]] = None) -> CellState:
        """Create initial cell state for SARS-CoV-2 infection model.

        Args:
            config: Optional configuration overrides

        Returns:
            Initial CellState
        """
        # Define host cell genes (ACE2 pathway, interferon response, etc.)
        genes = {
            "ACE2": Gene(id="ACE2", name="ACE2 receptor", expression_level=1.0, is_essential=True),
            "TMPRSS2": Gene(id="TMPRSS2", name="TMPRSS2 protease", expression_level=0.8, is_essential=False),
            "IFNB1": Gene(id="IFNB1", name="Interferon beta", expression_level=0.5, is_essential=False),
            "ISG15": Gene(id="ISG15", name="ISG15 antiviral protein", expression_level=0.3, is_essential=False),
            "MX1": Gene(id="MX1", name="MX1 antiviral protein", expression_level=0.3, is_essential=False),
            "IL6": Gene(id="IL6", name="Interleukin-6", expression_level=0.2, is_essential=False),
            "TNF": Gene(id="TNF", name="Tumor necrosis factor", expression_level=0.2, is_essential=False),
        }

        # Define viral genes (simplified representation)
        viral_genes = {
            "viral_spike": Gene(id="viral_spike", name="Spike protein", expression_level=0.0, is_essential=True),
            "viral_rep": Gene(id="viral_rep", name="Replication complex", expression_level=0.0, is_essential=True),
            "viral_nuc": Gene(id="viral_nuc", name="Nucleocapsid", expression_level=0.0, is_essential=True),
        }
        genes.update(viral_genes)

        # Define host proteins
        proteins = {
            "ACE2": Protein(id="ACE2", name="ACE2 receptor", concentration=1.0, gene_id="ACE2"),
            "TMPRSS2": Protein(id="TMPRSS2", name="TMPRSS2 protease", concentration=0.8, gene_id="TMPRSS2"),
            "IFNB1": Protein(id="IFNB1", name="Interferon beta", concentration=0.5, gene_id="IFNB1"),
            "IL6": Protein(id="IL6", name="Interleukin-6", concentration=0.2, gene_id="IL6"),
            "TNF": Protein(id="TNF", name="TNF", concentration=0.2, gene_id="TNF"),
        }

        # Define viral proteins
        viral_proteins = {
            "Spike": Protein(id="Spike", name="Spike protein", concentration=0.0, gene_id="viral_spike"),
            "Rep": Protein(id="Rep", name="Replication complex", concentration=0.0, gene_id="viral_rep"),
            "Nuc": Protein(id="Nuc", name="Nucleocapsid", concentration=0.0, gene_id="viral_nuc"),
        }
        proteins.update(viral_proteins)

        # Define metabolites
        metabolites = {
            "atp": Metabolite(id="atp", name="ATP", concentration=3.0, is_essential=True),
            "nucleotides": Metabolite(id="nucleotides", name="Nucleotides", concentration=2.0, is_essential=True),
            "amino_acids": Metabolite(id="amino_acids", name="Amino acids", concentration=2.0, is_essential=True),
        }

        # Define pathways
        pathways = {
            "viral_entry": Pathway(
                id="viral_entry",
                name="Viral entry",
                proteins=["ACE2", "TMPRSS2", "Spike"],
                metabolites=[],
                flux=0.0,
            ),
            "viral_replication": Pathway(
                id="viral_replication",
                name="Viral replication",
                proteins=["Rep", "Nuc"],
                metabolites=["nucleotides", "atp", "amino_acids"],
                flux=0.0,
            ),
            "interferon_response": Pathway(
                id="interferon_response",
                name="Interferon response",
                proteins=["IFNB1"],
                metabolites=[],
                flux=0.5,
            ),
            "inflammatory_response": Pathway(
                id="inflammatory_response",
                name="Inflammatory response",
                proteins=["IL6", "TNF"],
                metabolites=[],
                flux=0.2,
            ),
        }

        return CellState(
            cell_id="host_cell_001",
            cell_type="sars_cov2_host",
            genes=genes,
            proteins=proteins,
            metabolites=metabolites,
            pathways=pathways,
            metadata={"viral_load": 0.0, "infection_status": "uninfected"},
        )

    def get_supported_perturbations(self) -> List[Perturbation]:
        """Get supported perturbations for SARS-CoV-2 model.

        Returns:
            List of Perturbation objects
        """
        return [
            Perturbation(
                id="viral_infection",
                name="Viral infection",
                perturbation_type=PerturbationType.VIRAL_INFECTION,
                magnitude=1.0,
                timing=10.0,
            ),
            Perturbation(
                id="ace2_inhibition",
                name="ACE2 inhibition",
                perturbation_type=PerturbationType.PROTEIN_INHIBITION,
                target_id="ACE2",
                magnitude=0.9,
            ),
            Perturbation(
                id="interferon_treatment",
                name="Interferon treatment",
                perturbation_type=PerturbationType.GENE_OVEREXPRESSION,
                target_id="IFNB1",
                magnitude=2.0,
            ),
            Perturbation(
                id="antiviral_drug",
                name="Antiviral drug (replication inhibitor)",
                perturbation_type=PerturbationType.PROTEIN_INHIBITION,
                target_id="Rep",
                magnitude=0.95,
            ),
        ]
