# Provenance-Guided LLM Authoring Experiment

## Project Structure

```
stencila_dev/
├── README.md              # This file
├── docs/                  # Organized documentation
│   ├── getting-started/   # Quick start guides
│   ├── development/       # Development workflows
│   └── extension/         # Extension-specific guides
├── scripts/               # Helper scripts
│   ├── start-dev.sh      # One-command startup
│   ├── dev.sh            # Setup script
│   ├── build.sh          # Build everything
│   └── ...
├── stencila/             # Local Stencila toolchain & extension sources
│   ├── rust/            # Core Rust implementation
│   ├── vscode/          # VS Code extension
│   └── ...
└── test-files/          # Test documents
    ├── inputs/         # Source files
    ├── examples/       # Example documents
    └── outputs/        # Generated files
```

## Overview

### Stencila as a templating engine for provenance-aware LLM authoring. 
The CoastSat experiment uses interface.crate provenance and a Dynamic Authoring Framework to generate methodology prose via bounded micro-inference tasks. Each LLM call is supplied with deterministic context prepared in Python, preserving traceability between narrative text and the underlying computational workflow.

### Motivations
- Reduce hallucination risk by constraining prompts to narrowly scoped tasks.
- Preserve epistemic grounding by deferring factual weight to provenance artefacts, not model output.
- Showcase how interface-level provenance can be surfaced to readers alongside narrative text.
- Provide an extensible pattern for other RO-Crate based workflows.

## Core Components

- **`test-files/examples/CoastSat-example/interface.crate`** – RO-Crate capturing the CoastSat shoreline analysis workflow.
- **`test-files/examples/CoastSat-example/extract_steps_mini.py`** – Deterministically derives `step_dicts`, notebook snippets, IO summaries, and stats for prompting.
- **`test-files/examples/CoastSat-example/coastsat_llm.smd`** – Stencila document assembling overview, diagram, and per-step sections; invokes the micro-prompts.
- **Stencila prompt suite** (`stencila/prompts/template_describe/livepublication/*.smd`) – TemplateDescribe micro-prompts for titles, objectives, operations, inputs, outputs, overview, diagram, outcomes, etc.
- **`test-files/examples/CoastSat-example/render_and_preview.sh`** – Renders the document with the repo prompt directory (`STENCILA_PROMPTS_DIR`) enforced.
- **`docs/coastsat-example/example.html`** – Reference output illustrating the methodology, provenance links, and Mermaid workflow diagram (also published via GitHub Pages at [`https://gusellerm.github.io/stencila-dev/coastsat-example/example.html`](https://gusellerm.github.io/stencila-dev/coastsat-example/example.html)).

## Rendering the CoastSat Example

```bash
cd test-files/examples/CoastSat-example
./render_and_preview.sh
```

This command builds `coastsat_llm.smd`, writes `test.html`, and opens it. For a multi-step convert → evaluate → render workflow (as used in automated pipelines) run `./compile_coastsat_llm.sh`.

## Design Philosophy

1. **Provenance-first**  
   Every narrative block references data extracted from `interface.crate`: metadata tables, linked GitHub artefacts, notebook cells, and parameter-level notes.

2. **Dynamic Authoring Framework**  
   The Stencila micro-prompts orchestrate micro-inference tasks (e.g. step title, objective, operations). Each has strict Markdown expectations, link requirements, and word limits.

3. **Deterministic context**  
   Python pre-processing filters, truncates, and formats context so the LLM receives consistent payloads. Notebook snippets, cell references, and counts are capped to keep inference bounded.

4. **Transparent outputs**  
   Generated prose accompanies collapsible tables, code previews, and hyperlink lists. Readers can trace statements on inputs/outputs back to their sources.

## Documentation

- **[CoastSat methodology example](docs/examples/coastsat.md)** – Setup, key prompts, and refinement checklist.
- **[Prompt definitions](stencila/prompts/template_describe/livepublication/)** – Source for each TemplateDescribe prompt and shared partials.
- **[Generative logic notes](test-files/examples/CoastSat-example/generative_logic.md)** – Structure of payloads prepared for the LLM.
- **[LLM refinement notes](test-files/examples/CoastSat-example/llm_refinement_plan.md)** – Open items and future enhancements.
- **Legacy development docs** under `docs/development/` and `docs/extension/` remain available for working directly on Stencila itself.

## Scripts

| Script | Purpose |
|--------|---------|
| `./scripts/start-dev.sh` | Build CLI & extension, open the extension workspace |
| `./scripts/quick-dev.sh` | Launch extension workspace (assumes artefacts already built) |
| `./scripts/dev.sh` | Bootstrap environment dependencies |
| `./scripts/build.sh` | Build all components |
| `./scripts/watch.sh` | Watch Rust + extension sources, rebuild automatically |
| `./scripts/run-cli.sh` | Run the repository CLI without modifying global `PATH` |

These scripts are inherited from the broader Stencila development environment and remain useful when tweaking prompts, CLI behaviour, or extension logic.

## Current Notes

- Targets Stencila 2.6.0 debug build (`stencila/target/debug/stencila`).
- Extension development mode automatically locates the repo build; see `docs/extension/HOW_DEV_MODE_WORKS.md`.
- Example currently focuses on CoastSat site `nzd0001`, but the approach generalises to other provenance-rich workflows.

## Further Reading

- [Stencila project](https://github.com/stencila/stencila)
- [RO-Crate specification](https://www.researchobject.org/ro-crate/)
- [CoastSat tools](https://github.com/kvos/coastsat)
