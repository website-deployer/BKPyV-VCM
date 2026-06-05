"""Cancer cell plugin."""

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


class CancerCellPlugin(BasePlugin):
    """Plugin for cancer cell model.

    This represents a simplified cancer cell model with oncogenes,
    tumor suppressors, and altered metabolism (Warburg effect).
    """

    def __init__(self):
        """Initialize the cancer cell plugin."""
        super().__init__()
        self.plugin_id = "mammalian.cancer_cell"
        self.plugin_name = "Cancer Cell"
        self.description = "Cancer cell model with oncogenes and tumor suppressors"

    def get_default_config(self) -> ExperimentConfig:
        """Get default experiment configuration.

        Returns:
            Default ExperimentConfig
        """
        return ExperimentConfig(
            experiment_id="cancer_cell_default",
            plugin=self.plugin_id,
            simulator="hybrid",
            simulation_length=100.0,
            timestep=1.0,
            output_path="outputs/cancer_cell/",
        )

    def create_initial_state(self, config: Optional[Dict[str, Any]] = None) -> CellState:
        """Create initial cell state for cancer cell model.

        Args:
            config: Optional configuration overrides

        Returns:
            Initial CellState
        """
        # Define cancer-related genes
        genes = {
            "TP53": Gene(id="TP53", name="p53 tumor suppressor", expression_level=0.3, is_essential=False),
            "MYC": Gene(id="MYC", name="MYC oncogene", expression_level=3.0, is_essential=True),
            "KRAS": Gene(id="KRAS", name="KRAS oncogene", expression_level=2.5, is_essential=True),
            "PIK3CA": Gene(id="PIK3CA", name="PI3K catalytic subunit", expression_level=2.0, is_essential=True),
            "PTEN": Gene(id="PTEN", name="PTEN tumor suppressor", expression_level=0.4, is_essential=False),
            "AKT1": Gene(id="AKT1", name="AKT kinase", expression_level=2.0, is_essential=True),
            "mTOR": Gene(id="mTOR", name="mTOR kinase", expression_level=1.8, is_essential=True),
            "EGFR": Gene(id="EGFR", name="EGFR receptor", expression_level=1.5, is_essential=False),
            "VEGF": Gene(id="VEGF", name="VEGF growth factor", expression_level=1.2, is_essential=False),
            "CDKN1A": Gene(id="CDKN1A", name="p21 cell cycle inhibitor", expression_level=0.5, is_essential=False),
        }

        # Define cancer-related proteins
        proteins = {
            "p53": Protein(id="p53", name="p53 protein", concentration=0.3, gene_id="TP53"),
            "MYC": Protein(id="MYC", name="MYC protein", concentration=3.0, gene_id="MYC"),
            "KRAS": Protein(id="KRAS", name="KRAS protein", concentration=2.5, gene_id="KRAS"),
            "PI3K": Protein(id="PI3K", name="PI3K", concentration=2.0, gene_id="PIK3CA"),
            "PTEN": Protein(id="PTEN", name="PTEN", concentration=0.4, gene_id="PTEN"),
            "AKT": Protein(id="AKT", name="AKT", concentration=2.0, gene_id="AKT1"),
            "mTOR": Protein(id="mTOR", name="mTOR", concentration=1.8, gene_id="mTOR"),
            "EGFR": Protein(id="EGFR", name="EGFR", concentration=1.5, gene_id="EGFR"),
            "VEGF": Protein(id="VEGF", name="VEGF", concentration=1.2, gene_id="VEGF"),
        }

        # Define metabolites (Warburg effect - high glycolysis)
        metabolites = {
            "glucose": Metabolite(id="glucose", name="Glucose", concentration=10.0, is_essential=True),
            "atp": Metabolite(id="atp", name="ATP", concentration=2.5, is_essential=True),
            "lactate": Metabolite(id="lactate", name="Lactate", concentration=5.0, is_essential=False),
            "glutamine": Metabolite(id="glutamine", name="Glutamine", concentration=3.0, is_essential=True),
        }

        # Define pathways
        pathways = {
            "glycolysis": Pathway(
                id="glycolysis",
                name="Glycolysis (Warburg)",
                proteins=[],
                metabolites=["glucose", "atp", "lactate"],
                flux=4.0,
            ),
            "pi3k_akting": Pathway(
                id="pi3k_akting",
                name="PI3K/AKT/mTOR signaling",
                proteins=["PI3K", "AKT", "mTOR"],
                metabolites=["glucose", "glutamine"],
                flux=3.0,
            ),
            "cell_growth": Pathway(
                id="cell_growth",
                name="Cell growth and proliferation",
                proteins=["MYC", "mTOR"],
                metabolites=["atp", "glutamine"],
                flux=2.5,
            ),
            "apoptosis": Pathway(
                id="apoptosis",
                name="Apoptosis (suppressed)",
                proteins=["p53"],
                metabolites=[],
                flux=0.2,
            ),
        }

        return CellState(
            cell_id="cancer_cell_001",
            cell_type="cancer_cell",
            genes=genes,
            proteins=proteins,
            metabolites=metabolites,
            pathways=pathways,
            metadata={
                "proliferation_rate": 2.0,
                "mutation_burden": "high",
                "drug_resistance": "none",
            },
        )

    def get_supported_perturbations(self) -> List[Perturbation]:
        """Get supported perturbations for cancer cell model.

        Returns:
            List of Perturbation objects
        """
        return [
            Perturbation(
                id="chemotherapy",
                name="Chemotherapy",
                perturbation_type=PerturbationType.DRUG_TREATMENT,
                magnitude=1.0,
            ),
            Perturbation(
                id="egfr_inhibitor",
                name="EGFR inhibitor",
                perturbation_type=PerturbationType.PROTEIN_INHIBITION,
                target_id="EGFR",
                magnitude=0.9,
            ),
            Perturbation(
                id="pi3k_inhibitor",
                name="PI3K inhibitor",
                perturbation_type=PerturbationType.PROTEIN_INHIBITION,
                target_id="PI3K",
                magnitude=0.85,
            ),
            Perturbation(
                id="p53_restoration",
                name="p53 restoration",
                perturbation_type=PerturbationType.GENE_OVEREXPRESSION,
                target_id="TP53",
                magnitude=5.0,
            ),
            Perturbation(
                id="glucose_deprivation",
                name="Glucose deprivation",
                perturbation_type=PerturbationType.METABOLITE_DEPLETION,
                target_id="glucose",
                magnitude=0.9,
            ),
        ]
