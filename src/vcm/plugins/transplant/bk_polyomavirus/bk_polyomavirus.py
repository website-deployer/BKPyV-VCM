"""BK polyomavirus (BKPyV) plugin for kidney tubular epithelial cells.

This plugin models BKPyV infection in renal tubular epithelial cells, incorporating:
- Host DNA replication status and T antigen expression
- Cell cycle phase dynamics
- Immunomodulatory drug effects (tacrolimus vs mTOR inhibitors)
- Single-cell transcriptomic pathway activities
"""

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


class BKPolyomavirusPlugin(BasePlugin):
    """Plugin for BK polyomavirus (BKPyV) infection in kidney tubular epithelial cells.

    This model incorporates key mechanistic insights from single-cell studies:
    - BKPyV requires host DNA replication machinery for viral replication
    - Large T antigen (LT) drives viral replication and modulates host cell cycle
    - Immunomodulatory drugs (tacrolimus, sirolimus) differentially affect viral replication
    - Host pathways (DNA damage response, cell cycle, innate immunity) influence infection outcome

    Key references:
    - BKPyV replication in kidney epithelial cells and role of host DNA replication
    - Single-cell transcriptomics of BKPyV nephropathy
    - Immunomodulatory drug effects on BKPyV replication
    """

    def __init__(self):
        """Initialize the BK polyomavirus plugin."""
        super().__init__()
        self.plugin_id = "transplant.bk_polyomavirus"
        self.plugin_name = "BK Polyomavirus Kidney Cell"
        self.description = "BKPyV infection in renal tubular epithelial cells with drug effects"

    def get_default_config(self) -> ExperimentConfig:
        """Get default experiment configuration for BKPyV.

        Returns:
            Default ExperimentConfig
        """
        return ExperimentConfig(
            experiment_id="bkpyv_default",
            plugin=self.plugin_id,
            simulator="bkpyv_specific",
            simulation_length=100.0,
            timestep=1.0,
            output_path="outputs/bkpyv/",
        )

    def create_initial_state(self, config: Optional[Dict[str, Any]] = None) -> CellState:
        """Create initial cell state for BKPyV-infected kidney tubular epithelial cell.

        This state includes:
        - Key host genes for DNA replication, cell cycle, immune response
        - Viral genes (Large T antigen, Small T antigen, VP1, VP2, VP3)
        - Metabolites for nucleotide synthesis and energy
        - Pathway activity vector based on single-cell transcriptomic profiles

        Args:
            config: Optional configuration overrides

        Returns:
            Initial CellState with BKPyV-specific features
        """
        # Host DNA replication and cell cycle genes
        host_genes = {
            # DNA replication machinery
            "MCM2": Gene(
                id="MCM2",
                name="MCM2 helicase",
                expression_level=1.0,
                function="DNA replication initiation",
                is_essential=True,
            ),
            "MCM5": Gene(
                id="MCM5",
                name="MCM5 helicase",
                expression_level=1.0,
                function="DNA replication",
                is_essential=True,
            ),
            "PCNA": Gene(
                id="PCNA",
                name="Proliferating cell nuclear antigen",
                expression_level=1.2,
                function="DNA replication processivity",
                is_essential=True,
            ),
            "DNA_POL_ALPHA": Gene(
                id="DNA_POL_ALPHA",
                name="DNA polymerase alpha",
                expression_level=1.0,
                function="DNA synthesis",
                is_essential=True,
            ),
            "CDC45": Gene(
                id="CDC45",
                name="CDC45",
                expression_level=1.0,
                function="DNA replication initiation",
                is_essential=True,
            ),
            # Cell cycle regulators
            "CCND1": Gene(
                id="CCND1",
                name="Cyclin D1",
                expression_level=0.8,
                function="G1/S transition",
                is_essential=False,
            ),
            "CDK2": Gene(
                id="CDK2",
                name="Cyclin-dependent kinase 2",
                expression_level=1.0,
                function="Cell cycle progression",
                is_essential=True,
            ),
            "RB1": Gene(
                id="RB1",
                name="Retinoblastoma protein",
                expression_level=1.2,
                function="Cell cycle checkpoint",
                is_essential=True,
            ),
            "TP53": Gene(
                id="TP53",
                name="p53",
                expression_level=1.0,
                function="DNA damage response",
                is_essential=True,
            ),
            # DNA damage response
            "ATM": Gene(
                id="ATM",
                name="ATM kinase",
                expression_level=0.9,
                function="DNA damage sensing",
                is_essential=True,
            ),
            "ATR": Gene(
                id="ATR",
                name="ATR kinase",
                expression_level=0.9,
                function="DNA damage response",
                is_essential=True,
            ),
            "CHEK1": Gene(
                id="CHEK1",
                name="CHK1 kinase",
                expression_level=0.8,
                function="Cell cycle checkpoint",
                is_essential=True,
            ),
            # DDR genes from JVI S4 single-cell data (BRCA1, BRCA2, PRKDC, FANCI, MMS22L)
            # Source: jvi.01382-24-s0004.pdf - upregulated in late BKPyV infection
            "BRCA1": Gene(
                id="BRCA1",
                name="BRCA1 DNA repair",
                expression_level=0.7,
                function="DNA damage response",
                is_essential=True,
            ),
            "BRCA2": Gene(
                id="BRCA2",
                name="BRCA2 DNA repair",
                expression_level=0.7,
                function="DNA damage response",
                is_essential=True,
            ),
            "PRKDC": Gene(
                id="PRKDC",
                name="DNA-PK catalytic subunit",
                expression_level=0.9,
                function="DNA damage response",
                is_essential=True,
            ),
            "FANCI": Gene(
                id="FANCI",
                name="Fanconi anemia complementation group I",
                expression_level=0.6,
                function="DNA damage response",
                is_essential=False,
            ),
            "MMS22L": Gene(
                id="MMS22L",
                name="MMS22L DNA repair",
                expression_level=0.6,
                function="DNA damage response",
                is_essential=False,
            ),
            # Innate immune signaling
            "STAT1": Gene(
                id="STAT1",
                name="STAT1",
                expression_level=0.7,
                function="Antiviral signaling",
                is_essential=False,
            ),
            "IRF7": Gene(
                id="IRF7",
                name="IRF7",
                expression_level=0.5,
                function="Interferon response",
                is_essential=False,
            ),
            "IFNB1": Gene(
                id="IFNB1",
                name="Interferon beta",
                expression_level=0.3,
                function="Antiviral cytokine",
                is_essential=False,
            ),
            # Apoptosis regulators
            "BAX": Gene(
                id="BAX",
                name="BAX",
                expression_level=0.5,
                function="Pro-apoptotic",
                is_essential=False,
            ),
            "BCL2": Gene(
                id="BCL2",
                name="BCL2",
                expression_level=0.6,
                function="Anti-apoptotic",
                is_essential=False,
            ),
            # Cellular stress response
            "HSPA1A": Gene(
                id="HSPA1A",
                name="HSP70",
                expression_level=0.7,
                function="Stress response",
                is_essential=False,
            ),
            # Drug targets
            "FKBP1A": Gene(
                id="FKBP1A",
                name="FKBP12",
                expression_level=1.0,
                function="Tacrolimus binding protein",
                is_essential=False,
            ),
            "MTOR": Gene(
                id="MTOR",
                name="mTOR",
                expression_level=1.0,
                function="mTOR signaling pathway",
                is_essential=True,
            ),
            # Mitochondrial genes from JVI S4 single-cell data (MT-ND4, MT-CO1, MT-CYB)
            # Source: jvi.01382-24-s0004.pdf - upregulated in late BKPyV infection
            # Discordant mitochondria-encoded vs nucleus-encoded expression signature
            "MT-ND4": Gene(
                id="MT-ND4",
                name="MT-ND4",
                expression_level=0.8,
                function="Mitochondrial electron transport",
                is_essential=True,
            ),
            "MT-CO1": Gene(
                id="MT-CO1",
                name="MT-CO1",
                expression_level=0.8,
                function="Mitochondrial electron transport",
                is_essential=True,
            ),
            "MT-CYB": Gene(
                id="MT-CYB",
                name="MT-CYB",
                expression_level=0.8,
                function="Mitochondrial electron transport",
                is_essential=True,
            ),
            # Antigen presentation genes (MHC-I/II) for immune evasion
            # Source: Single-cell data shows downregulation in successful infection
            "HLA-A": Gene(
                id="HLA-A",
                name="HLA-A",
                expression_level=1.0,
                function="Antigen presentation",
                is_essential=False,
            ),
            "HLA-B": Gene(
                id="HLA-B",
                name="HLA-B",
                expression_level=1.0,
                function="Antigen presentation",
                is_essential=False,
            ),
        }

        # Viral genes
        viral_genes = {
            "viral_LT": Gene(
                id="viral_LT",
                name="Large T antigen",
                expression_level=0.0,  # Initially uninfected
                function="Viral replication and cell cycle modulation",
                is_essential=True,
            ),
            "viral_ST": Gene(
                id="viral_ST",
                name="Small T antigen",
                expression_level=0.0,
                function="Viral replication enhancement",
                is_essential=False,
            ),
            "viral_VP1": Gene(
                id="viral_VP1",
                name="Viral protein 1",
                expression_level=0.0,
                function="Capsid protein",
                is_essential=True,
            ),
            "viral_VP2": Gene(
                id="viral_VP2",
                name="Viral protein 2",
                expression_level=0.0,
                function="Capsid protein",
                is_essential=False,
            ),
            "viral_VP3": Gene(
                id="viral_VP3",
                name="Viral protein 3",
                expression_level=0.0,
                function="Capsid protein",
                is_essential=False,
            ),
        }

        genes = {**host_genes, **viral_genes}

        # Host proteins
        host_proteins = {
            "MCM2": Protein(
                id="MCM2",
                name="MCM2 helicase",
                concentration=1.0,
                gene_id="MCM2",
                is_enzyme=True,
            ),
            "PCNA": Protein(
                id="PCNA",
                name="PCNA",
                concentration=1.2,
                gene_id="PCNA",
                is_enzyme=False,
            ),
            "RB1": Protein(
                id="RB1",
                name="RB1",
                concentration=1.2,
                gene_id="RB1",
                is_enzyme=False,
            ),
            "p53": Protein(
                id="p53",
                name="p53",
                concentration=1.0,
                gene_id="TP53",
                is_enzyme=False,
            ),
            "STAT1": Protein(
                id="STAT1",
                name="STAT1",
                concentration=0.7,
                gene_id="STAT1",
                is_enzyme=True,
            ),
            "mTOR": Protein(
                id="mTOR",
                name="mTOR",
                concentration=1.0,
                gene_id="MTOR",
                is_enzyme=True,
            ),
        }

        # Viral proteins
        viral_proteins = {
            "LT": Protein(
                id="LT",
                name="Large T antigen",
                concentration=0.0,
                gene_id="viral_LT",
                is_enzyme=True,
                active=False,
            ),
            "ST": Protein(
                id="ST",
                name="Small T antigen",
                concentration=0.0,
                gene_id="viral_ST",
                is_enzyme=False,
                active=False,
            ),
            "VP1": Protein(
                id="VP1",
                name="VP1",
                concentration=0.0,
                gene_id="viral_VP1",
                is_enzyme=False,
                active=False,
            ),
        }

        proteins = {**host_proteins, **viral_proteins}

        # Metabolites (nucleotide synthesis and energy)
        metabolites = {
            "atp": Metabolite(
                id="atp",
                name="ATP",
                concentration=3.0,
                compartment="cytoplasm",
                is_essential=True,
            ),
            "dATP": Metabolite(
                id="dATP",
                name="dATP",
                concentration=0.5,
                compartment="nucleus",
                is_essential=True,
            ),
            "dCTP": Metabolite(
                id="dCTP",
                name="dCTP",
                concentration=0.5,
                compartment="nucleus",
                is_essential=True,
            ),
            "dGTP": Metabolite(
                id="dGTP",
                name="dGTP",
                concentration=0.5,
                compartment="nucleus",
                is_essential=True,
            ),
            "dTTP": Metabolite(
                id="dTTP",
                name="dTTP",
                concentration=0.5,
                compartment="nucleus",
                is_essential=True,
            ),
            "amino_acids": Metabolite(
                id="amino_acids",
                name="Amino acids",
                concentration=2.0,
                compartment="cytoplasm",
                is_essential=True,
            ),
        }

        # Define pathways with activity scores based on single-cell data
        # These represent the 10-15 key pathways identified from transcriptomics
        pathways = {
            "dna_replication": Pathway(
                id="dna_replication",
                name="DNA Replication",
                genes=["MCM2", "MCM5", "PCNA", "DNA_POL_ALPHA", "CDC45"],
                proteins=["MCM2", "PCNA"],
                metabolites=["dATP", "dCTP", "dGTP", "dTTP", "atp"],
                flux=0.8,  # Baseline activity
            ),
            "cell_cycle": Pathway(
                id="cell_cycle",
                name="Cell Cycle Regulation",
                genes=["CCND1", "CDK2", "RB1", "TP53"],
                proteins=["RB1"],
                metabolites=[],
                flux=0.6,  # Baseline activity
            ),
            "dna_damage_response": Pathway(
                id="dna_damage_response",
                name="DNA Damage Response",
                genes=["ATM", "ATR", "CHEK1", "TP53", "BRCA1", "BRCA2", "PRKDC", "FANCI", "MMS22L"],
                proteins=["p53"],
                metabolites=[],
                flux=0.3,  # Baseline activity
            ),
            "innate_immune": Pathway(
                id="innate_immune",
                name="Innate Immune Signaling",
                genes=["STAT1", "IRF7", "IFNB1"],
                proteins=["STAT1"],
                metabolites=[],
                flux=0.5,  # Baseline activity
            ),
            "apoptosis": Pathway(
                id="apoptosis",
                name="Apoptosis Regulation",
                genes=["BAX", "BCL2"],
                proteins=[],
                metabolites=[],
                flux=0.2,  # Baseline activity
            ),
            "mTOR_signaling": Pathway(
                id="mTOR_signaling",
                name="mTOR Signaling Pathway",
                genes=["MTOR", "FKBP1A"],
                proteins=["mTOR"],
                metabolites=[],
                flux=1.0,  # Baseline activity
            ),
            "viral_replication": Pathway(
                id="viral_replication",
                name="Viral Replication",
                genes=["viral_LT", "viral_ST", "viral_VP1", "viral_VP2", "viral_VP3"],
                proteins=["LT", "ST", "VP1"],
                metabolites=["dATP", "dCTP", "dGTP", "dTTP", "atp", "amino_acids"],
                flux=0.0,  # Initially no viral replication
            ),
            "cellular_stress": Pathway(
                id="cellular_stress",
                name="Cellular Stress Response",
                genes=["HSPA1A"],
                proteins=[],
                metabolites=[],
                flux=0.3,  # Baseline activity
            ),
            "interferon_response": Pathway(
                id="interferon_response",
                name="Interferon Response",
                genes=["IFNB1", "STAT1", "IRF7"],
                proteins=["STAT1"],
                metabolites=[],
                flux=0.4,  # Baseline activity
            ),
            "nucleotide_synthesis": Pathway(
                id="nucleotide_synthesis",
                name="Nucleotide Synthesis",
                genes=[],
                proteins=[],
                metabolites=["dATP", "dCTP", "dGTP", "dTTP", "atp"],
                flux=0.7,  # Baseline activity
            ),
            # Mitochondrial stress pathway - late phase specific
            # Source: jvi.01382-24-s0004.pdf - discordant mt vs nuclear expression in late BKPyV
            # MT-ND4, MT-CO1, MT-CYB, MT-ATP6 upregulated in late infection
            "mitochondrial_stress": Pathway(
                id="mitochondrial_stress",
                name="Mitochondrial Stress",
                genes=["MT-ND4", "MT-CO1", "MT-CYB"],
                proteins=[],
                metabolites=["atp"],
                flux=0.0,  # Baseline - emerges in late infection
            ),
            # Antigen presentation pathway - immune evasion mechanism
            # Source: Single-cell data shows downregulation in successful infection
            "antigen_presentation": Pathway(
                id="antigen_presentation",
                name="Antigen Presentation",
                genes=["HLA-A", "HLA-B"],
                proteins=[],
                metabolites=[],
                flux=1.0,  # Baseline - normal MHC expression
            ),
            # NEW: Translation pathway (highly elevated in infection, factor 2.0)
            # Source: jvi.01382-24-s0003.pdf - top pathway in BKPyV-infected cells
            "translation": Pathway(
                id="translation",
                name="Translation",
                genes=["EEF1A1", "EEF1B2"],
                proteins=["EEF1A1"],
                metabolites=["amino_acids", "atp"],
                flux=0.7,  # Baseline activity, highly elevated in infection
            ),
            # NEW: Protein degradation pathway (proteasome involvement)
            # Source: jvi.01382-24-s0003.pdf - ubiquitin-mediated degradation pathway
            "protein_degradation": Pathway(
                id="protein_degradation",
                name="Protein Degradation",
                genes=[],
                proteins=[],
                metabolites=[],
                flux=0.5,  # Baseline activity
            ),
        }

        # Create the cell state with enhanced metadata
        metadata = {
            # Cell cycle state (G0/G1, S, G2/M)
            "cell_cycle_phase": "G0/G1",
            # Host DNA synthesis status (active, inactive, suppressed)
            "host_dna_synthesis": "active",
            # T antigen expression (none, low, medium, high)
            "t_antigen_level": "none",
            # Viral load (log scale, copies/mL equivalent)
            "viral_load": 0.0,
            # Infection status (uninfected, latent, active_lytic)
            "infection_status": "uninfected",
            # NEW: Viral replication phase (early vs late) - critical for drug timing effects
            # Early: 0-24h post-infection, drug-sensitive; Late: >24h, drug-resistant
            # Source: AJT-16-821.pdf - sirolimus effective only during early gene expression
            "viral_replication_phase": "none",  # options: none, early, late
            # NEW: Mitochondrial stress state - single-cell signature (discordant mt vs nuclear expression)
            # Source: jvi.01382-24-s0004.pdf - mitochondrial genes upregulated in late infection
            "mitochondrial_stress": 0.0,  # continuous 0-1 scale
            # NEW: Antigen presentation state - MHC-I/II expression for immune detection
            # Source: Single-cell data shows downregulation in successful infection
            "antigen_presentation": 1.0,  # continuous 0-1 scale, baseline = 1.0 (normal)
            # NEW: Innate immune suppression state - viral evasion mechanism
            # Source: Single-cell data shows innate immune pathway downregulation
            "innate_immune_suppression": 0.0,  # continuous 0-1 scale
            # Pathway activity vector (enhanced with research-validated pathways)
            "pathway_activities": {
                "dna_replication": 0.8,
                "cell_cycle": 0.6,
                "dna_damage_response": 0.3,
                "innate_immune": 0.5,
                "apoptosis": 0.2,
                "mTOR_signaling": 1.0,
                "viral_replication": 0.0,
                "cellular_stress": 0.3,
                "interferon_response": 0.4,
                "nucleotide_synthesis": 0.7,
                # Mitochondrial stress pathway - emerges in late infection (single-cell validated)
                "mitochondrial_stress": 0.0,
                # Antigen presentation pathway - immune evasion mechanism (downregulated in infection)
                "antigen_presentation": 1.0,
                # Translation pathway (highly elevated in infection, factor 2.0)
                "translation": 0.7,
                # Protein degradation pathway (proteasome involvement)
                "protein_degradation": 0.5,
            },
            # Drug effects (enhanced with multiple drugs and concentration tracking)
            "drug_effects": {
                "tacrolimus": 0.0,  # FKBP-12 targeting, activates replication
                "sirolimus": 0.0,  # mTOR inhibition, suppresses replication
                "everolimus": 0.0,  # alternative mTOR inhibitor
            },
            # NEW: Time since infection for phase transitions (critical for drug timing)
            "time_since_infection": 0.0,  # hours
            # NEW: Drug exposure duration for pharmacodynamics
            "drug_exposure_duration": {
                "tacrolimus": 0.0,  # hours
                "sirolimus": 0.0,  # hours
            },
        }

        return CellState(
            cell_id="bkpyv_kidney_cell_001",
            cell_type="kidney_tubular_epithelial",
            genes=genes,
            proteins=proteins,
            metabolites=metabolites,
            pathways=pathways,
            metadata=metadata,
        )

    def get_supported_perturbations(self) -> List[Perturbation]:
        """Get supported perturbations for BKPyV model.

        Includes:
        - BKPyV infection
        - Tacrolimus (calcineurin inhibitor)
        - Sirolimus (mTOR inhibitor)
        - Reduced immunosuppression
        - Antiviral treatment

        Returns:
            List of Perturbation objects
        """
        return [
            Perturbation(
                id="bkpyv_infection",
                name="BKPyV infection",
                perturbation_type=PerturbationType.VIRAL_INFECTION,
                magnitude=1.0,
                timing=10.0,
                parameters={
                    "infection_dose": 1000,
                    "cell_tropism": "kidney_tubular",
                },
            ),
            Perturbation(
                id="tacrolimus_treatment",
                name="Tacrolimus (calcineurin inhibitor)",
                perturbation_type=PerturbationType.DRUG_TREATMENT,
                target_id="FKBP1A",
                magnitude=1.0,
                timing=0.0,
                parameters={
                    "mechanism": "calcineurin_inhibition",
                    "effect_on_viral_replication": "enhances",
                },
            ),
            Perturbation(
                id="sirolimus_treatment",
                name="Sirolimus (mTOR inhibitor)",
                perturbation_type=PerturbationType.DRUG_TREATMENT,
                target_id="MTOR",
                magnitude=1.0,
                timing=0.0,
                parameters={
                    "mechanism": "mTOR_inhibition",
                    "effect_on_viral_replication": "suppresses",
                },
            ),
            Perturbation(
                id="reduced_immunosuppression",
                name="Reduced immunosuppression",
                perturbation_type=PerturbationType.DRUG_TREATMENT,
                magnitude=0.5,
                timing=0.0,
                parameters={
                    "mechanism": "immune_recovery",
                    "effect_on_viral_replication": "suppresses",
                },
            ),
            Perturbation(
                id="antiviral_treatment",
                name="Antiviral treatment (cidofovir/leflunomide)",
                perturbation_type=PerturbationType.DRUG_TREATMENT,
                target_id="viral_LT",
                magnitude=0.8,
                timing=20.0,
                parameters={
                    "mechanism": "viral_polymerase_inhibition",
                    "effect_on_viral_replication": "suppresses",
                },
            ),
            Perturbation(
                id="dna_damage",
                name="DNA damage induction",
                perturbation_type=PerturbationType.ENVIRONMENTAL_CHANGE,
                magnitude=0.5,
                timing=15.0,
                parameters={
                    "type": "oxidative_damage",
                    "effect_on_viral_replication": "enhances",
                },
            ),
        ]

    def get_cell_schema(self) -> Dict[str, Any]:
        """Get enhanced schema for BKPyV kidney cell.

        Returns:
            Dictionary with schema information including pathway activities
        """
        schema = super().get_cell_schema()
        initial_state = self.create_initial_state()

        # Add BKPyV-specific information
        schema["viral_genes"] = ["viral_LT", "viral_ST", "viral_VP1", "viral_VP2", "viral_VP3"]
        schema["pathway_activities"] = initial_state.metadata["pathway_activities"]
        schema["cell_cycle_phases"] = ["G0/G1", "S", "G2/M"]
        schema["drug_targets"] = ["FKBP1A", "MTOR"]
        schema["key_pathways"] = [
            "dna_replication",
            "cell_cycle",
            "dna_damage_response",
            "innate_immune",
            "apoptosis",
            "mTOR_signaling",
            "viral_replication",
            "cellular_stress",
            "interferon_response",
            "nucleotide_synthesis",
        ]

        return schema
