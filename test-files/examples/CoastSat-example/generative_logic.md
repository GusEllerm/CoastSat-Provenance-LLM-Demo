# CoastSat Generative Workflow

This note captures how the CoastSat example now iterates over RO-Crate provenance data and where large-language-model calls fit into the flow.

## 1. Enrich the Provenance Data (Python)
- `extract_steps_mini.py` resolves `interface.crate` and augments each workflow step with:
  - `inputs_detail` / `outputs_detail`: friendly metadata for each formal parameter.
  - `inputs_overview` / `outputs_overview`: deterministic summaries containing GitHub-safe links, notebook cell references, transient artefact notes, and site-aware sample links (filtered to the current `site_id` when possible).
  - `linked_files`: grouped mappings of parameters to the files that reference them (`exampleOfWork`).
- The helper also summarises notebook crates and truncates large blobs so we can work with deterministic strings.
- Re-run the helper inside the example virtualenv to inspect the enriched structure:
  ```bash
  cd test-files/examples/CoastSat-example
  .venv/bin/python extract_steps_mini.py interface.crate | less
  ```
  or load `extract_step_dicts('interface.crate')` inside a REPL/notebook for programmatic access.

## 2. Pre-compute Prompt Context in `coastsat_llm.smd`
- The document imports `extract_step_dicts` and builds two collections:
  - `workflow_overview_input`, `workflow_diagram_input`, `workflow_outcomes_input` — aggregate datasets spanning all steps, used for the front-matter overview section.
  - `display_steps` — the subset of steps rendered in the main body (currently sliced for testing).
- For each step we still construct compact `prompt_context` strings and reuse the deterministic IO summaries so every prompt sees bounded, repeatable metadata.

## 3. Controlled Generative Calls
- **Top-level overview (new)**
  - `@livepublication/coastsat/workflow/overview-v2` — two introductory paragraphs about goals and tooling.
  - `@livepublication/coastsat/workflow/diagram-v2` — Mermaid flowchart connecting steps with repo links.
  - `@livepublication/coastsat/workflow/outcomes-v2` — bullet list of primary artefacts plus representative GitHub files.
- **Per-step micro-prompts**
  - `@livepublication/coastsat/step/title-v2` — 8-word title with repo link.
  - `@livepublication/coastsat/step/objective-v2` — single neutral objective sentence.
  - `@livepublication/coastsat/step/operations-v2` — 2-4 verb-led bullets referencing notebook cells.
  - `@livepublication/coastsat/step/input-v2` — 50-word input description referencing notebook cells and linked files.
  - `@livepublication/coastsat/step/output-v2` — 50-word output description referencing notebook cells and linked files.
- All prompts inherit document-level context partials so they remain aware of the broader narrative while staying scoped to supplied metadata. Lineage prompts are currently disabled because we prioritise concise IO narratives.

## 4. Rendering the Document
- The high-level overview appears before the per-step loop, giving readers goals, diagram, and headline outputs.
- Within the `:::: for step in display_steps` loop we now:
  1. Prepare deterministic Python payloads for the step (including a `_sequence` field used for numbered headings).
  2. Emit the title/objective/operations sections.
  3. Iterate deterministic lists of inputs and outputs, running the dedicated micro-prompts.
- Because each LLM call receives a curated payload, we avoid enumerating thousands of files yet maintain traceability through GitHub links and notebook references.

## 5. Testing & Iteration
- Always run the helper script (or a targeted REPL snippet) after changing `extract_steps_mini.py` to confirm that summarised fields still exist and remain small.
- Use the `.venv` in `CoastSat-example/` when executing the Stencila document so the same library versions are available.
- When experimenting with new prompts, add them under `stencila/prompts/template_describe/livepublication/` (or a `local/` namespace) so they can be selected with `@livepublication/...` without affecting the global library.

## 6. Extending the Workflow
- To cover additional artefact types (e.g., downstream dependency summaries), extend the summarisation logic to produce new aggregate strings and hook them into a dedicated prompt.
- Consider logging total prompt tokens or execution counts during iteration to track cost as provenance grows.
- Document any changes to thresholds (e.g., file-count limits or step slices) here so future iterations know why certain artefacts are skipped.
