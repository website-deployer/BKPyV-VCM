# Create probe-to-gene mapping using hgu133plus2.db annotation
library(hgu133plus2.db)

# Load the annotation package
library(AnnotationDbi)

# Get probe IDs from the expression matrix
expr <- read.csv("/Users/abhinavmishra/Projects/New Folder/virtual-cell-model/data/processed/GSE75693_normalized_R.csv", row.names=1)
probe_ids <- rownames(expr)

cat("Creating probe-to-gene mapping for", length(probe_ids), "probes\n")

# Map probe IDs to gene symbols
gene_symbols <- mapIds(hgu133plus2.db, 
                       keys=probe_ids, 
                       column="SYMBOL", 
                       keytype="PROBEID", 
                       multiVals="first")

# Create mapping dataframe
probe_gene_map <- data.frame(
    probe_id=probe_ids,
    gene_symbol=gene_symbols,
    stringsAsFactors=FALSE
)

# Save mapping
write.csv(probe_gene_map, "/Users/abhinavmishra/Projects/New Folder/virtual-cell-model/data/processed/probe_gene_mapping.csv", row.names=FALSE)

cat("Saved probe-to-gene mapping\n")
cat("Sample mappings:\n")
print(head(probe_gene_map))
cat("\nNumber of probes with gene symbols:", sum(!is.na(gene_symbols)), "/", length(gene_symbols))
