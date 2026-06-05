"""Tests for plugin system."""

import pytest

from vcm.plugins.bacteria.minimal_cell import MinimalCellPlugin
from vcm.plugins.base import PluginRegistry
from vcm.plugins.virus_host.sars_cov2 import SARSCoV2Plugin


def test_plugin_registry():
    """Test plugin registry functionality."""
    registry = PluginRegistry()

    # Initially may have auto-registered plugins (e.g., BKPyV)
    initial_count = len(registry.list_plugins())

    # Register a plugin
    plugin = MinimalCellPlugin()
    plugin.register()

    # Should now have one more plugin than initially
    assert len(registry.list_plugins()) == initial_count + 1
    assert "bacteria.minimal_cell" in registry.list_plugins()

    # Get the plugin
    retrieved = registry.get("bacteria.minimal_cell")
    assert retrieved is not None
    assert retrieved.plugin_id == "bacteria.minimal_cell"


def test_minimal_cell_plugin():
    """Test MinimalCellPlugin."""
    plugin = MinimalCellPlugin()
    assert plugin.plugin_id == "bacteria.minimal_cell"
    assert plugin.plugin_name == "Minimal Bacterial Cell"

    # Test default config
    config = plugin.get_default_config()
    assert config.plugin == "bacteria.minimal_cell"
    assert config.simulator == "mechanistic"

    # Test initial state creation
    state = plugin.create_initial_state()
    assert state.cell_type == "minimal_bacterium"
    assert len(state.genes) > 0
    assert len(state.proteins) > 0
    assert len(state.metabolites) > 0
    assert len(state.pathways) > 0

    # Test supported perturbations
    perturbations = plugin.get_supported_perturbations()
    assert len(perturbations) > 0

    # Test schema
    schema = plugin.get_cell_schema()
    assert schema["cell_type"] == "minimal_bacterium"
    assert schema["n_genes"] > 0
    assert schema["n_proteins"] > 0


def test_sars_cov2_plugin():
    """Test SARSCoV2Plugin."""
    plugin = SARSCoV2Plugin()
    assert plugin.plugin_id == "virus_host.sars_cov2"
    assert plugin.plugin_name == "SARS-CoV-2 Virus-Host"

    # Test default config
    config = plugin.get_default_config()
    assert config.plugin == "virus_host.sars_cov2"
    assert config.simulator == "hybrid"

    # Test initial state creation
    state = plugin.create_initial_state()
    assert state.cell_type == "sars_cov2_host"
    assert len(state.genes) > 0
    # Should have viral genes
    assert "viral_spike" in state.genes

    # Test supported perturbations
    perturbations = plugin.get_supported_perturbations()
    assert len(perturbations) > 0

    # Test schema
    schema = plugin.get_cell_schema()
    assert schema["cell_type"] == "sars_cov2_host"


def test_perturbation_validation():
    """Test perturbation validation."""
    plugin = MinimalCellPlugin()
    perturbations = plugin.get_supported_perturbations()

    # Valid perturbation
    valid = plugin.validate_perturbation(perturbations[0])
    assert valid is True

    # Invalid perturbation type (create a custom one)
    from vcm.core.models import Perturbation, PerturbationType

    invalid_pert = Perturbation(
        id="invalid",
        name="Invalid",
        perturbation_type=PerturbationType.RADIATION,
        target_id="gene1",
        magnitude=1.0,
    )
    invalid = plugin.validate_perturbation(invalid_pert)
    assert invalid is False
