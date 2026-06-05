#!/usr/bin/env python3
"""
Update BKPyV parameters with computationally derived values from GSE75693 microarray data.
Only updates parameters where computed values differ from current values by >10%.
"""

import pandas as pd
import json

# Load computed fold changes
computed_fc = pd.read_csv("data/processed/GSE75693_pathway_fold_changes_COMPUTED.csv")

print("Computed fold changes from GSE75693:")
print(computed_fc[["pathway","fold_change_peaking_vs_control","pvalue","n_probes_found"]])

# Current parameter values from literature calibration
current_values = {
    "cell_cycle_s_phase_bonus": 2.2,  # from JVI single-cell
    "dna_replication_coupling": 0.85,  # from AJT-16-821 + JVI
    "dna_damage_response_enhancement": 1.5,  # from JVI single-cell
    "innate_immune_suppression_factor": 0.4,  # from JVI single-cell (inverted)
    "translation_enhancement_factor": 2.5,  # from JVI single-cell
    "mitochondrial_function_importance": 0.9,  # from JVI single-cell
}

# Map pathways to parameters
pathway_to_param = {
    "cell_cycle": "cell_cycle_s_phase_bonus",
    "dna_replication": "dna_replication_coupling", 
    "dna_damage_response": "dna_damage_response_enhancement",
    "innate_immune": "innate_immune_suppression_factor",
    "translation": "translation_enhancement_factor",
    "cellular_stress": "mitochondrial_function_importance",
}

print("\n\nParameter update analysis:")
print("-" * 70)

updates_needed = []
for _, row in computed_fc.iterrows():
    pathway = row['pathway']
    computed_fc_val = row['fold_change_peaking_vs_control']
    
    if pathway in pathway_to_param:
        param_name = pathway_to_param[pathway]
        current_val = current_values.get(param_name)
        
        if current_val:
            # For immune suppression, computed is an enhancement factor (inverse)
            if param_name == "innate_immune_suppression_factor":
                computed_for_param = 1.0 / computed_fc_val if computed_fc_val > 0 else 1.0
            else:
                computed_for_param = computed_fc_val
            
            pct_diff = abs(computed_for_param - current_val) / current_val * 100
            
            print(f"\n{param_name}:")
            print(f"  Current (literature): {current_val:.3f}")
            print(f"  Computed (GSE75693): {computed_for_param:.3f}")
            print(f"  Difference: {pct_diff:.1f}%")
            print(f"  P-value: {row['pvalue']:.4f}")
            print(f"  Probes: {row['n_probes_found']}")
            
            if pct_diff > 10:
                updates_needed.append({
                    'parameter': param_name,
                    'old_value': current_val,
                    'new_value': computed_for_param,
                    'pct_change': pct_diff,
                    'pvalue': row['pvalue'],
                    'n_probes': row['n_probes_found']
                })
                print(f"  → UPDATE RECOMMENDED (>{pct_diff:.1f}% difference)")
            else:
                print(f"  → KEEP CURRENT (≤10% difference)")

print("\n" + "=" * 70)
if updates_needed:
    print(f"Updates needed: {len(updates_needed)} parameters")
    print("\nRecommended updates:")
    for update in updates_needed:
        print(f"  {update['parameter']}: {update['old_value']:.3f} → {update['new_value']:.3f}")
else:
    print("No parameter updates needed")
    print("Computed fold changes are within 10% of current literature-derived values")
    print("Keeping literature values as they may reflect different experimental conditions")

print("\n" + "=" * 70)
print("Analysis complete")
