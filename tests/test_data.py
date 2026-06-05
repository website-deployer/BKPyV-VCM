"""Tests for data loading functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from vcm.data.loader import DataLoader, DataValidator
from vcm.core.models import CellState, Gene, Protein


def test_data_validator_gene():
    """Test gene validation."""
    validator = DataValidator()
    valid_data = {"id": "gene1", "name": "Test Gene", "expression_level": 1.0}
    assert validator.validate_gene(valid_data) is True

    invalid_data = {"id": "gene1", "name": "Test Gene"}
    assert validator.validate_gene(invalid_data) is False


def test_data_validator_protein():
    """Test protein validation."""
    validator = DataValidator()
    valid_data = {"id": "prot1", "name": "Test Protein", "concentration": 1.0}
    assert validator.validate_protein(valid_data) is True

    invalid_data = {"id": "prot1", "name": "Test Protein"}
    assert validator.validate_protein(invalid_data) is False


def test_data_validator_metabolite():
    """Test metabolite validation."""
    validator = DataValidator()
    valid_data = {"id": "met1", "name": "Test Metabolite", "concentration": 1.0}
    assert validator.validate_metabolite(valid_data) is True

    invalid_data = {"id": "met1", "name": "Test Metabolite"}
    assert validator.validate_metabolite(invalid_data) is False


def test_data_loader_creation():
    """Test DataLoader creation."""
    loader = DataLoader()
    assert loader.data_dir == Path("data")
    assert loader.raw_dir.exists()
    assert loader.processed_dir.exists()
    assert loader.mock_dir.exists()


def test_data_loader_json_operations():
    """Test JSON load/save operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = DataLoader(data_dir=Path(tmpdir))
        test_data = {"test": "data", "number": 42}

        # Save
        test_file = loader.mock_dir / "test.json"
        loader.save_json(test_data, test_file)

        # Load
        loaded_data = loader.load_json(test_file)
        assert loaded_data == test_data


def test_data_loader_cell_state_save_load():
    """Test saving and loading CellState."""
    state = CellState(
        cell_id="cell1",
        cell_type="test_cell",
        genes={"gene1": Gene(id="gene1", name="Gene 1", expression_level=1.0)},
        proteins={"prot1": Protein(id="prot1", name="Protein 1", concentration=1.0, gene_id="gene1")},
        metabolites={},
        pathways={},
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        loader = DataLoader(data_dir=Path(tmpdir))
        test_file = loader.mock_dir / "cell_state.json"

        # Save
        loader.save_cell_state_to_json(state, test_file)

        # Load
        loaded_state = loader.load_cell_state_from_json(test_file)
        assert loaded_state.cell_id == state.cell_id
        assert loaded_state.cell_type == state.cell_type
        assert "gene1" in loaded_state.genes
        assert loaded_state.genes["gene1"].expression_level == 1.0


def test_data_loader_list_mock_datasets():
    """Test listing mock datasets."""
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = DataLoader(data_dir=Path(tmpdir))

        # Create some mock datasets
        loader.save_json({"test": "data1"}, loader.mock_dir / "dataset1.json")
        loader.save_json({"test": "data2"}, loader.mock_dir / "dataset2.json")

        # List
        datasets = loader.list_mock_datasets()
        assert len(datasets) == 2
        assert "dataset1" in datasets
        assert "dataset2" in datasets
