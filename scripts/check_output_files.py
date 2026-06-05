#!/usr/bin/env python3
"""
Check that all output files referenced in ISEF_PROJECT_OVERVIEW.md exist on disk.
"""

from pathlib import Path

print("=" * 80)
print("OUTPUT FILE CHECKLIST FOR ISEF PROJECT OVERVIEW")
print("=" * 80)
print()

# Files referenced in ISEF_PROJECT_OVERVIEW.md
required_files = [
    "outputs/clinical/roc_comparison.png",
    "outputs/clinical/feature_importance.png", 
    "outputs/clinical/calibration_plot.png",
    "outputs/clinical/risk_prediction_results.json",
    "outputs/clinical/viral_load_trajectories.png",
    "outputs/clinical/clinical_summary.json",
    "data/processed/synthetic_patient_cohort.csv",
    "data/processed/cohort_generation_params.json",
    "outputs/test_results.txt",
    "outputs/figures_summary.md",
    "docs/ISEF_PROJECT_OVERVIEW.md",
    "docs/bkpyv_research_to_model_map.md"
]

missing_files = []
existing_files = []

for file_path in required_files:
    path = Path(file_path)
    if path.exists():
        print(f"✓ EXISTS: {file_path}")
        existing_files.append(file_path)
    else:
        print(f"✗ MISSING: {file_path}")
        missing_files.append(file_path)

print()
print("=" * 80)
print(f"SUMMARY: {len(existing_files)} files exist, {len(missing_files)} files missing")
print("=" * 80)

if missing_files:
    print()
    print("Missing files:")
    for file in missing_files:
        print(f"  - {file}")
    exit(1)
else:
    print()
    print("✓ All required output files exist!")
    exit(0)