#!/usr/bin/env python3
"""
Compute pathway scores from GSE75693 RMA-normalized Affymetrix microarray data.
This replaces literature-derived values with actual computed fold changes from experimental data.
"""

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

# Load R-processed data
print("Loading GSE75693 RMA-normalized data...")
expr = pd.read_csv("data/processed/GSE75693_normalized_R.csv", index_col=0)
print(f"Expression matrix: {expr.shape[0]} probes x {expr.shape[1]} samples")

# Load probe-to-gene mapping from R
print("Loading probe-to-gene mapping...")
probe_gene_map = pd.read_csv("data/processed/probe_gene_mapping.csv")
print(f"Probe mapping: {probe_gene_map.shape[0]} probes")

# Remove probes without gene symbols
probe_gene_map = probe_gene_map.dropna(subset=['gene_symbol'])
print(f"Probes with gene symbols: {len(probe_gene_map)}")
print(f"Sample mappings: {probe_gene_map.head()}")

# Load sample annotations from the filename patterns
# Based on the sample names we saw earlier: STA1-30, AR1-15, BKVN1-15, CAN1-12, no.CAN1-7
sample_conditions = {}
for col in expr.columns:
    col_str = str(col)
    if 'BKVN' in col_str:
        sample_conditions[col] = 'peaking'  # Active BKV infection
    elif 'STA' in col_str:
        sample_conditions[col] = 'control'  # Stable graft (no BKV)
    elif 'AR' in col_str:
        sample_conditions[col] = 'control'  # Acute rejection (alternative control)
    elif 'CAN' in col_str and 'no' not in col_str:
        sample_conditions[col] = 'control'  # Cancer (control)
    elif 'no.CAN' in col_str:
        sample_conditions[col] = 'control'  # No cancer (control)
    else:
        sample_conditions[col] = 'unknown'

# Count samples per condition
print(f"\nSample condition mapping:")
from collections import Counter
condition_counts = Counter(sample_conditions.values())
for cond, count in condition_counts.items():
    print(f"  {cond}: {count} samples")

# Separate into groups
control_cols = [col for col, cond in sample_conditions.items() if cond == 'control']
peaking_cols = [col for col, cond in sample_conditions.items() if cond == 'peaking']

print(f"\nFinal sample groups:")
print(f"  Control (STA/AR/CAN): {len(control_cols)} samples")
print(f"  Peaking (BKVN): {len(peaking_cols)} samples")

# PATHWAY GENE SETS
PATHWAY_GENE_SETS = {
    "dna_replication":     ["MCM2","MCM5","PCNA","CDC45","RRM1","RRM2","CLSPN","TOP2A"],
    "cell_cycle":          ["CCND1","CDK2","RB1","MKI67","CENPF","SMC4","TP53","CCNB1"],
    "dna_damage_response": ["ATM","ATR","CHEK1","PRKDC","BRCA1","BRCA2","FANCI"],
    "innate_immune":       ["STAT1","IRF7","IFNB1","MX1","OAS1","IFIT1","ISG15"],
    "interferon_response": ["STAT1","IRF7","MX1","OAS1","IFIT1","IFIT3","ISG15"],
    "apoptosis":           ["BAX","BCL2","TP53","CASP3","CASP9"],
    "mtor_signaling":      ["MTOR","FKBP1A","RPS6KB1","EIF4EBP1","AKT1"],
    "cellular_stress":     ["HSP90AA1","HSPA8","MIF","HMOX1","HSPB1"],
    "nucleotide_synthesis": ["RRM1","RRM2","TYMS","DHODH","UMPS"],
    "translation":         ["EEF1A1","EEF2","RPL3","RPS6","EIF4A1","EIF3A"]
}

print("\nComputing pathway scores using probe-to-gene mapping...")

results = []
for pathway, genes in PATHWAY_GENE_SETS.items():
    # Find probes that map to these genes
    matching_probes = probe_gene_map[probe_gene_map['gene_symbol'].isin(genes)]['probe_id'].tolist()
    
    if not matching_probes:
        print(f"  {pathway}: No probes found")
        continue
    
    # Get expression for these probes (filter to only those present in expression matrix)
    available_probes = [p for p in matching_probes if p in expr.index]
    
    if not available_probes:
        print(f"  {pathway}: Probes found but not in expression matrix")
        continue
    
    pathway_expr = expr.loc[available_probes]
    
    # Compute mean expression per sample
    pathway_scores = pathway_expr.mean(axis=0)
    
    # Compare groups
    if len(control_cols) > 0 and len(peaking_cols) > 0:
        control_scores = pathway_scores[control_cols]
        peaking_scores = pathway_scores[peaking_cols]
        
        fc = peaking_scores.mean() / control_scores.mean() if control_scores.mean() > 0 else 1.0
        t_stat, pval = stats.ttest_ind(peaking_scores, control_scores)
        
        results.append({
            "pathway": pathway,
            "control_mean": control_scores.mean(),
            "peaking_mean": peaking_scores.mean(),
            "fold_change_peaking_vs_control": fc,
            "pvalue": pval,
            "n_probes_found": len(available_probes),
            "genes_queried": ",".join(genes),
            "source": "GSE75693 RMA-normalized Affymetrix HG-U133",
            "n_control_samples": len(control_cols),
            "n_peaking_samples": len(peaking_cols)
        })
        
        print(f"  {pathway}: FC={fc:.2f}, p={pval:.3f}, n_probes={len(available_probes)}")
    else:
        print(f"  {pathway}: SKIPPED (insufficient samples)")

if results:
    results_df = pd.DataFrame(results)
    output_path = "data/processed/GSE75693_pathway_fold_changes_COMPUTED.csv"
    results_df.to_csv(output_path, index=False)
    print(f"\nSaved computed fold changes to {output_path}")
    print(f"\nSummary of computed fold changes:")
    print(results_df[["pathway","fold_change_peaking_vs_control","pvalue","n_probes_found"]])
else:
    print("\nERROR: No pathway results computed")
