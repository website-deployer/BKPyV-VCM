"""Base plugin interface for VCM biological systems."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from vcm.core.models import CellState, ExperimentConfig, Perturbation


class PluginRegistry:
    """Registry for managing available plugins."""

    _plugins: Dict[str, "BasePlugin"] = {}

    @classmethod
    def register(cls, plugin: "BasePlugin") -> None:
        """Register a plugin.

        Args:
            plugin: Plugin instance to register
        """
        cls._plugins[plugin.plugin_id] = plugin

    @classmethod
    def get(cls, plugin_id: str) -> Optional["BasePlugin"]:
        """Get a registered plugin.

        Args:
            plugin_id: ID of the plugin to retrieve

        Returns:
            Plugin instance or None if not found
        """
        return cls._plugins.get(plugin_id)

    @classmethod
    def list_plugins(cls) -> List[str]:
        """List all registered plugin IDs.

        Returns:
            List of plugin IDs
        """
        return list(cls._plugins.keys())


class BasePlugin(ABC):
    """Abstract base class for biological system plugins.

    Each plugin represents a specific biological system (e.g., minimal cell,
    virus-host system, immune cell, etc.) and provides:
    - Default configuration
    - Cell/system schema
    - Supported perturbations
    - Optional custom simulator or adapters
    """

    def __init__(self):
        """Initialize the plugin."""
        self.plugin_id: str
        self.plugin_name: str
        self.plugin_version: str = "0.1.0"
        self.description: str = ""

    @abstractmethod
    def get_default_config(self) -> ExperimentConfig:
        """Get default experiment configuration for this plugin.

        Returns:
            Default ExperimentConfig
        """
        pass

    @abstractmethod
    def create_initial_state(self, config: Optional[Dict[str, Any]] = None) -> CellState:
        """Create initial cell state for this plugin.

        Args:
            config: Optional configuration overrides

        Returns:
            Initial CellState
        """
        pass

    @abstractmethod
    def get_supported_perturbations(self) -> List[Perturbation]:
        """Get list of supported perturbations for this plugin.

        Returns:
            List of Perturbation objects
        """
        pass

    def get_cell_schema(self) -> Dict[str, Any]:
        """Get schema information for the cell model.

        Returns:
            Dictionary with schema information
        """
        initial_state = self.create_initial_state()
        return {
            "plugin_id": self.plugin_id,
            "plugin_name": self.plugin_name,
            "cell_type": initial_state.cell_type,
            "n_genes": len(initial_state.genes),
            "n_proteins": len(initial_state.proteins),
            "n_metabolites": len(initial_state.metabolites),
            "n_pathways": len(initial_state.pathways),
            "gene_ids": list(initial_state.genes.keys()),
            "protein_ids": list(initial_state.proteins.keys()),
            "metabolite_ids": list(initial_state.metabolites.keys()),
            "pathway_ids": list(initial_state.pathways.keys()),
        }

    def validate_perturbation(self, perturbation: Perturbation) -> bool:
        """Validate if a perturbation is supported by this plugin.

        Args:
            perturbation: Perturbation to validate

        Returns:
            True if perturbation is valid for this plugin
        """
        supported = self.get_supported_perturbations()
        return any(p.perturbation_type == perturbation.perturbation_type for p in supported)

    def register(self) -> None:
        """Register this plugin with the global registry."""
        PluginRegistry.register(self)
