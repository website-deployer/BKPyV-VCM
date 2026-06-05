#!/usr/bin/env python3
"""
Process GSE317012 single-cell RNA-seq data to extract quantitative pathway activity scores
for BKPyV model parameter calibration.

Note: GSE317012 contains 10x Genomics single-cell data, not Affymetrix microarray as initially described.
This script adapts the analysis to work with the actual single-cell data format.
"""

import os
import sys
import glob
import numpy as np
import pandas as pd
from pathlib import Path
import json

# Set random seed for reproducibility
np.random.seed(42)

def install_and_import():
    """Install required packages and import them."""
    try:
        import scanpy as sc
        import anndata
        print("✓ scanpy and anndata already installed")
    except ImportError:
        print("Installing scanpy and anndata...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "scanpy", "anndata"])
        import scanpy as sc
        import anndata
        print("✓ scanpy and anndata installed successfully")
    
    return sc

def load_sample_metadata():
    """Load or infer sample metadata for GSE317012.
    
    Since GSE317012 is single-cell data, we need to determine condition assignments.
    Based on sample naming patterns, we'll infer conditions:
    - Control: T_XX_1 (single digit after T)
    - Peaking: T_XX_F2 (F2 likely indicates high viral load/peaking)
    - Resolving: T_XX (no suffix, post-peak)
    
    This is an approximation - actual metadata would be better.
    
    Note: Files are in format: GSM9463812_T_11_F2_matrix.mtx.gz (10x format, not subdirectories)
    """
    raw_dir = Path("/Users/abhinavmishra/Projects/New Folder/virtual-cell-model/data/raw/GSE317012_RAW")
    
    # Get all matrix files to identify samples
    matrix_files = sorted([f for f in raw_dir.glob("*matrix.mtx.gz") if f.name.startswith("GSM")])
    
    # Extract unique sample IDs from filenames
    sample_ids = set()
    for matrix_file in matrix_files:
        # GSM9463812_T_11_F2_matrix.mtx.gz -> GSM9463812_T_11_F2
        sample_id = matrix_file.name.replace('_matrix.mtx.gz', '').replace('_raw_matrix.mtx.gz', '')
        sample_ids.add(sample_id)
    
    sample_ids = sorted(list(sample_ids))
    
    metadata = []
    for sample_id in sample_ids:
        # Extract GSM ID
        gsm_id = sample_id.split('_')[0]
        
        # Extract pattern: GSM9463812_T_11_F2 -> T_11_F2
        if len(sample_id.split('_')) >= 3:
            pattern = '_'.join(sample_id.split('_')[1:])
        else:
            pattern = sample_id
        
        # Infer condition from naming pattern
        if 'F2' in pattern:
            condition = 'peaking'  # F2 likely indicates peak phase
        elif pattern.endswith('_1') or pattern.endswith('_2'):
            condition = 'control'  # Single digit after T likely control
        else:
            condition = 'resolving'  # No suffix, post-peak
        
        metadata.append({
            'sample_id': sample_id,
            'gsm_id': gsm_id,
            'pattern': pattern,
            'condition': condition,
            'path': str(raw_dir)  # Files are in the main directory
        })
    
    return pd.DataFrame(metadata)

def load_10x_data(sample_id, raw_dir):
    """Load 10x Genomics single-cell data matrix.
    
    Args:
        sample_id: Sample ID (e.g., "GSM9463812_T_11_F2")
        raw_dir: Directory containing the files
    """
    try:
        import scanpy as sc
    except ImportError:
        raise ImportError("scanpy not installed")
    
    # Check for 10x format files in the main directory
    matrix_files = list(raw_dir.glob(f"{sample_id}_matrix.mtx.gz"))
    features_files = list(raw_dir.glob(f"{sample_id}_features.tsv.gz"))
    barcodes_files = list(raw_dir.glob(f"{sample_id}_barcodes.tsv.gz"))
    
    if not matrix_files:
        # Try without .gz extension
        matrix_files = list(raw_dir.glob(f"{sample_id}_matrix.mtx"))
        features_files = list(raw_dir.glob(f"{sample_id}_features.tsv"))
        barcodes_files = list(raw_dir.glob(f"{sample_id}_barcodes.tsv"))
    
    if not matrix_files:
        raise ValueError(f"No matrix file found for sample {sample_id}")
    
    print(f"  Loading {sample_id}...")
    print(f"    Matrix: {matrix_files[0].name}")
    
    # Load using scanpy - note: scanpy.read_10x_mtx expects a directory
    # Since files are in the main directory, we need to handle this differently
    # We'll read the files manually using scipy and pandas
    
    import scipy.io as sio
    import gzip
    
    # Read matrix
    with gzip.open(matrix_files[0], 'rb') as f:
        matrix_data = sio.mmread(f)
    
    # Read features
    with gzip.open(features_files[0], 'rt') as f:
        features = pd.read_csv(f, sep='\t', header=None)
    
    # Read barcodes
    with gzip.open(barcodes_files[0], 'rt') as f:
        barcodes = pd.read_csv(f, sep='\t', header=None)
    
    # Create AnnData object manually
    import anndata
    
    gene_names = features[0].values
    cell_names = barcodes[0].values
    
    adata = anndata.AnnData(X=matrix_data.T.tocsr())  # Transpose to cells x genes
    adata.var_names = gene_names
    adata.obs_names = cell_names
    adata.var_names_make_unique()
    
    print(f"    Loaded {adata.n_obs} cells x {adata.n_vars} genes")
    
    return adata

def process_all_samples(metadata_df):
    """Process all samples and return combined expression matrix."""
    sc = install_and_import()
    
    processed_dir = Path("/Users/abhinavmishra/Projects/New Folder/virtual-cell-model/data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    raw_dir = Path("/Users/abhinavmishra/Projects/New Folder/virtual-cell-model/data/raw/GSE317012_RAW")
    
    # Load first sample to get gene list
    first_sample_id = metadata_df.iloc[0]['sample_id']
    print(f"Loading first sample: {first_sample_id}")
    adata_first = load_10x_data(first_sample_id, raw_dir)
    
    genes = adata_first.var_names.tolist()
    print(f"Total genes in dataset: {len(genes)}")
    
    # For single-cell data, we'll compute average expression per sample
    # Create a samples x genes matrix
    sample_expression = []
    sample_ids = []
    conditions = []
    
    for idx, row in metadata_df.iterrows():
        sample_id = row['sample_id']
        condition = row['condition']
        
        try:
            adata = load_10x_data(sample_id, raw_dir)
            
            # Compute average expression per gene
            import scipy.sparse as sp
            if sp.issparse(adata.X):
                avg_expr = np.mean(adata.X.toarray(), axis=0).flatten()
            else:
                avg_expr = np.mean(adata.X, axis=0).flatten()
            
            sample_expression.append(avg_expr)
            sample_ids.append(sample_id)
            conditions.append(condition)
            
        except Exception as e:
            print(f"Error loading {sample_id}: {e}")
            continue
    
    # Convert to DataFrame
    expression_matrix = pd.DataFrame(sample_expression, index=sample_ids, columns=genes)
    
    # Save normalized matrix
    expression_matrix.to_csv(processed_dir / "GSE317012_normalized.csv")
    print(f"Saved expression matrix to {processed_dir / 'GSE317012_normalized.csv'}")
    print(f"Matrix shape: {expression_matrix.shape}")
    
    # Save annotations
    annotations_df = pd.DataFrame({
        'sample_id': sample_ids,
        'condition': conditions
    })
    annotations_df.to_csv(processed_dir / "GSE317012_sample_annotations.csv", index=False)
    print(f"Saved sample annotations to {processed_dir / 'GSE317012_sample_annotations.csv'}")
    
    return expression_matrix, annotations_df, genes

def compute_pathway_activities(expression_matrix, annotations_df, genes):
    """Compute pathway activity scores for each sample."""
    
    # Define pathway gene sets from the model
    PATHWAY_GENE_SETS = {
        "dna_replication": ["MCM2", "MCM5", "PCNA", "CDC45", "DNAPOLALPHA", "RRM1", "RRM2"],
        "cell_cycle": ["CCND1", "CDK2", "RB1", "SMC4", "CENPF", "MKI67", "TP53"],
        "dna_damage_response": ["ATM", "ATR", "CHEK1", "PRKDC", "BRCA1", "BRCA2", "FANCI", "MMS22L"],
        "innate_immune": ["STAT1", "IRF7", "IFNB1"],
        "interferon_response": ["STAT1", "IRF7", "IFNB1", "MX1", "OAS1"],
        "apoptosis": ["BAX", "BCL2", "TP53"],
        "mtor_signaling": ["MTOR", "FKBP1A", "RPS6KB1", "EIF4EBP1"],
        "viral_replication": ["PCNA", "MCM2", "RRM2", "TOP2A"],
        "cellular_stress": ["HSP90AA1", "HSPA8", "MIF", "MT-ND4", "MT-CO1", "MT-CYB"],
        "nucleotide_synthesis": ["RRM1", "RRM2", "TYMS", "DHODH"]
    }
    
    # Check which genes are present in the data
    present_pathway_genes = {}
    print("\nGene presence in dataset:")
    for pathway, gene_list in PATHWAY_GENE_SETS.items():
        present_genes = [g for g in gene_list if g in genes]
        missing_genes = [g for g in gene_list if g not in genes]
        print(f"  {pathway}: {len(present_genes)}/{len(gene_list)} present")
        if missing_genes:
            print(f"    Missing: {missing_genes}")
        present_pathway_genes[pathway] = present_genes
    
    # Save pathway gene sets
    processed_dir = Path("/Users/abhinavmishra/Projects/New Folder/virtual-cell-model/data/processed")
    with open(processed_dir / "GSE317012_pathway_gene_sets.json", 'w') as f:
        json.dump(present_pathway_genes, f, indent=2)
    print(f"\nSaved pathway gene sets to {processed_dir / 'GSE317012_pathway_gene_sets.json'}")
    
    # Compute pathway activity scores (mean expression of pathway genes)
    pathway_scores = pd.DataFrame(index=expression_matrix.index)
    
    for pathway, gene_list in present_pathway_genes.items():
        if gene_list:  # Only if genes are present
            # Get expression of pathway genes
            pathway_expr = expression_matrix[gene_list]
            # Compute mean expression
            pathway_scores[pathway] = pathway_expr.mean(axis=1)
    
    # Add condition information
    pathway_scores['condition'] = annotations_df['condition'].values
    
    # Save pathway scores
    pathway_scores.to_csv(processed_dir / "GSE317012_pathway_scores.csv")
    print(f"Saved pathway scores to {processed_dir / 'GSE317012_pathway_scores.csv'}")
    
    return pathway_scores, present_pathway_genes

def compute_differential_pathway_activity(pathway_scores):
    """Compute differential pathway activity between conditions."""
    
    from scipy import stats
    
    # Get pathway columns (exclude condition)
    pathway_cols = [col for col in pathway_scores.columns if col != 'condition']
    
    results = []
    
    # Separate conditions
    control_scores = pathway_scores[pathway_scores['condition'] == 'control']
    peaking_scores = pathway_scores[pathway_scores['condition'] == 'peaking']
    resolving_scores = pathway_scores[pathway_scores['condition'] == 'resolving']
    
    print(f"\nCondition sample counts:")
    print(f"  Control: {len(control_scores)}")
    print(f"  Peaking: {len(peaking_scores)}")
    print(f"  Resolving: {len(resolving_scores)}")
    
    for pathway in pathway_cols:
        # Calculate means
        control_mean = control_scores[pathway].mean() if len(control_scores) > 0 else 0
        peaking_mean = peaking_scores[pathway].mean() if len(peaking_scores) > 0 else 0
        resolving_mean = resolving_scores[pathway].mean() if len(resolving_scores) > 0 else 0
        
        # Calculate fold changes (add small epsilon to avoid division by zero)
        epsilon = 0.001
        peaking_fc = (peaking_mean + epsilon) / (control_mean + epsilon) if control_mean > 0 else 1.0
        resolving_fc = (resolving_mean + epsilon) / (control_mean + epsilon) if control_mean > 0 else 1.0
        
        # Calculate p-values
        peaking_pval = stats.ttest_ind(peaking_scores[pathway], control_scores[pathway]).pvalue if len(peaking_scores) > 1 and len(control_scores) > 1 else 1.0
        resolving_pval = stats.ttest_ind(resolving_scores[pathway], control_scores[pathway]).pvalue if len(resolving_scores) > 1 and len(control_scores) > 1 else 1.0
        
        results.append({
            'pathway': pathway,
            'peaking_fc': peaking_fc,
            'resolving_fc': resolving_fc,
            'peaking_pval': peaking_pval,
            'resolving_pval': resolving_pval,
            'peaking_mean': peaking_mean,
            'resolving_mean': resolving_mean,
            'control_mean': control_mean
        })
    
    results_df = pd.DataFrame(results)
    
    # Save results
    processed_dir = Path("/Users/abhinavmishra/Projects/New Folder/virtual-cell-model/data/processed")
    results_df.to_csv(processed_dir / "GSE317012_pathway_fold_changes.csv", index=False)
    print(f"\nSaved pathway fold changes to {processed_dir / 'GSE317012_pathway_fold_changes.csv'}")
    
    # Print summary
    print("\nPathway Fold Change Summary (Peaking vs Control):")
    for _, row in results_df.iterrows():
        print(f"  {row['pathway']}: FC={row['peaking_fc']:.2f}, p={row['peaking_pval']:.3f}")
    
    return results_df

def main():
    """Main processing function."""
    
    print("=" * 70)
    print("GSE317012 Single-Cell Data Processing for BKPyV Parameter Calibration")
    print("=" * 70)
    
    # Step 1: Load sample metadata
    print("\nStep 1: Load sample metadata")
    print("-" * 70)
    metadata_df = load_sample_metadata()
    print(f"Found {len(metadata_df)} samples")
    print(f"Conditions: {metadata_df['condition'].value_counts().to_dict()}")
    
    # Step 2: Process all samples
    print("\nStep 2: Process all samples")
    print("-" * 70)
    expression_matrix, annotations_df, genes = process_all_samples(metadata_df)
    
    # Step 3: Compute pathway activities
    print("\nStep 3: Compute pathway activities")
    print("-" * 70)
    pathway_scores, present_genes = compute_pathway_activities(expression_matrix, annotations_df, genes)
    
    # Step 4: Compute differential expression
    print("\nStep 4: Compute differential pathway activity")
    print("-" * 70)
    fold_changes_df = compute_differential_pathway_activity(pathway_scores)
    
    print("\n" + "=" * 70)
    print("Processing Complete!")
    print("=" * 70)
    print("\nGenerated files:")
    print("  data/processed/GSE317012_normalized.csv")
    print("  data/processed/GSE317012_sample_annotations.csv")
    print("  data/processed/GSE317012_pathway_gene_sets.json")
    print("  data/processed/GSE317012_pathway_scores.csv")
    print("  data/processed/GSE317012_pathway_fold_changes.csv")
    
    print("\nNext steps:")
    print("  1. Review fold changes and update parameters.py")
    print("  2. Generate calibration report")
    print("  3. Re-run validation tests")

if __name__ == "__main__":
    main()
