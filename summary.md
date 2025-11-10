# CoastSat Provenance LLM Demo – Integration Summary

This document captures the key implementation steps and artefacts that underpin the generative methodology example published at [`docs/coastsat-example/example.html`](https://github.com/GusEllerm/CoastSat-Provenance-LLM-Demo/blob/master/docs/coastsat-example/example.html). It is intended to brief collaborators on how provenance data and LLM micro-prompts are combined to produce the CoastSat workflow narrative.

## Provenance Foundations

- Imported the full CoastSat RO-Crate ([`test-files/examples/CoastSat-example/interface.crate`](https://github.com/GusEllerm/CoastSat-Provenance-LLM-Demo/tree/master/test-files/examples/CoastSat-example/interface.crate)) containing step metadata, linked artefacts, notebook extracts, and statistics for site `nzd0001`.
- Extended `extract_steps_mini.py` to:
  - Normalise paths/URIs and map each step’s inputs, outputs, and notebook cells.
  - Generate prompt-ready payloads (`inputs_prompt_payload`, `outputs_prompt_payload`, `step_objective_input`, etc.), including GitHub-first links and transient artefact notes.
  - Summarise notebooks (cell names, full content, truncation flags) and provenance link lists for deterministic reuse in prompts.
- Stored deterministic context (counts, summaries, representative files) to limit LLM hallucination and keep reruns stable.

## Stencila / Templating Workflow

- Authored [`test-files/examples/CoastSat-example/coastsat_llm.smd`](https://github.com/GusEllerm/CoastSat-Provenance-LLM-Demo/blob/master/test-files/examples/CoastSat-example/coastsat_llm.smd), which:
  - Imports `extract_step_dicts` and prepares `display_steps = all_steps`.
  - Constructs workflow-level payloads for overview, diagram, and outcomes panels.
  - Iterates through each step with `for` blocks, emitting titles, objectives, operations, inputs, and outputs via TemplateDescribe calls.
  - Embeds provenance tables/notebook previews alongside generated text.
- Added shared context partial ([`stencila/prompts/partials/context/coastsat/overview.smd`](https://github.com/GusEllerm/CoastSat-Provenance-LLM-Demo/blob/master/stencila/prompts/partials/context/coastsat/overview.smd)) reused across prompts to keep narratives consistent.

## Prompt Suite

Created dedicated TemplateDescribe prompts under [`stencila/prompts/template_describe/livepublication/`](https://github.com/GusEllerm/CoastSat-Provenance-LLM-Demo/tree/master/stencila/prompts/template_describe/livepublication) (current `*-v2`/`*-v3` slugs):

| Scope | Prompt | Purpose |
| --- | --- | --- |
| Workflow | `workflow/overview-v2`, `workflow/diagram-v2`, `workflow/outcomes-v2` | High-level overview, Mermaid flowchart, bullet list of final outputs. |
| Step | `step/title-v2`, `step/objective-v2`, `step/operations-v3` | Numbered H2 titles with repo links; concise objectives citing notebook cells; ordered operations referencing code blocks. |
| IO | `step/input-v2`, `step/output-v2` | Per-parameter paragraphs describing role, provenance links, file counts, transient notes. |

Each prompt consumes the deterministic payloads from `extract_steps_mini.py`, reinforcing factual grounding and link consistency.

## Outputs and Publication

- Rendered HTML example: moved to [`docs/coastsat-example/example.html`](https://github.com/GusEllerm/CoastSat-Provenance-LLM-Demo/blob/master/docs/coastsat-example/example.html) so GitHub Pages (`https://gusellerm.github.io/CoastSat-Provenance-LLM-Demo/coastsat-example/example.html`) can serve the artefact.
- README and [`docs/examples/coastsat.md`](https://github.com/GusEllerm/CoastSat-Provenance-LLM-Demo/blob/master/docs/examples/coastsat.md) describe the workflow, prompt suite, and deterministic generation strategy.
- Added figure captions (in manuscript context) illustrating:
  - Procedural title generation loop.
  - Mermaid workflow diagram.
  - Objective generation referencing notebook cells.
  - Enumerated inputs linking to CoastSat provenance files.
- GitHub repo reorganised:
- Folded upstream Stencila sources into this repo via `git subtree` for transparency ([`stencila/`](https://github.com/GusEllerm/CoastSat-Provenance-LLM-Demo/tree/master/stencila) directory).
  - Updated metadata, topics, and public visibility; renamed repository to **CoastSat-Provenance-LLM-Demo**.

## Key Artefacts for Reference

- [`test-files/examples/CoastSat-example/interface.crate`](https://github.com/GusEllerm/CoastSat-Provenance-LLM-Demo/tree/master/test-files/examples/CoastSat-example/interface.crate)
- [`test-files/examples/CoastSat-example/extract_steps_mini.py`](https://github.com/GusEllerm/CoastSat-Provenance-LLM-Demo/blob/master/test-files/examples/CoastSat-example/extract_steps_mini.py)
- [`test-files/examples/CoastSat-example/coastsat_llm.smd`](https://github.com/GusEllerm/CoastSat-Provenance-LLM-Demo/blob/master/test-files/examples/CoastSat-example/coastsat_llm.smd)
- [`stencila/prompts/template_describe/livepublication/`](https://github.com/GusEllerm/CoastSat-Provenance-LLM-Demo/tree/master/stencila/prompts/template_describe/livepublication)
- [`docs/coastsat-example/example.html`](https://github.com/GusEllerm/CoastSat-Provenance-LLM-Demo/blob/master/docs/coastsat-example/example.html) (published example)
- [`docs/examples/coastsat.md`](https://github.com/GusEllerm/CoastSat-Provenance-LLM-Demo/blob/master/docs/examples/coastsat.md) (detailed documentation)


