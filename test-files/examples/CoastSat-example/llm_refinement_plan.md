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

3. **Prompt template updates** *(DONE)*
   - ✅ `livepublication/coastsat/step` enforces consistent Markdown sections, hyperlink usage, and notebook references
   - ✅ `livepublication/coastsat/data` requires structured provenance bullets with links

## Next Steps
- Monitor prompt outputs after rendering (`./render_and_preview.sh`) and adjust examples if models need further nudging.
- Consider adding per-artefact aggregation (e.g. counts by file type) if the prose still feels vague.

## Notes
- Notebook crates live under `interface.crate/notebooks/<step_id>/` with `ro-crate-metadata.json` describing code cells.
- `extract_step_dicts` already pulls many fields; focus on presenting them in prompt-friendly, deterministic formats.
- Remember performance: cap large lists (e.g. linked files) and provide aggregate counts + representative samples.
