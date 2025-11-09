# CoastSat LLM Refinement Plan

## Goals
- Produce consistent, publication-ready prose for each workflow step.
- Surface links to provenance artefacts (GitHub files, local paths, RO-Crate assets).
- Incorporate notebook-level detail deterministically (code-cell summaries, previews).
- Keep prompts concise and reproducible while leveraging richer context.

## Action Items
1. **Data enrichment in `extract_steps_mini.py`** *(DONE)*
   - ✅ Markdown-ready links for inputs/outputs/linked artefacts
   - ✅ Notebook cell summaries with deterministic previews
   - ✅ Structured snippets stored on each step for prompt use

2. **Document rendering (`coastsat_llm.smd`)** *(DONE)*
   - ✅ Display metadata + notebook summary tables via Python exec blocks
   - ✅ Prompt context now includes Markdown links, notebook previews, and artefact summaries
   - ✅ Title, objective, and key operations prompts invoked per step in `coastsat_llm.smd`
   - ✅ Front-matter overview/diagram/outcomes prompts wired in before the per-step loop

3. **Prompt template updates** *(DONE)*
   - ✅ Workflow introduction prompts (`workflow/overview`, `workflow/diagram`, `workflow/outcomes`) added for the new preamble
   - ✅ Step-level micro-prompts (title/objective/operations/input/output) enforce consistent Markdown, repo links, and notebook references

4. **Deterministic input/output sections** *(DONE)*
   - ✅ Deterministic inputs/outputs overviews rendered per step with tables and bullet narratives
   - ✅ Input/output micro-prompts generate concise summaries with provenance-aware notes and notebook cell references

## Next Steps
- Render `coastsat_llm.smd` (still scoped to targeted steps) to validate the new overview section, diagram, and IO summaries. Confirm the Mermaid block renders and that sample links point to the current `site_id`.
- Monitor LLM responses for references to local file paths; adjust prompt payload sanitisation if needed.
- Extend provenance coverage (e.g., downstream dependency micro-prompts) or restore artefact lineage once the overview content is approved.

## Notes
- Notebook crates live under `interface.crate/notebooks/<step_id>/` with `ro-crate-metadata.json` describing code cells.
- `extract_step_dicts` already pulls many fields; focus on presenting them in prompt-friendly, deterministic formats.
- Remember performance: cap large lists (e.g. linked files) and provide aggregate counts + representative samples.
