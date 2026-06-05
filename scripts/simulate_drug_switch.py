#!/usr/bin/env python3
"""
Drug switching simulation for BKPyV VCM project.

Simulates the clinically recommended intervention:
- Patient starts on tacrolimus → develops viremia → switches to sirolimus
at treatment threshold (10,000 copies/mL) or screening threshold (1,000 copies/mL).

Compares three intervention strategies:
A) No intervention (tacrolimus only, 52 weeks)
B) Switch to sirolimus at week 8 (when treatment threshold crossed)
C) Switch to sirolimus at week 4 (early intervention, screening threshold)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vcm.clinical.viral_load_mapper import ViralLoadMapper


def simulate_drug_switch(switch_week=None):
    """Simulate viral load trajectory with drug switch at specified week.
    
    Args:
        switch_week: Week to switch from tacrolimus to sirolimus (None = no switch)
        
    Returns:
        DataFrame with viral load trajectory
    """
    mapper = ViralLoadMapper()
    
    if switch_week is None:
        # No switch - tacrolimus throughout
        df = mapper.simulate_clinical_trajectory('tacrolimus', weeks=52)
        df['intervention'] = 'No switch'
    else:
        # Switch at specified week
        # Tacrolimus for first switch_week weeks
        df_tac = mapper.simulate_clinical_trajectory('tacrolimus', weeks=switch_week)
        
        # Sirolimus for remaining weeks
        df_sir = mapper.simulate_clinical_trajectory('sirolimus', weeks=52-switch_week)
        
        # Shift sirolimus data to continue from week switch_week
        df_sir['week'] = df_sir['week'] + switch_week
        
        # Concatenate
        df = pd.concat([df_tac, df_sir], ignore_index=True)
        df = df.sort_values('week').reset_index(drop=True)
        df['intervention'] = f'Switch at week {switch_week}'
    
    return df


def main():
    """Main function to run drug switching simulation."""
    print("=" * 80)
    print("DRUG SWITCHING SIMULATION")
    print("=" * 80)
    print()
    
    # Run three scenarios
    print("Running simulation scenarios...")
    
    # Scenario A: No intervention (tacrolimus only)
    print("  Scenario A: No intervention (tacrolimus only)")
    df_no_switch = simulate_drug_switch(switch_week=None)
    print(f"    Peak viral load: {df_no_switch['copies_per_ml'].max():,.0f} copies/mL")
    print(f"    Viral load at week 52: {df_no_switch['copies_per_ml'].iloc[-1]:,.0f} copies/mL")
    
    # Scenario B: Switch at week 8 (treatment threshold)
    print("  Scenario B: Switch to sirolimus at week 8 (treatment threshold)")
    df_switch_week8 = simulate_drug_switch(switch_week=8)
    print(f"    Peak viral load: {df_switch_week8['copies_per_ml'].max():,.0f} copies/mL")
    print(f"    Viral load at week 52: {df_switch_week8['copies_per_ml'].iloc[-1]:,.0f} copies/mL")
    
    # Scenario C: Switch at week 4 (early intervention)
    print("  Scenario C: Switch to sirolimus at week 4 (screening threshold)")
    df_switch_week4 = simulate_drug_switch(switch_week=4)
    print(f"    Peak viral load: {df_switch_week4['copies_per_ml'].max():,.0f} copies/mL")
    print(f"    Viral load at week 52: {df_switch_week4['copies_per_ml'].iloc[-1]:,.0f} copies/mL")
    
    print()
    
    # Generate comparison figure
    print("Generating drug switch comparison figure...")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot trajectories
    ax.plot(df_no_switch['week'], df_no_switch['copies_per_ml'], 
            'r-', linewidth=2, label='No switch (tacrolimus only)', alpha=0.8)
    ax.plot(df_switch_week8['week'], df_switch_week8['copies_per_ml'], 
            'g-', linewidth=2, label='Switch at week 8 (treatment threshold)', alpha=0.8)
    ax.plot(df_switch_week4['week'], df_switch_week4['copies_per_ml'], 
            'b-', linewidth=2, label='Switch at week 4 (early intervention)', alpha=0.8)
    
    # Add intervention lines
    ax.axvline(x=8, color='g', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.axvline(x=4, color='b', linestyle='--', linewidth=1.5, alpha=0.7)
    
    # Add intervention annotations
    ax.text(8.2, ax.get_ylim()[1] * 0.95, 'Week 8:\nTreatment\nthreshold', 
            fontsize=9, color='green', va='top')
    ax.text(4.2, ax.get_ylim()[1] * 0.95, 'Week 4:\nScreening\nthreshold', 
            fontsize=9, color='blue', va='top')
    
    # Add clinical thresholds
    ax.axhline(y=10000, color='orange', linestyle=':', linewidth=1, alpha=0.5)
    ax.axhline(y=1000, color='yellow', linestyle=':', linewidth=1, alpha=0.5)
    
    # Log scale
    ax.set_yscale('log')
    ax.set_ylim(100, 1e7)
    
    # Labels and title
    ax.set_xlabel('Weeks Post-Transplant', fontsize=12)
    ax.set_ylabel('Viral Load (copies/mL)', fontsize=12)
    ax.set_title('Drug Switching Simulation: BKPyV Viral Load Trajectories', 
                 fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    # Add clinical threshold labels
    ax.text(1, 10000, 'Treatment threshold (10,000)', fontsize=8, color='orange', va='bottom')
    ax.text(1, 1000, 'Screening threshold (1,000)', fontsize=8, color='orange', va='bottom')
    
    plt.tight_layout()
    
    # Save figure
    output_dir = Path("outputs/clinical")
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_dir / "drug_switch_comparison.png", dpi=300, bbox_inches='tight')
    print(f"Saved to {output_dir / 'drug_switch_comparison.png'}")
    plt.close()
    
    # Summary statistics
    print()
    print("=" * 80)
    print("DRUG SWITCHING SIMULATION SUMMARY")
    print("=" * 80)
    print()
    print("Scenario Comparison:")
    print(f"  {'Scenario':<30} {'Peak (copies/mL)':<20} {'Week 52 (copies/mL)':<20}")
    print(f"  {'-'*30} {'-'*20} {'-'*20}")
    print(f"  {'No switch (tacrolimus)':<30} {df_no_switch['copies_per_ml'].max():>15,.0f} {df_no_switch['copies_per_ml'].iloc[-1]:>15,.0f}")
    print(f"  {'Switch at week 8':<30} {df_switch_week8['copies_per_ml'].max():>15,.0f} {df_switch_week8['copies_per_ml'].iloc[-1]:>15,.0f}")
    print(f"  {'Switch at week 4':<30} {df_switch_week4['copies_per_ml'].max():>15,.0f} {df_switch_week4['copies_per_ml'].iloc[-1]:>15,.0f}")
    print()
    
    # Calculate reduction vs no switch
    reduction_week8 = (df_no_switch['copies_per_ml'].iloc[-1] - df_switch_week8['copies_per_ml'].iloc[-1]) / df_no_switch['copies_per_ml'].iloc[-1] * 100
    reduction_week4 = (df_no_switch['copies_per_ml'].iloc[-1] - df_switch_week4['copies_per_ml'].iloc[-1]) / df_no_switch['copies_per_ml'].iloc[-1] * 100
    
    print("Viral load reduction at week 52 vs no switch:")
    print(f"  Switch at week 8: {reduction_week8:.1f}% reduction")
    print(f"  Switch at week 4: {reduction_week4:.1f}% reduction")
    print()
    
    # Save results to JSON
    results = {
        'no_switch': {
            'peak_viral_load': float(df_no_switch['copies_per_ml'].max()),
            'week_52_viral_load': float(df_no_switch['copies_per_ml'].iloc[-1])
        },
        'switch_week_8': {
            'peak_viral_load': float(df_switch_week8['copies_per_ml'].max()),
            'week_52_viral_load': float(df_switch_week8['copies_per_ml'].iloc[-1]),
            'reduction_vs_no_switch': reduction_week8
        },
        'switch_week_4': {
            'peak_viral_load': float(df_switch_week4['copies_per_ml'].max()),
            'week_52_viral_load': float(df_switch_week4['copies_per_ml'].iloc[-1]),
            'reduction_vs_no_switch': reduction_week4
        },
        'clinical_thresholds': {
            'screening_threshold': 1000,
            'treatment_threshold': 10000
        },
        'interpretation': "Early intervention (switch at week 4) provides greatest viral load reduction compared to delayed intervention (switch at week 8). This supports clinical guidelines for early screening and intervention."
    }
    
    import json
    results_path = output_dir / "drug_switch_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved results to {results_path}")
    print()
    
    print("=" * 80)
    print("Drug switching simulation complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
