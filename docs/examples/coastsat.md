# CoastSat LLM Methodology Example

This case study demonstrates how we transform provenance stored in `interface.crate` into a reproducible, LLM-assisted methodology narrative. It lives under `test-files/examples/CoastSat-example/` and produces the rendered exemplar `example.html`.

## Key Assets

- `interface.crate`: Full CoastSat provenance archive for site `nzd0001`.
- `extract_steps_mini.py`: Deterministic extractor that prepares per-step payloads (metadata tables, notebook snapshots, inputs/outputs).
- `coastsat_llm.smd`: Stencila document orchestrating micro-prompts and display logic.
- `render_and_preview.sh` / `compile_coastsat_llm.sh`: Convenience scripts for rendering locally.
- `example.html`: Reference output capturing the workflow narrative, diagram, and per-step summaries.

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

## Refinement Checklist

- ✅ Deterministic prompt payloads (counts, summaries, sample links) minimise hallucination.
- ✅ Prompt suite enforces consistent Markdown structure, numbered step headings, and repository hyperlinks.
- ✅ Rendering scripts ensure the CLI uses the working-tree prompts (`STENCILA_PROMPTS_DIR`).
- Pending improvements:
  - Revisit artefact lineage prompts once the IO narratives settle.
  - Watch for local path leakage in outputs; tighten sanitisation if observed.
  - Expand to additional sites by parameterising `site_id` and re-running the pipeline.

## Maintenance Notes

- Regenerate `example.html` after updating `interface.crate`, micro-prompts, or extractor logic.
- Clear Stencila caches (`stencila clean coastsat_llm.smd`) if prompt changes appear stale.
- The extractor and prompts use ASCII-only formatting for compatibility; keep new additions consistent unless data demands otherwise.

