#!/usr/bin/env python3
"""
Generate synthetic training dataset for BKPyVAN risk prediction.

Creates a cohort of 500 simulated patients with:
- Clinical covariates (from Fang et al. 2022 risk factors, PMC9428263)
- VCM simulation features (run actual simulator for each patient)
- Outcome: BKPyVAN within 1 year using logistic model with literature-based ORs
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vcm.clinical.viral_load_mapper import ViralLoadMapper


def generate_clinical_covariates(n_patients=500, random_state=42):
    """Generate clinical covariates based on Fang et al. 2022.
    
    Args:
        n_patients: Number of patients to generate
        random_state: Random seed for reproducibility
        
    Returns:
        DataFrame with clinical covariates
    """
    np.random.seed(random_state)
    
    data = {
        # Age: random, mean=45, std=12
        'age': np.random.normal(45, 12, n_patients),
        
        # Sex: binary (0=female, 1=male), 60% male
        'sex': np.random.binomial(1, 0.60, n_patients),
        
        # Prior transplant: binary, 20% prevalence
        'prior_transplant': np.random.binomial(1, 0.20, n_patients),
        
        # Diabetes: binary, 25% prevalence
        'diabetes': np.random.binomial(1, 0.25, n_patients),
        
        # Tacrolimus use: binary, 75% prevalence (vs sirolimus/other)
        'tacrolimus_use': np.random.binomial(1, 0.75, n_patients),
        
        # HLA mismatch: integer 0-6, mean=3.2
        'hla_mismatch': np.random.normal(3.2, 1.5, n_patients).clip(0, 6).astype(int),
        
        # Donor age: random, mean=42, std=15
        'donor_age': np.random.normal(42, 15, n_patients)
    }
    
    # Ensure age is positive and reasonable
    data['age'] = data['age'].clip(18, 80)
    data['donor_age'] = data['donor_age'].clip(10, 75)
    
    return pd.DataFrame(data)


def run_vcm_simulation_for_patient(covariates, mapper):
    """Run VCM simulation for a single patient and extract features.
    
    Args:
        covariates: Dict with clinical covariates for one patient
        mapper: ViralLoadMapper instance
        
    Returns:
        Dict with VCM features
    """
    # Determine scenario based on tacrolimus_use
    if covariates['tacrolimus_use'] == 1:
        scenario = 'tacrolimus'
    else:
        # Assume sirolimus or other (use sirolimus as proxy)
        scenario = 'sirolimus'
    
    # Run 52-week simulation
    df = mapper.simulate_clinical_trajectory(scenario, weeks=52)
    
    # Extract features
    peak_viral_load_copies = df['copies_per_ml'].max()
    weeks_above_1k = len(df[df['copies_per_ml'] >= 1000])
    weeks_above_10k = len(df[df['copies_per_ml'] >= 10000])
    
    # Area under curve (log scale)
    # Approximate using trapezoidal rule
    log_viral_loads = np.log10(df['copies_per_ml'] + 1)  # +1 to avoid log(0)
    weeks = df['week'].values
    area_under_curve_log = np.trapz(log_viral_loads, weeks)
    
    # Time to peak (weeks)
    peak_idx = df['copies_per_ml'].idxmax()
    time_to_peak_weeks = df.loc[peak_idx, 'week']
    
    return {
        'peak_viral_load_copies': peak_viral_load_copies,
        'weeks_above_1k': weeks_above_1k,
        'weeks_above_10k': weeks_above_10k,
        'area_under_curve_log': area_under_curve_log,
        'time_to_peak_weeks': time_to_peak_weeks
    }


def generate_outcomes(df):
    """Generate BKPyVAN outcome using logistic model with literature-based ORs.
    
    Risk factors and ORs from Fang et al. 2022 (PMC9428263):
    - tacrolimus use: OR ~2.3
    - prior transplant: OR ~2.1
    - male sex: OR ~1.6
    - higher peak viral load (log): OR > 1 (to be derived from VCM features)
    
    Target prevalence: ~15% BKPyVAN (realistic)
    
    Args:
        df: DataFrame with clinical and VCM features
        
    Returns:
        Series with outcomes (1=BKPyVAN, 0=no BKPyVAN)
    """
    np.random.seed(42)  # For reproducible noise
    
    # Logistic model coefficients (log(OR))
    # Adjust intercept to achieve ~15% prevalence
    # Current achieved prevalence is 9.8%, need slightly less negative intercept
    intercept = -6.3  # Adjusted to achieve ~15% prevalence
    
    # Coefficients from literature ORs (all positive, as higher value = higher risk)
    # Sex encoding: 0=female, 1=male → higher sex (male) should increase risk
    coef_tacrolimus = np.log(2.3)  # OR 2.3
    coef_prior_transplant = np.log(2.1)  # OR 2.1
    coef_male = np.log(1.6)  # OR 1.6 for male sex
    
    # Clinical features with smaller effects
    coef_age = 0.01  # Slight increase with age
    coef_diabetes = np.log(1.3)  # OR ~1.3 for diabetes
    coef_hla_mismatch = 0.1  # Per additional mismatch
    
    # VCM feature coefficient
    # Higher peak viral load increases risk
    coef_peak_viral_log = 0.5  # Moderate effect from VCM features
    
    # Calculate linear predictor (all coefficients positive → higher value = higher risk)
    X = intercept + \
        coef_age * (df['age'] - 45) / 12 + \
        coef_male * df['sex'] + \
        coef_prior_transplant * df['prior_transplant'] + \
        coef_diabetes * df['diabetes'] + \
        coef_tacrolimus * df['tacrolimus_use'] + \
        coef_hla_mismatch * (df['hla_mismatch'] - 3.2) / 1.5 + \
        coef_peak_viral_log * np.log10(df['peak_viral_load_copies'] + 1)
    
    # Convert to probability
    prob = 1 / (1 + np.exp(-X))
    
    # Add random noise for realism
    noise = np.random.normal(0, 0.1, len(df))
    prob = prob + noise
    prob = np.clip(prob, 0.01, 0.99)
    
    # Generate binary outcome
    outcomes = np.random.binomial(1, prob)
    
    return pd.Series(outcomes, index=df.index)


def main():
    """Main function to generate synthetic patient cohort."""
    print("Generating synthetic patient cohort for BKPyVAN risk prediction...")
    
    # Create output directory
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate clinical covariates
    print("Generating clinical covariates (n=500)...")
    df = generate_clinical_covariates(n_patients=500, random_state=42)
    
    # Initialize ViralLoadMapper
    print("Initializing ViralLoadMapper...")
    mapper = ViralLoadMapper()
    
    # Run VCM simulation for each patient
    print("Running VCM simulations for each patient...")
    vcm_features = []
    
    for idx, row in df.iterrows():
        if idx % 50 == 0:
            print(f"  Progress: {idx}/500")
        
        vcm_features.append(run_vcm_simulation_for_patient(row.to_dict(), mapper))
    
    # Add VCM features to DataFrame
    vcm_df = pd.DataFrame(vcm_features)
    df = pd.concat([df, vcm_df], axis=1)
    
    # Generate outcomes
    print("Generating BKPyVAN outcomes using logistic model...")
    df['bkypan_outcome'] = generate_outcomes(df)
    
    # Calculate prevalence
    prevalence = df['bkypan_outcome'].mean()
    print(f"Prevalence: {prevalence:.2%}")
    
    # Save cohort data
    cohort_path = output_dir / "synthetic_patient_cohort.csv"
    df.to_csv(cohort_path, index=False)
    print(f"Saved cohort data to {cohort_path}")
    
    # Save generation parameters
    params = {
        'n_patients': 500,
        'random_state': 42,
        'clinical_covariates': {
            'age': {'mean': 45, 'std': 12, 'source': 'Fang et al. 2022, PMC9428263'},
            'sex': {'male_prevalence': 0.60, 'source': 'Fang et al. 2022, PMC9428263'},
            'prior_transplant': {'prevalence': 0.20, 'source': 'Fang et al. 2022, PMC9428263'},
            'diabetes': {'prevalence': 0.25, 'source': 'Fang et al. 2022, PMC9428263'},
            'tacrolimus_use': {'prevalence': 0.75, 'source': 'Fang et al. 2022, PMC9428263'},
            'hla_mismatch': {'mean': 3.2, 'std': 1.5, 'source': 'Fang et al. 2022, PMC9428263'},
            'donor_age': {'mean': 42, 'std': 15, 'source': 'Fang et al. 2022, PMC9428263'}
        },
        'vcm_simulation': {
            'mapper': 'ViralLoadMapper with bounded Hill function',
            'scenario_mapping': {
                'tacrolimus_use=1': 'tacrolimus scenario',
                'tacrolimus_use=0': 'sirolimus scenario (proxy)'
            },
            'features_extracted': [
                'peak_viral_load_copies',
                'weeks_above_1k', 
                'weeks_above_10k',
                'area_under_curve_log',
                'time_to_peak_weeks'
            ]
        },
        'outcome_model': {
            'type': 'logistic regression',
            'intercept': -7.5,
            'coefficients': {
                'age_standardized': 0.01,
                'sex': np.log(1.6),  # male=1 increases risk
                'prior_transplant': np.log(2.1),
                'diabetes': np.log(1.3),
                'tacrolimus_use': np.log(2.3),
                'hla_mismatch_standardized': 0.1,
                'peak_viral_load_copies_log': 0.5
            },
            'source_or_values': {
                'tacrolimus_use': {'OR': 2.3, 'source': 'Fang et al. 2022, PMC9428263'},
                'prior_transplant': {'OR': 2.1, 'source': 'Fang et al. 2022, PMC9428263'},
                'sex': {'OR': 1.6, 'source': 'Fang et al. 2022, PMC9428263'},
                'diabetes': {'OR': 1.3, 'source': 'Fang et al. 2022, PMC9428263'},
                'peak_viral_load_copies_log': {'OR': 'derived from VCM features', 'note': 'Higher peak increases risk'},
                'age_standardized': {'note': 'Standardized age, slight risk increase'},
                'hla_mismatch_standardized': {'note': 'Standardized HLA mismatch, slight risk increase'}
            },
            'target_prevalence': 0.15,
            'achieved_prevalence': float(prevalence)
        }
    }
    
    params_path = output_dir / "cohort_generation_params.json"
    with open(params_path, 'w') as f:
        json.dump(params, f, indent=2)
    print(f"Saved generation parameters to {params_path}")
    
    print("\nDataset summary:")
    print(f"  Total patients: {len(df)}")
    print(f"  BKPyVAN cases: {df['bkypan_outcome'].sum()}")
    print(f"  Prevalence: {prevalence:.2%}")
    print(f"  Clinical features: 7")
    print(f"  VCM features: 5")
    print(f"  Total features: 12")
    
    print("\nVCM feature statistics:")
    print(df[['peak_viral_load_copies', 'weeks_above_1k', 'weeks_above_10k', 
              'area_under_curve_log', 'time_to_peak_weeks']].describe())
    
    print("\nSynthetic cohort generation complete!")


if __name__ == "__main__":
    main()
