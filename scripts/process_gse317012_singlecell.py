#!/usr/bin/env python3
"""
Process GSE317012 single-cell RNA-seq data to extract quantitative pathway activity scores
for BKPyV model parameter calibration.

Note: GSE317012 contains 10x Genomics single-cell data, not Affymetrix microarray as originally assumed.
Processing uses scanpy for single-cell analysis.
"""

import os
import sys
import glob
import numpy as np
import pandas as pd
from pathlib import Path

# Set random seed for reproducibility
np.random.seed(42)

def load_10x_data(sample_dir):
    """Load 10x Genomics single-cell data matrix."""
    try:
        import scanpy as sc
        import anndata
    except ImportError:
        print("Error: scanpy not installed. Install with: pip install scanpy anndata")
        sys.exit(1)
    
    print(f"Loading 10x data from {sample_dir}...")
    
    # Check for 10x format files
    matrix_file = glob.glob(os.path.join(sample_dir, "*matrix.mtx.gz"))[0]
    features_file = glob.glob(os.path.join(sample_dir, "*features.tsv.gz"))[0]
    barcodes_file = glob.glob(os.path.join(sample_dir, "*barcodes.tsv.gz"))[0]
    
    print(f"  Matrix: {os.path.basename(matrix_file)}")
    print(f"  Features: {os.path.basename(features_file)}")
    print(f"  Barcodes: {os.path.basename(barcodes_file)}")
    
    # Load using scanpy
    adata = sc.read_10x_mtx(
        sample_dir,
        var_names='gene_symbols',  # use gene symbols
        cache=True
    )
    
    # Make variable names unique
    adata.var_names_make_unique()
    
    print(f"Loaded {adata.n_obs} cells x {adata.n_vars} genes")
    return adata

def main():
    """Main function to process GSE317012 data."""
    
    # Set up paths
    project_root = Path("/Users/abhinavmishra/Projects/New Folder/virtual-cell-model")
    raw_data_dir = project_root / "data/raw/GSE317012_RAW"
    processed_dir = project_root / "data/processed"
    
    # Create processed directory
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("GSE317012 Single-Cell Data Processing")
    print("=" * 60)
    
    # Check if raw data directory exists
    if not raw_data_dir.exists():
        print(f"Error: Raw data directory not found: {raw_data_dir}")
        sys.exit(1)
    
    # List all sample directories
    sample_dirs = []
    for item in raw_data_dir.iterdir():
        if item.is_dir() and item.name.startswith("GSM"):
            sample_dirs.append(item)
    
    print(f"Found {len(sample_dirs)} sample directories")
    
    if len(sample_dirs) == 0:
        print("No sample directories found. Checking for direct 10x files...")
        # Try to load from main directory if files are there
        matrix_files = glob.glob(str(raw_data_dir / "*matrix.mtx.gz"))
        if matrix_files:
            print(f"Found {len(matrix_files)} matrix files in main directory")
            sample_dirs = [raw_data_dir]
        else:
            print("Error: No 10x data files found")
            sys.exit(1)
    
    # Parse sample names to infer conditions
    # Looking at sample names: T_11_F2, T_12_1, T_13_1, T_2_2, T_20, etc.
    # Need to determine which are control, peaking, resolving
    # For now, we'll load all and create a mapping
    
    print("\n" + "=" * 60)
    print("Step 1: Load 10x single-cell data")
    print("=" * 60)
    
    # Load first sample to get gene list and structure
    first_sample = sample_dirs[0]
    print(f"\nLoading first sample: {first_sample.name}")
    adata_example = load_10x_data(first_sample)
    
    # Get gene list
    genes = adata_example.var_names.tolist()
    print(f"Genes in first sample: {len(genes)}")
    
    # Save gene list
    gene_list_path = processed_dir / "GSE317012_gene_list.txt"
    with open(gene_list_path, 'w') as f:
        f.write('\n'.join(genes))
    print(f"Saved gene list to {gene_list_path}")
    
    print("\n" + "=" * 60)
    print("Step 2: Annotate samples by condition")
    print("=" * 60)
    
    # For single-cell data, we need to parse sample names to infer conditions
    # Based on the naming pattern (T_X_Y), we may need to look at metadata
    # For now, create a placeholder annotation
    sample_annotations = []
    
    for sample_dir in sample_dirs:
        sample_name = sample_dir.name
        # Parse sample name to determine condition
        # This is a placeholder - would need actual metadata
        sample_annotations.append({
            'sample_id': sample_name,
            'condition': 'unknown',  # Would need metadata
            'path': str(sample_dir)
        })
    
    annotations_df = pd.DataFrame(sample_annotations)
    annotations_path = processed_dir / "GSE317012_sample_annotations.csv"
    annotations_df.to_csv(annotations_path, index=False)
    print(f"Saved sample annotations to {annotations_path}")
    print(f"Total samples: {len(sample_annotations)}")
    
    print("\n" + "=" * 60)
    print("Step 3: Define pathway gene sets")
    print("=" * 60)
    
    # Define pathway gene sets from the model
    PATHWAY_GENE_SETS = {
        "dna_replication": ["MCM2", "MCM5", "PCNA", "CDC45", "RRM1", "RRM2"],
        "cell_cycle": ["CCND1", "CDK2", "RB1", "SMC4", "CENPF", "MKI67", "TP53"],
        "dna_damage_response": ["ATM", "ATR", "CHEK1", "PRKDC", "BRCA1", "BRCA2", "FANCI", "MMS22L"],
        "innate_immune": ["STAT1", "IRF7", "IFNB1"],
        "interferon_response": ["STAT1", "IRF7", "IFNB1", "MX1", "OAS1"],
        "apoptosis": ["BAX", "BCL2", "TP53"],
        "mtor_signaling": ["MTOR", "FKBP1A"],
        "viral_replication": ["PCNA", "MCM2", "RRM2"],
        "cellular_stress": ["HSP90AA1", "HSPA8", "MIF"],
        "nucleotide_synthesis": ["RRM1", "RRM2"]
    }
    
    # Check which genes are present in the data
    print("\nGene presence in data:")
    for pathway, gene_list in PATHWAY_GENE_SETS.items():
        present_genes = [g for g in gene_list if g in genes]
        missing_genes = [g for g in gene_list if g not in genes]
        print(f"  {pathway}: {len(present_genes)}/{len(gene_list)} present")
        if missing_genes:
            print(f"    Missing: {missing_genes}")
        PATHWAY_GENE_SETS[pathway] = present_genes  # Update to only present genes
    
    # Save pathway gene sets
    pathway_path = processed_dir / "GSE317012_pathway_gene_sets.json"
    import json
    with open(pathway_path, 'w') as f:
        json.dump(PATHWAY_GENE_SETS, f, indent=2)
    print(f"\nSaved pathway gene sets to {pathway_path}")
    
    print("\n" + "=" * 60)
    print("Processing complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Need to determine actual sample conditions (control/peaking/resolving)")
    print("2. Load and normalize all samples")
    print("3. Compute pathway activity scores")
    print("4. Calculate differential expression")
    print("5. Update model parameters")

if __name__ == "__main__":
    main()
