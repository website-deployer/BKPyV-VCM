"""Tests for core domain models."""

import pytest

from vcm.core.models import (
    CellState,
    Environment,
    ExperimentConfig,
    Gene,
    Metabolite,
    Pathway,
    Perturbation,
    PerturbationType,
    Protein,
    SimulationResult,
    SimulationStep,
)


def test_gene_creation():
    """Test Gene model creation."""
    gene = Gene(id="gene1", name="Test Gene", expression_level=1.5)
    assert gene.id == "gene1"
    assert gene.name == "Test Gene"
    assert gene.expression_level == 1.5
    assert gene.is_essential is False


def test_protein_creation():
    """Test Protein model creation."""
    protein = Protein(id="prot1", name="Test Protein", concentration=2.0, gene_id="gene1")
    assert protein.id == "prot1"
    assert protein.concentration == 2.0
    assert protein.gene_id == "gene1"
    assert protein.active is True


def test_metabolite_creation():
    """Test Metabolite model creation."""
    metabolite = Metabolite(id="met1", name="Glucose", concentration=5.0)
    assert metabolite.id == "met1"
    assert metabolite.concentration == 5.0
    assert metabolite.compartment == "cytoplasm"


def test_pathway_creation():
    """Test Pathway model creation."""
    pathway = Pathway(id="path1", name="Glycolysis", proteins=["prot1"], metabolites=["met1"])
    assert pathway.id == "path1"
    assert "prot1" in pathway.proteins
    assert "met1" in pathway.metabolites
    assert pathway.flux == 1.0


def test_perturbation_creation():
    """Test Perturbation model creation."""
    perturbation = Perturbation(
        id="pert1",
        name="Test Perturbation",
        perturbation_type=PerturbationType.GENE_KNOCKOUT,
        target_id="gene1",
        magnitude=1.0,
    )
    assert perturbation.id == "pert1"
    assert perturbation.perturbation_type == PerturbationType.GENE_KNOCKOUT
    assert perturbation.target_id == "gene1"


def test_environment_creation():
    """Test Environment model creation."""
    env = Environment(temperature=37.0, ph=7.4)
    assert env.temperature == 37.0
    assert env.ph == 7.4
    assert env.glucose_concentration == 5.0


def test_cell_state_creation():
    """Test CellState model creation."""
    state = CellState(
        cell_id="cell1",
        cell_type="test_cell",
        genes={"gene1": Gene(id="gene1", name="Gene 1", expression_level=1.0)},
        proteins={"prot1": Protein(id="prot1", name="Protein 1", concentration=1.0)},
    )
    assert state.cell_id == "cell1"
    assert state.cell_type == "test_cell"
    assert "gene1" in state.genes
    assert "prot1" in state.proteins


def test_cell_state_vector():
    """Test CellState vector representation."""
    state = CellState(
        cell_id="cell1",
        cell_type="test_cell",
        genes={"gene1": Gene(id="gene1", name="Gene 1", expression_level=1.0)},
        proteins={"prot1": Protein(id="prot1", name="Protein 1", concentration=2.0)},
        metabolites={"met1": Metabolite(id="met1", name="Metabolite 1", concentration=3.0)},
    )
    vector = state.get_state_vector()
    assert len(vector) == 3
    assert vector[0] == 1.0  # gene expression
    assert vector[1] == 2.0  # protein concentration
    assert vector[2] == 3.0  # metabolite concentration


def test_simulation_step_creation():
    """Test SimulationStep model creation."""
    state = CellState(
        cell_id="cell1",
        cell_type="test_cell",
        genes={},
        proteins={},
    )
    step = SimulationStep(step_number=0, timestamp=0.0, cell_state=state)
    assert step.step_number == 0
    assert step.timestamp == 0.0
    assert step.cell_state.cell_id == "cell1"


def test_simulation_result_creation():
    """Test SimulationResult model creation."""
    result = SimulationResult(
        experiment_id="exp1",
        simulator_type="mechanistic",
        plugin="test",
        config_id="default",
    )
    assert result.experiment_id == "exp1"
    assert result.simulator_type == "mechanistic"
    assert result.success is True
    assert len(result.steps) == 0


def test_simulation_result_trajectory():
    """Test trajectory extraction from SimulationResult."""
    state1 = CellState(
        cell_id="cell1",
        cell_type="test_cell",
        genes={"gene1": Gene(id="gene1", name="Gene 1", expression_level=1.0)},
        proteins={},
        metabolites={},
        pathways={},
    )
    state2 = CellState(
        cell_id="cell1",
        cell_type="test_cell",
        genes={"gene1": Gene(id="gene1", name="Gene 1", expression_level=2.0)},
        proteins={},
        metabolites={},
        pathways={},
    )

    step1 = SimulationStep(step_number=0, timestamp=0.0, cell_state=state1)
    step2 = SimulationStep(step_number=1, timestamp=1.0, cell_state=state2)

    result = SimulationResult(
        experiment_id="exp1",
        simulator_type="mechanistic",
        plugin="test",
        config_id="default",
        steps=[step1, step2],
    )

    trajectory = result.get_trajectory("gene1", "gene")
    assert len(trajectory) == 2
    assert trajectory[0] == 1.0
    assert trajectory[1] == 2.0


def test_experiment_config_creation():
    """Test ExperimentConfig model creation."""
    config = ExperimentConfig(
        experiment_id="exp1",
        plugin="test_plugin",
        simulator="mechanistic",
        simulation_length=100.0,
        timestep=1.0,
    )
    assert config.experiment_id == "exp1"
    assert config.plugin == "test_plugin"
    assert config.simulator == "mechanistic"
    assert config.simulation_length == 100.0
    assert config.timestep == 1.0
