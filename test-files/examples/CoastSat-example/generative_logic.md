# CoastSat Generative Workflow

This note captures how the CoastSat example now iterates over RO-Crate provenance data and where large-language-model calls fit into the flow.

## 1. Enrich the Provenance Data (Python)
- `extract_steps_mini.py` resolves `interface.crate` and augments each workflow step with:
  - `inputs_detail` / `outputs_detail`: friendly metadata for each formal parameter.
  - `linked_files`: grouped mappings of parameters to the files that reference them (`exampleOfWork`).
- The helper also summarises notebook crates and truncates large blobs so we can work with deterministic strings.
- Re-run the helper inside the example virtualenv to inspect the enriched structure:
  ```bash
  cd test-files/examples/CoastSat-example
  .venv/bin/python extract_steps_mini.py interface.crate | less
  ```
  or load `extract_step_dicts('interface.crate')` inside a REPL/notebook for programmatic access.

## 2. Pre-compute Prompt Context in `coastsat_llm.smd`
- The document imports `extract_step_dicts` and, for each step:
  - Generates aggregate summaries (counts, representative examples, total linked files).
  - Builds a compact `prompt_context` string that lists the step name, position, programming language, repo URL, IO summaries, and linked artefact totals.
  - Selects a small number of output artefacts (`<=25` files each) to create `lineage_targets` with concise metadata and file samples.
- These pre-computed strings keep LLM prompts deterministic and bounded, avoiding full payloads of thousands of files.

## 3. Controlled Generative Calls
- **`@coastsat/step_overview`** (TemplateDescribe)
  - Input: `step.prompt_context` (aggregate summary only).
  - Goal: produce one or two paragraphs that explain the methodological role of the step and how its inputs/outputs fit together.
- **`@coastsat/data_lineage`** (TemplateDescribe)
  - Triggered only for artefacts with manageable file counts.
  - Input: curated context string per artefact (`parameter`, counts, metadata, sample filenames).
  - Goal: explain provenance and downstream usage without enumerating every file.
- Both prompts inherit document-level context partials so they remain aware of surrounding narrative while staying scoped to the supplied metadata.

## 4. Rendering the Document
- Within the `:::: for step in step_dicts` loop we now:
  1. Emit deterministic bullet summaries (counts, repositories, example IDs).
  2. Call `@coastsat/step_overview` for the narrative description.
  3. Optionally call `@coastsat/data_lineage` for highlighted outputs.
- The previous free-form describe prompt that inlined `step.raw` has been removed to avoid excessive context and hallucination risk.

## 5. Testing & Iteration
- Always run the helper script (or a targeted REPL snippet) after changing `extract_steps_mini.py` to confirm that summarised fields still exist and remain small.
- Use the `.venv` in `CoastSat-example/` when executing the Stencila document so the same library versions are available.
- When experimenting with new prompts, add them under `prompts/local/coastsat/` so they can be selected with `@coastsat/...` without affecting the global library.

## 6. Extending the Workflow
- To cover additional artefact types (e.g., inputs consumed by later steps), extend the summarisation logic to produce new aggregate strings and hook them into a dedicated prompt.
- Consider logging total prompt tokens or execution counts during iteration to track cost as provenance grows.
- Document any changes to thresholds (e.g., the `<=25` file rule for lineage prompts) here so future iterations know why certain artefacts are skipped.
