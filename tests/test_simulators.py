"""Tests for simulator implementations."""

import pytest

from vcm.core.models import CellState, Environment, Gene, Protein
from vcm.simulators.base import BaseSimulator
from vcm.simulators.hybrid import HybridSimulator
from vcm.simulators.mechanistic import MechanisticSimulator
from vcm.simulators.ml_based import MLBasedSimulator


def test_base_simulator_interface():
    """Test that BaseSimulator defines the required interface."""
    # BaseSimulator is abstract, so we can't instantiate it directly
    # But we can check that the methods are defined
    assert hasattr(BaseSimulator, "simulate")
    assert hasattr(BaseSimulator, "step")
    assert hasattr(BaseSimulator, "get_simulator_info")


def test_mechanistic_simulator_creation():
    """Test MechanisticSimulator creation."""
    sim = MechanisticSimulator()
    assert sim is not None
    assert sim.decay_rate == 0.05
    assert sim.growth_rate == 0.1

    sim_with_config = MechanisticSimulator({"decay_rate": 0.1, "growth_rate": 0.2})
    assert sim_with_config.decay_rate == 0.1
    assert sim_with_config.growth_rate == 0.2


def test_mechanistic_simulator_step():
    """Test MechanisticSimulator step function."""
    sim = MechanisticSimulator()
    state = CellState(
        cell_id="cell1",
        cell_type="test_cell",
        genes={"gene1": Gene(id="gene1", name="Gene 1", expression_level=1.0)},
        proteins={"prot1": Protein(id="prot1", name="Protein 1", concentration=1.0, gene_id="gene1")},
        metabolites={},
        pathways={},
    )

    new_state = sim.step(state, None, Environment(), 1.0)
    assert new_state.timestamp == 1.0
    assert new_state.cell_id == "cell1"
    # Gene expression should change due to growth/decay
    assert new_state.genes["gene1"].expression_level != 1.0


def test_mechanistic_simulator_simulate():
    """Test MechanisticSimulator simulate function."""
    sim = MechanisticSimulator()
    state = CellState(
        cell_id="cell1",
        cell_type="test_cell",
        genes={"gene1": Gene(id="gene1", name="Gene 1", expression_level=1.0)},
        proteins={"prot1": Protein(id="prot1", name="Protein 1", concentration=1.0, gene_id="gene1")},
        metabolites={},
        pathways={},
    )

    result = sim.simulate(state, None, Environment(), n_steps=10, timestep=1.0)
    assert result is not None
    assert result.simulator_type == "mechanistic"
    assert len(result.steps) == 10
    assert result.final_state is not None
    assert result.final_state.timestamp == 10.0


def test_ml_based_simulator_creation():
    """Test MLBasedSimulator creation."""
    sim = MLBasedSimulator()
    assert sim is not None
    assert sim.hidden_size == 64
    assert sim.learning_rate == 0.01


def test_ml_based_simulator_step():
    """Test MLBasedSimulator step function."""
    sim = MLBasedSimulator()
    state = CellState(
        cell_id="cell1",
        cell_type="test_cell",
        genes={"gene1": Gene(id="gene1", name="Gene 1", expression_level=1.0)},
        proteins={"prot1": Protein(id="prot1", name="Protein 1", concentration=1.0, gene_id="gene1")},
        metabolites={},
        pathways={},
    )

    new_state = sim.step(state, None, Environment(), 1.0)
    assert new_state.timestamp == 1.0
    assert new_state.cell_id == "cell1"


def test_ml_based_simulator_simulate():
    """Test MLBasedSimulator simulate function."""
    sim = MLBasedSimulator()
    state = CellState(
        cell_id="cell1",
        cell_type="test_cell",
        genes={"gene1": Gene(id="gene1", name="Gene 1", expression_level=1.0)},
        proteins={"prot1": Protein(id="prot1", name="Protein 1", concentration=1.0, gene_id="gene1")},
        metabolites={},
        pathways={},
    )

    result = sim.simulate(state, None, Environment(), n_steps=10, timestep=1.0)
    assert result is not None
    assert result.simulator_type == "ml_based"
    assert len(result.steps) == 10
    assert result.final_state is not None


def test_hybrid_simulator_creation():
    """Test HybridSimulator creation."""
    sim = HybridSimulator()
    assert sim is not None
    assert sim.mechanistic_weight == 0.7
    assert sim.ml_weight == 0.3


def test_hybrid_simulator_step():
    """Test HybridSimulator step function."""
    sim = HybridSimulator()
    state = CellState(
        cell_id="cell1",
        cell_type="test_cell",
        genes={"gene1": Gene(id="gene1", name="Gene 1", expression_level=1.0)},
        proteins={"prot1": Protein(id="prot1", name="Protein 1", concentration=1.0, gene_id="gene1")},
        metabolites={},
        pathways={},
    )

    new_state = sim.step(state, None, Environment(), 1.0)
    assert new_state.timestamp == 1.0
    assert new_state.cell_id == "cell1"


def test_hybrid_simulator_simulate():
    """Test HybridSimulator simulate function."""
    sim = HybridSimulator()
    state = CellState(
        cell_id="cell1",
        cell_type="test_cell",
        genes={"gene1": Gene(id="gene1", name="Gene 1", expression_level=1.0)},
        proteins={"prot1": Protein(id="prot1", name="Protein 1", concentration=1.0, gene_id="gene1")},
        metabolites={},
        pathways={},
    )

    result = sim.simulate(state, None, Environment(), n_steps=10, timestep=1.0)
    assert result is not None
    assert result.simulator_type == "hybrid"
    assert len(result.steps) == 10
    assert result.final_state is not None


def test_simulator_info():
    """Test simulator info method."""
    sim = MechanisticSimulator()
    info = sim.get_simulator_info()
    assert "simulator_type" in info
    assert info["simulator_type"] == "MechanisticSimulator"
    assert "config" in info
