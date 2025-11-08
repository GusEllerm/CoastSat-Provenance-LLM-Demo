# LLM File Attachments Plan

## Overview

Add first-class support for attaching local or remote files to Stencila LLM instructions such as `::: template_describe :::`. Users should be able to co-reference uploaded artefacts within prompts, and Stencila should adapt the payload sent to each backend (OpenAI GPT-5, Anthropic, Google, Ollama, etc.) while warning when a model cannot ingest the supplied artefacts. The feature must fit into existing execution flows (variable dereferencing, prompt rendering, model selection) and remain backwards compatible with documents that do not specify attachments.

## Current Behaviour

- Instruction blocks render the prompt, resolve kernel variables, then send `InstructionMessage.parts` (text and image/audio/video segments) through `prompts::execute_instruction_block`.
- Messages are generated from plain directive text; there is no schema field for attachments, and no attempt to read files from disk.

```166:211:stencila/rust/node-execute/src/instruction_block.rs
        let rendered_message = match message_utils::render_message_variables(&self.message, executor).await {
            Ok(rendered) => rendered,
            Err(error) => {
                tracing::warn!("Failed to render variables in message, using original: {}", error);
                self.message.clone()
            }
        };
```

- When tasks are sent to models we already have helpers for converting `schema::File` nodes into message parts, but they are only used for chat attachments.

```34:85:stencila/rust/node-execute/src/model_utils.rs
pub(super) fn file_to_message_part(file: &File) -> Option<MessagePart> {
    ...
}
```

## Proposed User Experience

Directive syntax:

```
::: template_describe [openai/gpt-5] [analysis: ./reports/summary.md, chart: ./plots/latest.png] 
Summarise the findings from analysis and explain what chart illustrates.
:::
```

- First bracket remains the model selector (or stays optional, exactly as today).
- Optional second bracket introduces a comma-separated list of `alias: path` pairs. Paths may be relative to the document directory or absolute; aliases become attachment labels exposed to the LLM.
- Prompt text continues to allow templating (`{{variable}}`) and can mention aliases in natural language.

## Document & Schema Updates

1. Extend the schema so instruction messages can carry attachments:
   - Add an optional `attachments: Option<Vec<File>>` (or similar) to `InstructionMessage`.
   - Mirror updates in generated bindings (`rust`, `ts`, `python`) via `schema-gen`.
   - Ensure encoding/decoding preserves attachments (Markdown, SMD, MyST, IPYNB).
2. Update Markdown codec parsing:
   - Split directive arguments into model selector + attachment list.
   - Parse attachment list into `File` placeholders (store alias + raw path, defer resolution until execution).
   - Extend re-encode logic so attachments render back to the `[alias: path]` list.
3. Decide how aliases surface in templates: expose them via a `instruction.attachments` context so `{{ instruction.attachments.analysis.name }}` is possible if desired.

## Runtime Handling

1. During execution (`InstructionBlock::execute`), resolve attachment paths:
   - Use the executor’s directory stack to join relative paths with the document directory.
   - Support HTTP(S) URLs via download-to-memory (respect size limits) or reject/emit warning initially.
   - Populate each `File` node with `name`, canonical `path`, inferred `media_type`, size, and content (text or base64).
2. Convert resolved files into additional `MessagePart`s before invoking `prompts::execute_instruction_block`:
   - Text-like formats → `MessagePart::Text` with a prefixed header (e.g. `Attachment: analysis\n\n<content>`).
   - Image/audio/video → reuse existing binary handling to produce `ImageObject` / `AudioObject` / `VideoObject`.
   - Preserve alias metadata so we can instruct the LLM (“Attachment `analysis`”).
3. Add guardrails:
   - Configurable max file size; emit execution message if exceeded.
   - Hash-based caching to avoid re-reading unchanged files on subsequent executions.
   - Clear warnings when attachments cannot be read or a model cannot accept them (and optionally fall back to embedding truncated text).

## Model Adapter Changes

- **OpenAI GPT-5 / GPT-4o**: migrate to the Responses API (supports text + file references). Upload attachments to `/v1/files`, include resulting file IDs in the request, and annotate user message with alias descriptions. Maintain compatibility with Chat Completions for models lacking file support.
- **OpenAI migration notes**:
  - Detect attachments in `ModelTask`; if present, switch from Chat Completions to the Responses API.
  - Upload each attachment via `POST /v1/files` (purpose `assistants`) and capture the returned `file_id`.
  - Build the `/v1/responses` payload using the existing message list plus one `input_file` / `input_image` entry per attachment (mapped by media type).
  - Restrict file uploads to attachment-capable models (e.g. `gpt-5` family); emit a clear warning when a user selects another OpenAI model with attachments.
  - Maintain the current Chat Completions flow when no attachments are present.
- **Anthropic Claude 3.5**: supports images/base64 but not arbitrary documents. Continue base64 images; for text/PDF attachments emit warning or convert to inline text under a size cap.
- **Google Gemini 2.0**: uses multi-part content; adapt adapter to send attachments via `Part::FileData` or fallback.
- **Ollama / local models**: many accept only plain text; degrade by concatenating attachment snippets with alias headings.
- Maintain a capabilities registry so we can short-circuit unsupported uploads and present actionable feedback to the user.

## CLI, UI, and Kernel Considerations

- CLI documentation (`docs/development/template_describe.md`, `docs/getting-started/QUICKSTART.md`) needs examples covering attachments and warnings about model compatibility.
- Web/VS Code editors should surface an attachments editor (optional follow-up): either autocomplete alias list or provide UI for choosing files when inserting a directive.
- Ensure execution in boxed kernels respects filesystem restrictions; attachments should only be read via the host, not via sandboxed kernels.

## Testing Strategy

- **Unit tests**: Markdown codec round-trips for directives with/without attachments; path resolution helper; file-to-message conversion.
- **Integration tests**: end-to-end execution using mocked model adapters verifying payload composition and warnings.
- **Provider stubs**: extend model crates with fake adapters to assert uploaded payload matches each API’s expectations.
- **Manual QA**: run `stencila render` on example docs with mixed attachments, verify outputs and warnings, test large-file rejection.

## Open Questions & Risks

- How to persist file IDs for providers (OpenAI) across executions to avoid repeated uploads—store in execution metadata?
- Attachment size limits differ; need configurable overrides per model.
- Security considerations for remote URLs and for storing temporary data (encryption, cleanup).
- Future extensibility: should we expose attachments to prompt templates via `include` or `{{ attach('alias') }}` helpers?


