"""Data loading and validation utilities."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import ValidationError

from vcm.core.models import (
    CellState,
    Gene,
    Metabolite,
    Pathway,
    Protein,
)


class DataValidator:
    """Validator for data schemas."""

    @staticmethod
    def validate_gene(data: Dict[str, Any]) -> bool:
        """Validate gene data structure.

        Args:
            data: Dictionary containing gene data

        Returns:
            True if valid
        """
        required_fields = ["id", "name", "expression_level"]
        return all(field in data for field in required_fields)

    @staticmethod
    def validate_protein(data: Dict[str, Any]) -> bool:
        """Validate protein data structure.

        Args:
            data: Dictionary containing protein data

        Returns:
            True if valid
        """
        required_fields = ["id", "name", "concentration"]
        return all(field in data for field in required_fields)

    @staticmethod
    def validate_metabolite(data: Dict[str, Any]) -> bool:
        """Validate metabolite data structure.

        Args:
            data: Dictionary containing metabolite data

        Returns:
            True if valid
        """
        required_fields = ["id", "name", "concentration"]
        return all(field in data for field in required_fields)


class DataLoader:
    """Load and manage biological datasets."""

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the data loader.

        Args:
            data_dir: Base directory for data files
        """
        self.data_dir = data_dir or Path("data")
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.mock_dir = self.data_dir / "mock"

        # Ensure directories exist
        for dir_path in [self.raw_dir, self.processed_dir, self.mock_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load data from JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Dictionary containing loaded data
        """
        with open(file_path, "r") as f:
            return json.load(f)

    def load_csv(self, file_path: Path) -> pd.DataFrame:
        """Load data from CSV file.

        Args:
            file_path: Path to CSV file

        Returns:
            DataFrame containing loaded data
        """
        return pd.read_csv(file_path)

    def save_json(self, data: Dict[str, Any], file_path: Path) -> None:
        """Save data to JSON file.

        Args:
            data: Dictionary to save
            file_path: Path to save file
        """
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def save_csv(self, data: pd.DataFrame, file_path: Path) -> None:
        """Save data to CSV file.

        Args:
            data: DataFrame to save
            file_path: Path to save file
        """
        data.to_csv(file_path, index=False)

    def load_cell_state_from_json(self, file_path: Path) -> CellState:
        """Load a CellState from JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            CellState object
        """
        data = self.load_json(file_path)

        # Convert dictionaries to objects
        genes = {g_id: Gene(**g_data) for g_id, g_data in data.get("genes", {}).items()}
        proteins = {p_id: Protein(**p_data) for p_id, p_data in data.get("proteins", {}).items()}
        metabolites = {m_id: Metabolite(**m_data) for m_id, m_data in data.get("metabolites", {}).items()}
        pathways = {p_id: Pathway(**p_data) for p_id, p_data in data.get("pathways", {}).items()}

        return CellState(
            cell_id=data["cell_id"],
            cell_type=data["cell_type"],
            timestamp=data.get("timestamp", 0.0),
            genes=genes,
            proteins=proteins,
            metabolites=metabolites,
            pathways=pathways,
            metadata=data.get("metadata", {}),
        )

    def save_cell_state_to_json(self, state: CellState, file_path: Path) -> None:
        """Save a CellState to JSON file.

        Args:
            state: CellState to save
            file_path: Path to save file
        """
        # Convert objects to dictionaries
        data = {
            "cell_id": state.cell_id,
            "cell_type": state.cell_type,
            "timestamp": state.timestamp,
            "genes": {g_id: g.model_dump() for g_id, g in state.genes.items()},
            "proteins": {p_id: p.model_dump() for p_id, p in state.proteins.items()},
            "metabolites": {m_id: m.model_dump() for m_id, m in state.metabolites.items()},
            "pathways": {p_id: p.model_dump() for p_id, p in state.pathways.items()},
            "metadata": state.metadata,
        }

        self.save_json(data, file_path)

    def load_mock_dataset(self, dataset_name: str) -> Dict[str, Any]:
        """Load a mock dataset by name.

        Args:
            dataset_name: Name of the mock dataset

        Returns:
            Dictionary containing the mock data
        """
        file_path = self.mock_dir / f"{dataset_name}.json"
        return self.load_json(file_path)

    def list_mock_datasets(self) -> List[str]:
        """List available mock datasets.

        Returns:
            List of dataset names
        """
        if not self.mock_dir.exists():
            return []
        return [f.stem for f in self.mock_dir.glob("*.json")]
