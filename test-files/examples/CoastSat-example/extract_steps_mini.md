# `extract_steps_mini` Refactor Log

This document tracks decisions, milestones, and tests while we break down `extract_steps_mini.py` into a maintainable module suite for the CoastSat example.

## Goals
- Reduce the size and complexity of the current monolithic script without changing behaviour.
- Group responsibilities into clearer layers (crate loading, summarisation, prompt payload preparation, workflow aggregation).
- Preserve the public API consumed by `coastsat_llm.smd`: `extract_step_dicts` and `build_workflow_context`.
- Maintain deterministic outputs for the Stencila document (prompt payloads, counts, links) and keep integration tests passing.

## Initial State (2025-11-10)
- `extract_steps_mini.py` ~1,400 lines combining RO-Crate ingestion, notebook parsing, stats aggregation, prompt preparation.
- Stencila document imports `extract_step_dicts` and `build_workflow_context` directly from this file.
- Smoke testing performed via ad-hoc Python snippets (`python - <<'PY' ...`).

### Progress
- 2025-11-10: Created `extract_steps_package/` with initial `pipeline.py` (copy of legacy implementation) and shimmed `extract_steps_mini.py` to re-export from the package.
- 2025-11-10: Extracted RO-Crate loader utilities into `extract_steps_package/loader.py`; `pipeline.py` now imports the loader primitives instead of inlining them.
- 2025-11-10: Moved summary/table/lineage helpers into `extract_steps_package/summaries.py` and prompt payload preparation into `extract_steps_package/prompts.py`, keeping `pipeline.py` focused on orchestration.

## Planned Work
1. Introduce an `extract_steps_mini/` package within `CoastSat-example/` to house modular components.
2. Gradually migrate logic:
   - Loader & crate utilities
   - Summaries & table builders
   - Prompt payload preparation
   - Public façade exposing existing API
3. Backfill lightweight tests/smoke scripts to ensure parity at each step.
4. Update documentation (`helper.md`, etc.) as interfaces stabilise.

## Testing Strategy
- Continue running inline Python smoke tests comparing key outputs (step counts, payload keys, representative values).
- Consider adding pytest-based fixtures for regression once the package layout is stable.
- After the final migration, re-render `coastsat_llm.smd` using `render_and_preview.sh` to ensure Stencila execution still succeeds.

## Notes
- Any new helper modules should remain importable from `extract_steps_mini/__init__.py` to keep the Stencila import surface unchanged.
- Avoid introducing new external dependencies during refactor.
- Keep Markdown doc updated with milestones, issues, and test results.

