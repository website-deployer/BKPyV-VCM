"""Clinical Parameter Calibration for BKPyV Plugin.

This module provides calibration functions to tune BKPyV simulation parameters
to match clinical cohort observations. It uses extracted clinical table data
from research papers to calibrate:

1. Time to first viremia (from transplant to detectable viral load)
2. Peak viral load timing and magnitude
3. Viral load kinetics (rise and fall patterns)
4. Immunouppression reduction effects on viral clearance

Research Data Sources:
- Extracted clinical tables from DOCX files (GcfDNA, risk factor tables)
- Published cohort studies on BK viremia kinetics
- Clinical guidelines for DNAemia thresholds
- Drug effect data from clinical trials

Calibration Approach:
- Use extracted clinical data as targets
- Optimize simulation parameters to match timing and magnitude
- Apply objective functions for matching clinical trajectories
- Use sensitivity analysis to identify key parameters
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
import csv
from pathlib import Path


@dataclass
class ClinicalTarget:
    """Clinical observations to match during calibration."""
    
    # Time to first viremia (days)
    time_to_first_viremia_mean: float = 30.0  # ~1 month post-transplant
    time_to_first_viremia_std: float = 15.0   # ±2 weeks
    
    # Peak viral load (copies/mL)
    peak_viral_load_mean: float = 50000.0      # 50,000 copies/mL
    peak_viral_load_std: float = 30000.0       # Wide range
    
    # Time to peak (days)
    time_to_peak_mean: float = 60.0            # ~2 months post-transplant
    time_to_peak_std: float = 30.0
    
    # Viral clearance after immunosuppression reduction
    clearance_rate_mean: float = 0.1           # Per day
    clearance_rate_std: float = 0.05
    
    # Clinical threshold crossing times
    time_to_1000_copies: float = 40.0           # Screening threshold
    time_to_10000_copies: float = 60.0          # High-risk threshold


@dataclass
class CalibrationResult:
    """Result of parameter calibration."""
    
    calibrated_params: Dict[str, float]
    objective_value: float
    matched_targets: Dict[str, float]
    calibration_metadata: Dict[str, any]


class ClinicalCalibration:
    """Clinical parameter calibration for BKPyV simulations.
    
    This class provides methods to:
    1. Load clinical target data from extracted tables
    2. Run BKPyV simulations with parameter variations
    3. Compare simulation outputs to clinical targets
    4. Optimize parameters to minimize mismatch
    5. Generate calibrated configuration files
    """
    
    def __init__(self, clinical_data_path: Optional[Path] = None):
        """Initialize clinical calibration.
        
        Args:
            clinical_data_path: Path to extracted clinical table data
        """
        self.clinical_data_path = clinical_data_path
        self.clinical_targets = ClinicalTarget()
        self.viral_load_mapper = None
        
        # Import viral load mapper (lazy import to avoid circular dependency)
        try:
            from vcm.clinical.viral_load_mapper import ClinicalViralLoadMapper
            self.viral_load_mapper = ClinicalViralLoadMapper()
        except ImportError:
            print("Warning: ClinicalViralLoadMapper not available, some features disabled")
    
    def load_clinical_data(self, table_file: str) -> Dict[str, any]:
        """Load clinical data from extracted table CSV file.
        
        Args:
            table_file: Name of the table file (e.g., 'irnf_a_2509785_sm5943_table_0.csv')
            
        Returns:
            Dictionary with clinical data
        """
        if self.clinical_data_path is None:
            # Default path
            base_path = Path(__file__).parent.parent.parent / "data" / "research" / "docx" / "extracted_tables"
        else:
            base_path = self.clinical_data_path
        
        table_path = base_path / table_file
        
        if not table_path.exists():
            print(f"Warning: Clinical table {table_file} not found")
            return {}
        
        data = []
        with open(table_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        
        return {'table_name': table_file, 'data': data, 'n_rows': len(data)}
    
    def extract_clinical_targets(self) -> ClinicalTarget:
        """Extract clinical targets from loaded data.
        
        Analyzes the extracted clinical tables to determine:
        - Typical time to first viremia
        - Peak viral load ranges
        - Time to peak timing
        - Clearance patterns
        
        Returns:
            ClinicalTarget with extracted values
        """
        # This would analyze the actual extracted clinical data
        # For now, use literature-based defaults
        
        # Load development cohort data if available
        cohort_data = self.load_clinical_data('irnf_a_2509785_sm5943_table_0.csv')
        
        # Load GcfDNA data if available
        gcfdna_data = self.load_clinical_data('DataSheet_1_table_0.csv')
        
        # Extract relevant statistics from the data
        # This would involve parsing the clinical tables and extracting:
        # - Time to first viremia distributions
        # - Peak viral load statistics
        # - Drug effect comparisons
        # - Risk factor associations
        
        # For now, return literature-based targets
        return ClinicalTarget()
    
    def calculate_objective_function(
        self,
        simulated_trajectory: Dict[str, List[float]],
        clinical_targets: ClinicalTarget,
        weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """Calculate objective function value for parameter calibration.
        
        The objective function measures how well simulated trajectories match
        clinical targets. Lower values indicate better matches.
        
        Args:
            simulated_trajectory: Dictionary with timepoints and viral loads
            clinical_targets: Clinical targets to match
            weights: Optional weights for different targets
            
        Returns:
            Objective function value (lower is better)
        """
        if weights is None:
            weights = {
                'time_to_first_viremia': 1.0,
                'peak_viral_load': 2.0,  # Higher weight for magnitude
                'time_to_peak': 1.0,
                'clearance_rate': 1.5,    # Higher weight for kinetics
            }
        
        timepoints = simulated_trajectory.get('timepoints', [])
        viral_loads = simulated_trajectory.get('plasma_viral_load', [])
        
        if not timepoints or not viral_loads:
            return float('inf')  # Invalid simulation
        
        # Extract clinical features from simulation
        sim_peak = max(viral_loads)
        sim_peak_time = timepoints[viral_loads.index(sim_peak)]
        
        # Find time to first viremia (above screening threshold)
        screening_threshold = 1000.0  # copies/mL
        first_viremia_idx = next(
            (i for i, load in enumerate(viral_loads) if load >= screening_threshold),
            len(viral_loads) - 1
        )
        sim_first_viremia = timepoints[first_viremia_idx]
        
        # Estimate clearance rate from decay phase
        if sim_peak_time < timepoints[-1]:
            decay_start = sim_peak_time
            decay_end = timepoints[-1]
            decay_start_idx = timepoints.index(decay_start)
            decay_end_idx = len(timepoints) - 1
            
            if decay_end_idx > decay_start_idx:
                initial_load = viral_loads[decay_start_idx]
                final_load = viral_loads[decay_end_idx]
                if final_load > 0 and initial_load > final_load:
                    # Simple exponential decay model
                    decay_rate = math.log(initial_load / final_load) / (decay_end - decay_start)
                else:
                    decay_rate = 0.1  # Default
            else:
                decay_rate = 0.1
        else:
            decay_rate = 0.1
        
        # Calculate weighted errors
        errors = []
        
        # Time to first viremia error (normalized by clinical std)
        time_error = abs(sim_first_viremia - clinical_targets.time_to_first_viremia_mean)
        errors.append(weights['time_to_first_viremia'] * (time_error / clinical_targets.time_to_first_viremia_std) ** 2)
        
        # Peak viral load error (normalized by clinical std)
        peak_error = abs(sim_peak - clinical_targets.peak_viral_load_mean)
        errors.append(weights['peak_viral_load'] * (peak_error / clinical_targets.peak_viral_load_std) ** 2)
        
        # Time to peak error (normalized by clinical std)
        peak_time_error = abs(sim_peak_time - clinical_targets.time_to_peak_mean)
        errors.append(weights['time_to_peak'] * (peak_time_error / clinical_targets.time_to_peak_std) ** 2)
        
        # Clearance rate error (normalized by clinical std)
        clearance_error = abs(decay_rate - clinical_targets.clearance_rate_mean)
        errors.append(weights['clearance_rate'] * (clearance_error / clinical_targets.clearance_rate_std) ** 2)
        
        return sum(errors)
    
    def run_calibration(
        self,
        simulation_function: Callable[[Dict[str, float]], Dict[str, List[float]]],
        parameter_ranges: Dict[str, Tuple[float, float]],
        n_iterations: int = 100,
        optimization_method: str = 'grid_search',
    ) -> CalibrationResult:
        """Run parameter calibration optimization.
        
        Args:
            simulation_function: Function that takes parameters and returns trajectory
            parameter_ranges: Dictionary of parameter ranges to explore
            n_iterations: Number of iterations for optimization
            optimization_method: 'grid_search', 'random_search', or 'bayesian'
            
        Returns:
            CalibrationResult with optimal parameters and objective value
        """
        print(f"Starting calibration with {optimization_method} method...")
        
        # Extract clinical targets
        clinical_targets = self.extract_clinical_targets()
        
        if optimization_method == 'grid_search':
            result = self._grid_search_calibration(
                simulation_function, parameter_ranges, clinical_targets, n_iterations
            )
        elif optimization_method == 'random_search':
            result = self._random_search_calibration(
                simulation_function, parameter_ranges, clinical_targets, n_iterations
            )
        elif optimization_method == 'bayesian':
            result = self._bayesian_calibration(
                simulation_function, parameter_ranges, clinical_targets, n_iterations
            )
        else:
            raise ValueError(f"Unknown optimization method: {optimization_method}")
        
        print(f"Calibration completed. Objective value: {result.objective_value:.4f}")
        return result
    
    def _grid_search_calibration(
        self,
        simulation_function: Callable[[Dict[str, float]], Dict[str, List[float]]],
        parameter_ranges: Dict[str, Tuple[float, float]],
        clinical_targets: ClinicalTarget,
        n_iterations: int,
    ) -> CalibrationResult:
        """Grid search calibration."""
        best_objective = float('inf')
        best_params = {}
        
        # Simple grid search (not recommended for high-dimensional parameter spaces)
        param_names = list(parameter_ranges.keys())
        
        # For simplicity, sample from grid rather than full grid
        for _ in range(n_iterations):
            params = {}
            for param_name, (min_val, max_val) in parameter_ranges.items():
                # Random sampling within ranges
                params[param_name] = np.random.uniform(min_val, max_val)
            
            # Run simulation
            try:
                trajectory = simulation_function(params)
                objective = self.calculate_objective_function(trajectory, clinical_targets)
                
                if objective < best_objective:
                    best_objective = objective
                    best_params = params.copy()
            except Exception as e:
                print(f"Simulation failed: {e}")
                continue
        
        # Run final simulation with best parameters
        best_trajectory = simulation_function(best_params)
        
        return CalibrationResult(
            calibrated_params=best_params,
            objective_value=best_objective,
            matched_targets=self._extract_simulation_targets(best_trajectory),
            calibration_metadata={
                'method': 'grid_search',
                'n_iterations': n_iterations,
                'parameter_ranges': parameter_ranges,
            }
        )
    
    def _random_search_calibration(
        self,
        simulation_function: Callable[[Dict[str, float]], Dict[str, List[float]]],
        parameter_ranges: Dict[str, Tuple[float, float]],
        clinical_targets: ClinicalTarget,
        n_iterations: int,
    ) -> CalibrationResult:
        """Random search calibration."""
        best_objective = float('inf')
        best_params = {}
        
        for _ in range(n_iterations):
            params = {}
            for param_name, (min_val, max_val) in parameter_ranges.items():
                params[param_name] = np.random.uniform(min_val, max_val)
            
            try:
                trajectory = simulation_function(params)
                objective = self.calculate_objective_function(trajectory, clinical_targets)
                
                if objective < best_objective:
                    best_objective = objective
                    best_params = params.copy()
            except Exception as e:
                continue
        
        best_trajectory = simulation_function(best_params)
        
        return CalibrationResult(
            calibrated_params=best_params,
            objective_value=best_objective,
            matched_targets=self._extract_simulation_targets(best_trajectory),
            calibration_metadata={
                'method': 'random_search',
                'n_iterations': n_iterations,
                'parameter_ranges': parameter_ranges,
            }
        )
    
    def _bayesian_calibration(
        self,
        simulation_function: Callable[[Dict[str, float]], Dict[str, List[float]]],
        parameter_ranges: Dict[str, Tuple[float, float]],
        clinical_targets: ClinicalTarget,
        n_iterations: int,
    ) -> CalibrationResult:
        """Bayesian optimization calibration (simplified)."""
        # Simplified implementation - in production, use proper Bayesian optimization library
        print("Warning: Bayesian optimization simplified to random search")
        return self._random_search_calibration(
            simulation_function, parameter_ranges, clinical_targets, n_iterations
        )
    
    def _extract_simulation_targets(self, trajectory: Dict[str, List[float]]) -> Dict[str, float]:
        """Extract clinical targets from simulation trajectory."""
        viral_loads = trajectory.get('plasma_viral_load', [])
        timepoints = trajectory.get('timepoints', [])
        
        if not viral_loads or not timepoints:
            return {}
        
        peak_load = max(viral_loads)
        peak_time = timepoints[viral_loads.index(peak_load)]
        
        # Time to first viremia
        screening_threshold = 1000.0
        first_viremia_idx = next(
            (i for i, load in enumerate(viral_loads) if load >= screening_threshold),
            len(viral_loads) - 1
        )
        first_viremia = timepoints[first_viremia_idx]
        
        return {
            'peak_viral_load': peak_load,
            'time_to_peak': peak_time,
            'time_to_first_viremia': first_viremia,
        }
    
    def sensitivity_analysis(
        self,
        simulation_function: Callable[[Dict[str, float]], Dict[str, List[float]]],
        base_params: Dict[str, float],
        parameter_ranges: Dict[str, Tuple[float, float]],
        perturbation_fraction: float = 0.1,
    ) -> Dict[str, float]:
        """Perform sensitivity analysis on parameters.
        
        Args:
            simulation_function: Function to run simulations
            base_params: Base parameter values
            parameter_ranges: Valid parameter ranges
            perturbation_fraction: Fraction to perturb each parameter
            
        Returns:
            Dictionary mapping parameter names to sensitivity scores
        """
        clinical_targets = self.extract_clinical_targets()
        
        # Run baseline simulation
        base_trajectory = simulation_function(base_params)
        base_objective = self.calculate_objective_function(base_trajectory, clinical_targets)
        
        sensitivity_scores = {}
        
        for param_name in base_params:
            # Create perturbed parameters
            perturbed_params = base_params.copy()
            perturbation = base_params[param_name] * perturbation_fraction
            perturbed_params[param_name] += perturbation
            
            # Ensure perturbed value is within valid range
            min_val, max_val = parameter_ranges.get(param_name, (0, float('inf')))
            perturbed_params[param_name] = max(min_val, min(max_val, perturbed_params[param_name]))
            
            # Run perturbed simulation
            perturbed_trajectory = simulation_function(perturbed_params)
            perturbed_objective = self.calculate_objective_function(perturbed_trajectory, clinical_targets)
            
            # Calculate sensitivity (change in objective / change in parameter)
            sensitivity = abs(perturbed_objective - base_objective) / abs(perturbation)
            sensitivity_scores[param_name] = sensitivity
        
        return sensitivity_scores
    
    def generate_calibrated_config(
        self,
        calibration_result: CalibrationResult,
        base_config: Dict[str, any],
        output_path: str,
    ) -> None:
        """Generate calibrated configuration file.
        
        Args:
            calibration_result: Calibration result with optimal parameters
            base_config: Base configuration to update
            output_path: Path to write calibrated config
        """
        import yaml
        
        # Update base config with calibrated parameters
        calibrated_config = base_config.copy()
        
        # Add calibrated parameters to simulator_parameters section
        if 'simulator_parameters' not in calibrated_config:
            calibrated_config['simulator_parameters'] = {}
        
        for param_name, param_value in calibration_result.calibrated_params.items():
            calibrated_config['simulator_parameters'][param_name] = param_value
        
        # Add calibration metadata
        calibrated_config['calibration'] = {
            'objective_value': calibration_result.objective_value,
            'matched_targets': calibration_result.matched_targets,
            'metadata': calibration_result.calibration_metadata,
        }
        
        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            yaml.dump(calibrated_config, f, default_flow_style=False)
        
        print(f"Calibrated config written to {output_path}")


def default_bkpyv_parameter_ranges() -> Dict[str, Tuple[float, float]]:
    """Get default parameter ranges for BKPyV calibration.
    
    Returns:
        Dictionary mapping parameter names to (min, max) ranges
    """
    return {
        'viral_replication_rate': (0.05, 0.2),
        'viral_clearance_rate': (0.05, 0.2),
        't_antigen_replication_threshold': (0.3, 0.7),
        'dna_replication_coupling': (0.5, 1.0),
        'cell_cycle_s_phase_bonus': (1.5, 3.0),
        'tacrolimus_enhancement_factor': (1.5, 2.5),
        'sirolimus_inhibition_factor': (0.3, 0.7),
        'innate_immune_suppression_factor': (0.3, 0.7),
    }


if __name__ == "__main__":
    # Example usage
    calibration = ClinicalCalibration()
    
    print("Clinical Calibration Module")
    print("=" * 80)
    
    # Load clinical data
    print("\nLoading clinical data...")
    clinical_targets = calibration.extract_clinical_targets()
    print(f"Clinical targets: time to first viremia = {clinical_targets.time_to_first_viremia_mean} days")
    print(f"Clinical targets: peak viral load = {clinical_targets.peak_viral_load_mean} copies/mL")
    
    print("\nParameter ranges for calibration:")
    param_ranges = default_bkpyv_parameter_ranges()
    for param_name, (min_val, max_val) in param_ranges.items():
        print(f"  {param_name}: [{min_val}, {max_val}]")
    
    print("\nTo perform actual calibration, provide a simulation function")
    print("that takes parameters and returns a trajectory dictionary.")
    print("See documentation for detailed usage instructions.")