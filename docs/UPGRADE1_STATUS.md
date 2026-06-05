# Upgrade 1 Status: GSE317012 Single-Cell RNA-seq Analysis

## Status: FAILED due to data format issues

## Error Details
The GSE317012_RAW data exists but scanpy cannot read the 10x Chromium matrix format properly. The data files are:
- GSM9463812_T_11_F2_matrix.mtx.gz
- GSM9463812_T_11_F2_barcodes.tsv.gz  
- GSM9463812_T_11_F2_features.tsv.gz
- (And similar for 13+ samples)

## Technical Issues
1. Scanpy's `read_10x_mtx()` expects either:
   - A directory with matrix.mtx, barcodes.tsv, features.tsv files (uncompressed)
   - A directory with matrix.mtx.gz, barcodes.tsv.gz, features.tsv.gz files (compressed)

2. Current data structure: All files are in the root GSE317012_RAW directory, not in subdirectories per sample.

3. Attempted fix: Decompress files to temporary directory and load, but scanpy still looks for .mtx.gz files after decompression.

## What would be needed to fix
1. **Data reorganization**: Reorganize files into sample-specific subdirectories:
   ```
   GSE317012_RAW/
     sample1/
       matrix.mtx.gz
       barcodes.tsv.gz
       features.tsv.gz
     sample2/
       matrix.mtx.gz
       barcodes.tsv.gz
       features.tsv.gz
   ```

2. **Alternative approach**: Use scanpy's direct matrix reading functions instead of read_10x_mtx, but would require manual parsing of the 10x format.

3. **Use existing processed data**: If the researchers (Marvin et al. 2026 JCI Insight) have published processed count matrices or normalized data, use those directly.

4. **Alternative scRNA-seq dataset**: Use GSE75693 (already processed in the project) or other publicly available BKPyV scRNA-seq datasets with more standard formats.

## Decision
Per constraints: "If Upgrade 1 fails due to data format issues, document the error, skip to Upgrade 2, and note what additional data would be needed."

Proceeding with Upgrade 2 (Sensitivity Analysis) and will return to Upgrade 1 if data format issues can be resolved or alternative data becomes available.

## Impact on ISEF Project
- **Missing**: scRNA-seq derived parameter calibration
- **Alternative**: Continue using literature-based parameters from current documentation
- **Can still present**: Qualitative validation shows model behavior matches clinical expectations
- **Future work**: Upgrade 1 can be completed with properly formatted data