#!/usr/bin/env python3
"""
Save risk prediction results to JSON.

This script trains both models and saves the comprehensive results to
outputs/clinical/risk_prediction_results.json as specified in the requirements.
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vcm.clinical.risk_prediction import RiskPredictor


def main():
    """Main function to train models and save results."""
    print("Training risk prediction models and saving results...")
    
    # Create output directory
    output_dir = Path("outputs/clinical")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load synthetic cohort data
    cohort_path = Path("data/processed/synthetic_patient_cohort.csv")
    df = pd.read_csv(cohort_path)
    print(f"Loaded cohort data: {df.shape}")
    
    # Initialize risk predictor
    predictor = RiskPredictor(random_state=42)
    
    # Train baseline model
    print("Training baseline clinical model...")
    baseline_results = predictor.train_clinical_baseline(df)
    
    # Train VCM-enhanced model
    print("Training VCM-enhanced model...")
    vcm_results = predictor.train_vcm_enhanced(df)
    
    # Compare models
    print("Comparing models...")
    comparison = predictor.compare_models(baseline_results, vcm_results)
    
    # Calculate summary statistics
    n_patients = len(df)
    prevalence = df['bkypan_outcome'].mean()
    n_features_clinical = len(predictor.clinical_features)
    n_features_vcm_added = len(predictor.vcm_features)
    
    # Compile results dictionary
    results = {
        'baseline_auc_mean': float(baseline_results['auc_mean']),
        'baseline_auc_std': float(baseline_results['auc_std']),
        'vcm_auc_mean': float(vcm_results['auc_mean']),
        'vcm_auc_std': float(vcm_results['auc_std']),
        'auc_improvement': float(comparison['auc_improvement']),
        'baseline_brier': float(baseline_results['brier_score']),
        'vcm_brier': float(vcm_results['brier_score']),
        'feature_importances': {k: float(v) for k, v in vcm_results['feature_importances'].items()},
        'n_patients': int(n_patients),
        'prevalence': float(prevalence),
        'n_features_clinical': int(n_features_clinical),
        'n_features_vcm_added': int(n_features_vcm_added),
        'comparison_metrics': {
            'delong_p_value': float(comparison['delong_p_value']),
            'nri': float(comparison['nri']),
            'interpretation': comparison['interpretation']
        },
        'honest_assessment': comparison['interpretation']
    }
    
    # Save results to JSON
    results_path = output_dir / "risk_prediction_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {results_path}")
    print(f"\nSummary:")
    print(f"  Patients: {n_patients}")
    print(f"  Prevalence: {prevalence:.1%}")
    print(f"  Baseline AUC: {baseline_results['auc_mean']:.3f} ± {baseline_results['auc_std']:.3f}")
    print(f"  VCM-enhanced AUC: {vcm_results['auc_mean']:.3f} ± {vcm_results['auc_std']:.3f}")
    print(f"  AUC improvement: {comparison['auc_improvement']:.3f}")
    print(f"\n{comparison['interpretation']}")


if __name__ == "__main__":
    main()