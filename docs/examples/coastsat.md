# CoastSat LLM Methodology Example

This case study demonstrates how we transform provenance stored in `interface.crate` into a reproducible, LLM-assisted methodology narrative. The sources remain in `test-files/examples/CoastSat-example/`, while the rendered exemplar is published at `docs/coastsat-example/example.html`.

## Key Assets

- `interface.crate`: Full CoastSat provenance archive for site `nzd0001`.
- `extract_steps_mini.py`: Deterministic extractor that prepares per-step payloads (metadata tables, notebook snapshots, inputs/outputs).
- `coastsat_llm.smd`: Stencila document orchestrating micro-prompts and display logic.
- `render_and_preview.sh` / `compile_coastsat_llm.sh`: Convenience scripts for rendering locally.
- `docs/coastsat-example/example.html`: Reference output capturing the workflow narrative, diagram, and per-step summaries (served via GitHub Pages at [`https://gusellerm.github.io/stencila-dev/coastsat-example/example.html`](https://gusellerm.github.io/stencila-dev/coastsat-example/example.html)).

## Setup & Rendering

1. From `test-files/examples/CoastSat-example/`, fetch the crate (optional if already present):
   ```bash
   ./fetch-interface-crate.sh
   ```
2. Render the Stencila document using the local CLI build and repo prompts:
   ```bash
   ./render_and_preview.sh
   ```
   The script exports `STENCILA_PROMPTS_DIR` so updated prompts are respected.
3. For the full convert → render pipeline (as used in CI), run:
   ```bash
   ./compile_coastsat_llm.sh
   ```

## Generative Workflow Highlights

- **Provenance extraction:** `extract_step_dicts()` derives structured `step_dicts` covering metadata, GitHub links, notebook cells, and IO summaries.
- **Micro-prompts (TemplateDescribe):**
  - Workflow preamble: `@livepublication/coastsat/workflow/overview-v2`, `diagram-v2`, `outcomes-v2`.
  - Per-step focus: `@livepublication/coastsat/step/title-v3`, `objective-v2`, `operations-v3`.
  - Inputs/outputs: `@livepublication/coastsat/step/input-v2`, `output-v2`.
- **Notebook integration:** Up to ten notebook cells per step surfaced via collapsible previews and referenced inside prompt outputs.
- **Site-aware linking:** Payloads prioritise GitHub artefacts matching `site_id` (`nzd0001`) and annotate transient states when no files are captured.

## Maintenance Notes

- Regenerate `docs/coastsat-example/example.html` after updating `interface.crate`, micro-prompts, or extractor logic (copy or move the newly rendered HTML into `docs/coastsat-example/`).
- Clear Stencila caches (`stencila clean coastsat_llm.smd`) if prompt changes appear stale.
- The extractor and prompts use ASCII-only formatting for compatibility; keep new additions consistent unless data demands otherwise.

