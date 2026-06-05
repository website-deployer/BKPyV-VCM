# Set CRAN mirror
options(repos=structure(c(CRAN="https://cloud.r-project.org/")))

# Install Bioconductor packages
if (!requireNamespace("BiocManager", quietly=TRUE)) install.packages("BiocManager")
BiocManager::install(c("affy", "limma", "GEOquery", "hgu133plus2.db"), ask=FALSE)

library(affy)
library(limma)
library(GEOquery)

# Load all CEL files
setwd("/Users/abhinavmishra/Projects/New Folder/virtual-cell-model/data/raw/GSE75693_RAW")
cel_files <- list.files(pattern="\\.CEL$", full.names=TRUE)
cat("Found", length(cel_files), "CEL files\n")

# RMA normalization
raw_data <- ReadAffy(filenames=cel_files)
eset <- rma(raw_data)

# Save normalized expression matrix
expr_matrix <- exprs(eset)
write.csv(expr_matrix, "/Users/abhinavmishra/Projects/New Folder/virtual-cell-model/data/processed/GSE75693_normalized_R.csv")
cat("Normalized matrix saved:", nrow(expr_matrix), "probes x",
    ncol(expr_matrix), "samples\n")

# Fetch sample metadata from GEO
gse <- getGEO("GSE75693", GSEMatrix=TRUE)
pdata <- pData(phenoData(gse[[1]]))
write.csv(pdata, "/Users/abhinavmishra/Projects/New Folder/virtual-cell-model/data/processed/GSE75693_sample_metadata.csv")

# Print metadata structure
cat("\nMetadata columns:\n")
print(colnames(pdata))
cat("\nSample metadata preview:\n")
print(head(pdata[, grep("characteristics|title|source",
                         colnames(pdata), ignore.case=TRUE)]))
