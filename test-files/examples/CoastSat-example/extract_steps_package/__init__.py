"""Modular implementation for CoastSat provenance extraction."""

from .pipeline import (  # noqa: F401
    build_workflow_context,
    extract_step_dicts,
    extract_step_models,
    main,
)

__all__ = [
    "extract_step_dicts",
    "extract_step_models",
    "build_workflow_context",
    "main",
]
