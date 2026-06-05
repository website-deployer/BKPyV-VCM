"""VCM Clinical Integration Module."""

from .viral_load_mapper import (
    ViralLoadMapper,
    generate_clinical_summary
)

__all__ = [
    'ViralLoadMapper',
    'generate_clinical_summary',
]