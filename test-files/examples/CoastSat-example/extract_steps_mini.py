# coding: utf-8
"""Compatibility shim for the legacy `extract_steps_mini` module.

The refactored implementation now lives under `extract_steps_package`. This
file keeps existing imports working while the codebase transitions to the new
package structure.
"""

from __future__ import annotations

import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from extract_steps_package import (  # noqa: F401
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


if __name__ == "__main__":
    import sys

    main(sys.argv)
