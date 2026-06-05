#!/usr/bin/env python3
"""
Analyze GSE317012 single-cell RNA-seq data for BKPyV VCM parameter calibration.

This script processes 10x Chromium scRNA-seq data from BKV-infected kidney allograft biopsies,
computes pathway activity scores per condition, and generates visualizations.
"""

import scanpy as sc
import numpy as np
import pandas as pd
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Scanpy settings
sc.settings.verbosity = 3
sc.settings.set_figure_params(dpi=150, facecolor='white')

def main():
    """Main function to analyze GSE317012 scRNA-seq data."""
    print("=" * 80)
    print("GSE317012 Single-Cell RNA-seq Analysis")
    print("=" * 80)
    print()
    
    data_dir = Path("data/raw/GSE317012_RAW")
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Find and load matrix files
    print("Step 1: Finding and loading 10x matrix files...")
    adatas = []
    sample_info = []
    
    # The data files are directly in the directory, not in subdirectories
    # Each sample has barcodes, features, and matrix files
    # Group files by sample ID
    sample_groups = {}
    
    for file_path in data_dir.glob("*.mtx.gz"):
        # Extract sample ID from filename
        sample_id = file_path.name.replace("_matrix.mtx.gz", "").replace("_matrix.mtx", "")
        if sample_id not in sample_groups:
            sample_groups[sample_id] = {}
        sample_groups[sample_id]['matrix'] = file_path
    
    for file_path in data_dir.glob("*.tsv.gz"):
        if "barcodes" in file_path.name:
            sample_id = file_path.name.replace("_barcodes.tsv.gz", "").replace("_barcodes.tsv", "")
            if sample_id not in sample_groups:
                sample_groups[sample_id] = {}
            sample_groups[sample_id]['barcodes'] = file_path
        elif "features" in file_path.name:
            sample_id = file_path.name.replace("_features.tsv.gz", "").replace("_features.tsv", "")
            if sample_id not in sample_groups:
                sample_groups[sample_id] = {}
            sample_groups[sample_id]['features'] = file_path
    
    print(f"Found {len(sample_groups)} sample groups")
    
    # Load each sample that has all required files
    for sample_name, files in sorted(sample_groups.items()):
        if 'matrix' in files and 'barcodes' in files and 'features' in files:
            print(f"  Processing sample: {sample_name}")
            
            try:
                # Determine condition from sample name
                if any(x in sample_name.upper() for x in ['F2', 'PEAK', 'HIGH', 'BKV']):
                    condition = 'peaking'
                elif any(x in sample_name.upper() for x in ['CA', 'CONTROL', 'DONOR']):
                    condition = 'control' 
                elif any(x in sample_name.upper() for x in ['SV', 'RESOLV', 'LOW']):
                    condition = 'resolving'
                else:
                    condition = 'unknown'
                
                print(f"    Condition: {condition}")
                
                # Load using scanpy's read_10x_mtx with the directory approach
                # Create temporary directory with the sample's files
                import tempfile
                import shutil
                import gzip
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    
                    # Copy and decompress files to temp directory
                    for file_type in ['matrix', 'barcodes', 'features']:
                        src_file = files[file_type]
                        dst_name = file_type + '.mtx' if file_type == 'matrix' else file_type + '.tsv'
                        dst_file = temp_path / dst_name
                        
                        with gzip.open(src_file, 'rt') as f_in:
                            with open(dst_file, 'w') as f_out:
                                f_out.write(f_in.read())
                    
                    # Load from temp directory
                    adata = sc.read_10x_mtx(temp_path, var_names='gene_symbols', cache=True)
                    adata.obs['sample'] = sample_name
                    adata.obs['condition'] = condition
                    adatas.append(adata)
                    sample_info.append({
                        'sample': sample_name,
                        'condition': condition,
                        'n_cells': adata.shape[0],
                        'n_genes': adata.shape[1]
                    })
                    print(f"    Loaded: {adata.shape[0]} cells, {adata.shape[1]} genes")
                    
            except Exception as e:
                print(f"    Could not load {sample_name}: {e}")
                import traceback
                traceback.print_exc()
    
    if not adatas:
        print("ERROR: No samples could be loaded")
        return
    
    print(f"Successfully loaded {len(adatas)} samples")
    print()
    
    # Step 2: Concatenate samples
    print("Step 2: Concatenating samples...")
    adata = sc.concat(adatas, label='sample', keys=[s.obs['sample'].iloc[0] for s in adatas])
    print(f"Combined: {adata.shape[0]} cells, {adata.shape[1]} genes")
    print()
    
    # Step 3: Standard QC and preprocessing
    print("Step 3: Quality control and preprocessing...")
    
    # Basic filtering
    print("  Filtering cells and genes...")
    sc.pp.filter_cells(adata, min_genes=200)
    sc.pp.filter_genes(adata, min_cells=3)
    print(f"  After filtering: {adata.shape[0]} cells, {adata.shape[1]} genes")
    
    # Mitochondrial gene filtering
    adata.var['mt'] = adata.var_names.str.startswith('MT-')
    sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], inplace=True)
    
    print(f"  Before MT filtering: {adata.shape[0]} cells")
    adata = adata[adata.obs.pct_counts_mt < 20]
    print(f"  After MT filtering: {adata.shape[0]} cells")
    
    # Gene count filtering
    print(f"  Before gene count filtering: {adata.shape[0]} cells")
    adata = adata[adata.obs.n_genes_by_counts < 6000]
    print(f"  After gene count filtering: {adata.shape[0]} cells")
    
    # Normalization
    print("  Normalizing and log-transforming...")
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    
    # Highly variable genes
    print("  Finding highly variable genes...")
    sc.pp.highly_variable_genes(adata, n_top_genes=2000)
    
    # Scale and PCA
    print("  Scaling and running PCA...")
    sc.pp.scale(adata)
    sc.pp.pca(adata, n_comps=50)
    
    # Neighborhood and UMAP
    print("  Computing neighborhood graph and UMAP...")
    sc.pp.neighbors(adata, n_neighbors=10, n_pcs=40)
    sc.tl.umap(adata)
    
    # Clustering
    print("  Running Leiden clustering...")
    sc.tl.leiden(adata, resolution=0.5)
    
    print(f"Final dataset: {adata.shape[0]} cells, {adata.shape[1]} genes")
    print(f"Found {len(adata.obs['leiden'].unique())} clusters")
    print()
    
    # Step 4: Save processed data
    print("Step 4: Saving processed data...")
    adata.write(output_dir / "GSE317012_processed.h5ad")
    print(f"Saved to {output_dir / 'GSE317012_processed.h5ad'}")
    print()
    
    # Step 5: Compute pathway activity scores
    print("Step 5: Computing pathway activity scores...")
    
    PATHWAY_GENES = {
        "dna_replication": ["MCM2","MCM5","PCNA","CDC45","RRM1","RRM2","TOP2A","CLSPN","MKI67"],
        "cell_cycle": ["CCND1","CDK2","MKI67","CENPF","CCNB1","CDK1","CDKN1A","CDC20"],
        "dna_damage_response": ["ATM","ATR","CHEK1","BRCA1","BRCA2","PRKDC","H2AX","TP53"],
        "innate_immune": ["STAT1","IRF7","IFNB1","MX1","OAS1","IFIT1","ISG15","IFIT3"],
        "apoptosis": ["BAX","BCL2","CASP3","TP53","BBC3","PMAIP1"],
        "mtor_signaling": ["MTOR","FKBP1A","RPS6KB1","EIF4EBP1","RPS6"],
        "cellular_stress": ["HSP90AA1","HSPA8","HMOX1","HSPB1","DNAJA1"],
        "translation": ["EEF1A1","EEF2","RPL3","RPS6","EIF4A1","RPLP0"],
        "viral_response": ["STAT1","IRF7","IFIT1","MX1","OAS1","ISG15"],
        "mitochondrial": ["MT-ND4","MT-CO1","MT-CYB","MT-ATP6","MT-ND1"]
    }
    
    results = []
    conditions = adata.obs['condition'].unique()
    
    for pathway, genes in PATHWAY_GENES.items():
        present = [g for g in genes if g in adata.var_names]
        if not present:
            print(f"  WARNING: No genes found for {pathway}")
            continue
        
        pathway_scores = {}
        for cond in conditions:
            mask = adata.obs['condition'] == cond
            if mask.sum() > 0:
                scores = adata[mask, present].X
                if hasattr(scores, 'toarray'):
                    scores = scores.toarray()
                pathway_scores[cond] = float(np.mean(scores))
            else:
                pathway_scores[cond] = 0.0
        
        # Compute fold changes vs control
        control_score = pathway_scores.get('control', 1.0)
        if control_score > 0:
            fc_peaking = pathway_scores.get('peaking', control_score) / control_score
            fc_resolving = pathway_scores.get('resolving', control_score) / control_score
        else:
            fc_peaking = 1.0
            fc_resolving = 1.0
        
        results.append({
            'pathway': pathway,
            'control_mean': control_score,
            'peaking_mean': pathway_scores.get('peaking', control_score),
            'resolving_mean': pathway_scores.get('resolving', control_score),
            'fc_peaking_vs_control': fc_peaking,
            'fc_resolving_vs_control': fc_resolving,
            'n_genes_found': len(present),
            'genes_found': ','.join(present),
            'source': 'GSE317012 10x scRNA-seq computed'
        })
    
    df = pd.DataFrame(results)
    df.to_csv(output_dir / "GSE317012_scrna_pathway_scores.csv", index=False)
    print(f"Saved pathway scores to {output_dir / 'GSE317012_scrna_pathway_scores.csv'}")
    print()
    print("Pathway activity summary:")
    print(df[['pathway','fc_peaking_vs_control','fc_resolving_vs_control','n_genes_found']])
    print()
    
    # Step 6: Generate UMAP visualizations
    print("Step 6: Generating UMAP visualizations...")
    
    # Create output directory for figures
    figures_dir = Path("outputs/scrna")
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # UMAP by condition
    print("  Generating UMAP by condition...")
    sc.pl.umap(adata, color=['condition'], save='_GSE317012_condition.png')
    # Move the figure to outputs/scrna
    src = Path("figures/umap_GSE317012_condition.png")
    if src.exists():
        import shutil
        shutil.move(src, figures_dir / "GSE317012_umap_condition.png")
    
    # UMAP by leiden clusters
    print("  Generating UMAP by clusters...")
    sc.pl.umap(adata, color=['leiden'], save='_GSE317012_leiden.png')
    src = Path("figures/umap_GSE317012_leiden.png")
    if src.exists():
        import shutil
        shutil.move(src, figures_dir / "GSE317012_umap_leiden.png")
    
    print(f"Figures saved to {figures_dir}")
    print()
    
    # Step 7: Generate pathway heatmap
    print("Step 7: Generating pathway activity heatmap...")
    
    # Create heatmap data
    heatmap_data = df[['pathway','control_mean','peaking_mean','resolving_mean']].copy()
    heatmap_data = heatmap_data.set_index('pathway')
    
    # Normalize for visualization
    heatmap_data_norm = heatmap_data.div(heatmap_data.max(axis=1), axis=0)
    
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 8))
    import seaborn as sns
    sns.heatmap(heatmap_data_norm, annot=True, cmap='YlOrRd', fmt='.2f', cbar_kws={'label': 'Normalized Activity'})
    plt.title('Pathway Activity Scores by Condition (GSE317012)')
    plt.ylabel('Pathway')
    plt.xlabel('Condition')
    plt.tight_layout()
    plt.savefig(figures_dir / "GSE317012_pathway_heatmap.png", dpi=150)
    plt.close()
    
    print(f"Heatmap saved to {figures_dir / 'GSE317012_pathway_heatmap.png'}")
    print()
    
    print("=" * 80)
    print("GSE317012 Analysis Complete")
    print("=" * 80)
    print(f"Processed: {adata.shape[0]} cells, {adata.shape[1]} genes")
    print(f"Conditions: {', '.join(conditions)}")
    print(f"Pathways analyzed: {len(results)}")
    print()
    print("Output files:")
    print(f"  - {output_dir / 'GSE317012_processed.h5ad'}")
    print(f"  - {output_dir / 'GSE317012_scrna_pathway_scores.csv'}")
    print(f"  - {figures_dir / 'GSE317012_umap_condition.png'}")
    print(f"  - {figures_dir / 'GSE317012_umap_leiden.png'}")
    print(f"  - {figures_dir / 'GSE317012_pathway_heatmap.png'}")
    print()

if __name__ == "__main__":
    main()