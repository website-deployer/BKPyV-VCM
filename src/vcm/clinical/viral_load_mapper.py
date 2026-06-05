"""Clinical Viral Load Mapper for BKPyV Plugin.

This module provides the mapping between virtual cell viral load (0-1 scale) 
and clinical plasma viral load (copies/mL) to bridge simulations to real-world 
clinical decision-making.

Research Grounding:
- Clinical guidelines: BK viremia thresholds ≥1,000 and ≥10,000 copies/mL
- Source: Favi et al. 2019 (PMC6369392), UK BTS Guidelines
- Hill function fitted to clinical anchor points

Reference Sources:
- Favi et al. 2019. PMCID: PMC6369392
- UK BTS Guidelines for BKV nephropathy monitoring
"""

import json
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from pathlib import Path
from typing import Optional, Dict, List
import sys


def hill_function(vl, Vmax, K, n):
    """Hill equation: copies_per_mL = Vmax * (vl^n) / (K^n + vl^n)
    
    Args:
        vl: Normalized viral load (0-1)
        Vmax: Maximum viral load (copies/mL)
        K: Half-saturation constant
        n: Hill coefficient (cooperativity)
        
    Returns:
        copies_per_mL: Clinical viral load in copies/mL
    """
    return Vmax * (vl**n) / (K**n + vl**n)


def fit_hill_parameters():
    """Fit Hill function parameters to clinical anchor points.
    
    Anchor points:
    - viral_load = 0.0  → copies/mL ≈ 0
    - viral_load = 0.3  → copies/mL = 1,000  (screening threshold)
    - viral_load = 0.6  → copies/mL = 10,000 (treatment threshold)
    - viral_load = 1.0  → copies/mL = 10^7   (severe nephropathy range)
    
    Uses bounded optimization to ensure reasonable Hill coefficient (n) 
    for smoother clinical transitions.
    
    Returns:
        dict: Fitted parameters (Vmax, K, n)
    """
    # Anchor points for fitting
    vl_values = np.array([0.3, 0.6, 1.0])
    copies_values = np.array([1000, 10000, 1e7])
    
    # Fix Vmax to 1e7 (severe nephropathy range)
    Vmax_fixed = 1e7
    
    # Fit n and K given Vmax
    def hill_fixed_vmax(vl, K, n):
        return hill_function(vl, Vmax_fixed, K, n)
    
    # Initial guesses: K=0.5, n=2 (more reasonable than steep hill)
    p0 = [0.5, 2.0]
    
    # Add bounds to prevent unrealistic steepness
    # K between 0.1 and 0.9, n between 1 and 5
    bounds = ([0.1, 1.0], [0.9, 5.0])
    
    # Fit parameters with bounds
    popt, pcov = curve_fit(hill_fixed_vmax, vl_values, copies_values, p0=p0, bounds=bounds, maxfev=10000)
    
    K_fit, n_fit = popt
    K_std, n_std = np.sqrt(np.diag(pcov))
    
    params = {
        'Vmax': Vmax_fixed,
        'K': float(K_fit),
        'n': float(n_fit),
        'K_std': float(K_std),
        'n_std': float(n_std),
        'source': 'Favi et al. 2019 (PMC6369392), UK BTS Guidelines',
        'fit_method': 'Bounded curve_fit (n: 1-5, K: 0.1-0.9) for smooth clinical transitions',
        'anchor_points': [
            {'viral_load': 0.0, 'copies_per_ml': 0, 'description': 'No infection'},
            {'viral_load': 0.3, 'copies_per_ml': 1000, 'description': 'Screening threshold'},
            {'viral_load': 0.6, 'copies_per_ml': 10000, 'description': 'Treatment threshold'},
            {'viral_load': 1.0, 'copies_per_ml': 1e7, 'description': 'Severe nephropathy'}
        ]
    }
    
    # Verify fit quality
    predicted = hill_function(vl_values, Vmax_fixed, K_fit, n_fit)
    fit_quality = {
        'predicted_values': predicted.tolist(),
        'actual_values': copies_values.tolist(),
        'percent_error': np.abs((predicted - copies_values) / copies_values * 100).tolist()
    }
    params['fit_quality'] = fit_quality
    
    return params


def save_hill_parameters(params: Dict, output_path: str):
    """Save fitted Hill function parameters to JSON.
    
    Args:
        params: Fitted parameters dictionary
        output_path: Path to save JSON file
    """
    with open(output_path, 'w') as f:
        json.dump(params, f, indent=2)


class ViralLoadMapper:
    """Mapper for converting simulator viral_load (0-1) to clinical plasma copies/mL.
    
    Uses a Hill function fitted to clinical anchor points to map normalized
    viral load from the BKPyV simulator to clinically relevant plasma viral load
    values in copies/mL.
    """
    
    CLINICAL_THRESHOLDS = {
        'screening': 1000.0,    # copies/mL - screening threshold
        'treatment': 10000.0,    # copies/mL - treatment threshold
        'severe': 1e7            # copies/mL - severe nephropathy
    }
    
    def __init__(self, params_path: Optional[str] = None):
        """Initialize ViralLoadMapper.
        
        Args:
            params_path: Path to JSON file with Hill parameters. If None,
                        will attempt to load from default location or fit new parameters.
        """
        if params_path is None:
            params_path = "data/processed/viral_load_mapper_params.json"
        
        # Try to load existing parameters
        if Path(params_path).exists():
            with open(params_path, 'r') as f:
                self.params = json.load(f)
        else:
            # Fit new parameters
            print("Fitting Hill function parameters...")
            self.params = fit_hill_parameters()
            # Save parameters
            Path(params_path).parent.mkdir(parents=True, exist_ok=True)
            save_hill_parameters(self.params, params_path)
            print(f"Saved parameters to {params_path}")
        
        self.Vmax = self.params['Vmax']
        self.K = self.params['K']
        self.n = self.params['n']
    
    def normalized_to_copies(self, viral_load: float) -> float:
        """Convert simulator viral_load (0-1) to copies/mL.
        
        Args:
            viral_load: Normalized viral load from simulator (0.0-1.0)
            
        Returns:
            copies_per_mL: Clinical viral load in copies/mL
        """
        viral_load = max(0.0, min(1.0, viral_load))
        return hill_function(viral_load, self.Vmax, self.K, self.n)
    
    def copies_to_risk_category(self, copies_per_ml: float) -> str:
        """Return risk category based on clinical viral load.
        
        Args:
            copies_per_ml: Plasma viral load in copies/mL
            
        Returns:
            risk_category: One of 'undetectable', 'low_risk', 'screening', 
                          'treatment', 'severe'
        """
        if copies_per_ml < 100:  # Detection limit
            return 'undetectable'
        elif copies_per_ml < self.CLINICAL_THRESHOLDS['screening']:
            return 'low_risk'
        elif copies_per_ml < self.CLINICAL_THRESHOLDS['treatment']:
            return 'screening'
        elif copies_per_ml < self.CLINICAL_THRESHOLDS['severe']:
            return 'treatment'
        else:
            return 'severe'
    
    def simulate_clinical_trajectory(
        self,
        scenario: str,
        weeks: int = 52
    ) -> pd.DataFrame:
        """Run simulation using BKPyVSimulator and return weekly copies/mL trajectory.
        
        This method now actually uses the BKPyVSimulator to generate viral load dynamics,
        then converts the simulator output to clinical copies/mL using the Hill function.
        This fixes the critical architecture flaw where the mapper used internal trajectory math.
        
        Args:
            scenario: One of 'baseline', 'infection', 'tacrolimus', 'sirolimus'
            weeks: Number of weeks to simulate (default: 52)
            
        Returns:
            DataFrame with columns: week, viral_load_norm, copies_per_ml, 
                                 risk_category, drug_scenario
        """
        # Import simulator components
        from vcm.plugins.transplant.bk_polyomavirus.bk_polyomavirus import BKPolyomavirusPlugin
        from vcm.simulators.bkpyv_simulator import BKPyVSimulator
        from vcm.core.models import CellState, Environment, Perturbation, PerturbationType
        
        # Create plugin and simulator
        plugin = BKPolyomavirusPlugin()
        initial_state = plugin.create_initial_state()
        environment = Environment()
        
        # Set up simulator config based on scenario
        valid_scenarios = ['baseline', 'infection', 'tacrolimus', 'sirolimus']
        if scenario not in valid_scenarios:
            raise ValueError(f"Invalid scenario: {scenario}. Must be one of {valid_scenarios}")
        
        config = {}
        if scenario == 'tacrolimus':
            config['tacrolimus_enhancement_factor'] = 1.8
        elif scenario == 'sirolimus':
            config['mtor_inhibition_factor'] = 0.5
        else:
            config = {}  # Use default for baseline and infection
        
        simulator = BKPyVSimulator(config)
        
        # Set up perturbations based on scenario
        perturbations = []
        if scenario in ['infection', 'tacrolimus', 'sirolimus']:
            # Add infection perturbation
            perturbations.append(Perturbation(
                id='bkpyv_infection',
                name='BKPyV infection',
                perturbation_type=PerturbationType.VIRAL_INFECTION,
                target_id='viral_entry',
                magnitude=1.0,
                timing=504,  # 3 weeks = 504 hours
                duration=None
            ))
        
        # Add drug perturbations for drug scenarios
        if scenario == 'tacrolimus':
            # Tacrolimus: calcineurin inhibitor, starts at transplant (time 0)
            perturbations.append(Perturbation(
                id='tacrolimus_treatment',
                name='Tacrolimus treatment',
                perturbation_type=PerturbationType.DRUG_TREATMENT,
                target_id='FKBP1A',
                magnitude=1.0,
                timing=0.0,  # Start at transplant
                duration=None
            ))
        elif scenario == 'sirolimus':
            # Sirolimus: mTOR inhibitor, starts at transplant (time 0)
            perturbations.append(Perturbation(
                id='sirolimus_treatment',
                name='Sirolimus treatment',
                perturbation_type=PerturbationType.DRUG_TREATMENT,
                target_id='MTOR',
                magnitude=1.0,
                timing=0.0,  # Start at transplant
                duration=None
            ))
        
        # Calculate simulation parameters
        total_hours = weeks * 168  # hours per week
        n_steps = int(total_hours)  # 1-hour timestep
        timestep = 1.0
        
        # Infection timing: 3 weeks post-transplant = 504 hours
        # Make sure simulation runs long enough for infection to occur
        infection_timing = 504
        if total_hours <= infection_timing:
            # Extend simulation to at least 1 week after infection
            total_hours = infection_timing + 168
            n_steps = int(total_hours)
        
        # Run simulation
        result = simulator.simulate(
            initial_state=initial_state,
            perturbations=perturbations,
            environment=environment,
            n_steps=n_steps,
            timestep=timestep
        )
        
        # Extract viral load from simulation steps
        viral_loads = []
        for step in result.steps:
            viral_load = step.cell_state.viral_load
            viral_loads.append(viral_load)
        
        # Interpolate to weekly resolution
        weekly_indices = np.linspace(0, len(viral_loads)-1, weeks+1, dtype=int)
        weekly_viral_loads = [viral_loads[i] for i in weekly_indices]
        
        # Convert to clinical copies/mL using Hill function
        weekly_copies = []
        for vl in weekly_viral_loads:
            copies = self.normalized_to_copies(vl)
            weekly_copies.append(copies)
        
        # Build results DataFrame
        results = []
        for week, (vl_norm, copies) in enumerate(zip(weekly_viral_loads, weekly_copies)):
            risk_category = self.copies_to_risk_category(copies)
            results.append({
                'week': week,
                'viral_load_norm': vl_norm,
                'copies_per_ml': copies,
                'risk_category': risk_category,
                'drug_scenario': scenario
            })
        
        return pd.DataFrame(results)


def generate_clinical_summary(trajectories: Dict[str, pd.DataFrame]) -> Dict:
    """Generate clinical summary statistics for each scenario.
    
    Args:
        trajectories: Dict mapping scenario names to DataFrames
        
    Returns:
        Dict with summary statistics for each scenario
    """
    summary = {}
    
    for scenario, df in trajectories.items():
        # Time to first detectable viremia (weeks post-transplant)
        detectable = df[df['copies_per_ml'] >= 100]
        if len(detectable) > 0:
            time_to_detectable = int(detectable['week'].min())
        else:
            time_to_detectable = None
        
        # Peak viral load (copies/mL)
        peak_viral_load = float(df['copies_per_ml'].max())
        
        # Week of peak
        week_of_peak = int(df.loc[df['copies_per_ml'].idxmax(), 'week'])
        
        # Time above screening threshold (weeks)
        above_screening = df[df['copies_per_ml'] >= 1000]
        time_above_screening = int(len(above_screening))
        
        # Time above treatment threshold (weeks)
        above_treatment = df[df['copies_per_ml'] >= 10000]
        time_above_treatment = int(len(above_treatment))
        
        # Final viral load at week 52
        final_viral_load = float(df[df['week'] == 52]['copies_per_ml'].values[0] if len(df[df['week'] == 52]) > 0 else df['copies_per_ml'].iloc[-1])
        
        summary[scenario] = {
            'time_to_first_detectable_viremia_weeks': time_to_detectable,
            'peak_viral_load_copies_per_ml': peak_viral_load,
            'week_of_peak': week_of_peak,
            'time_above_screening_threshold_weeks': time_above_screening,
            'time_above_treatment_threshold_weeks': time_above_treatment,
            'final_viral_load_week_52_copies_per_ml': final_viral_load
        }
    
    return summary
