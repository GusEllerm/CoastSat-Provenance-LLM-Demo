# Template Describe Instruction

## Overview

`TemplateDescribe` is an experimental instruction type (`::: template_describe :::`) that lets us iterate on enhanced variable resolution and templating features without affecting the stable `Describe` instruction.

Use it to:

- Isolate experimental behavior while keeping `Describe` unchanged
- A/B test new prompting strategies
- Migrate proven features into the standard instruction type later

## Implementation Plan

### Phase 1: Schema Definition

1. Update `stencila/schema/InstructionType.yaml`:
   ```yaml
   - const: TemplateDescribe
     "@id": stencila:TemplateDescribe
     description: |
       Experimental version of Describe that supports enhanced variable
       resolution and template features. Use this for testing new features
       before they are promoted to the standard Describe instruction type.
   ```
2. Regenerate the schema to refresh:
   - `rust/schema/src/types/instruction_type.rs`
   - `ts/src/types/InstructionType.ts`
   - `python/stencila_types/src/stencila_types/types.py`
   - JSON / JSON-LD schema artifacts

### Phase 2: Markdown Parsing

- Update `rust/codec-markdown/src/decode/shared.rs` to include `"template_describe".value(InstructionType::TemplateDescribe)`.

### Phase 3: Prompt Template

- Add `prompts/template_describe/block.smd`, or temporarily reuse `prompts/describe/block.smd`.

### Phase 4: Execution Logic

- In `rust/node-execute/src/instruction_block.rs` add handling for `InstructionType::TemplateDescribe`, e.g.:
  ```rust
  match self.instruction_type {
      InstructionType::TemplateDescribe => {
          // Experimental logic (enhanced variable resolution, templating, etc.)
      }
      _ => {
          // Standard behavior
      }
  }
  ```

### Phase 5: Testing

- Parse `::: template_describe :::` blocks
- Verify prompt template selection
- Test the enhanced variable resolution (if enabled)
- Compare behavior with the base `::: describe :::` flow

## Example Usage

```markdown
```python exec
x = 4
y = "hello"
```

::: template_describe [openai/gpt-4] Describe these values: {{x}} and {{y}} :::
```

## Status

- ✅ Schema updated and regenerated
- ✅ Markdown parser recognizes `template_describe`
- ✅ Prompt template available
- ✅ Execution logic leverages existing Describe behavior
- ✅ Basic parsing verified
- ✅ Encoding bug fixed (underscores preserved on re-encode)

## CLI Integration Review

### Summary

The CLI (`stencila compile`, `stencila render`) can execute `TemplateDescribe` blocks when explicitly enabled. Changes are opt-in, isolated, and backward compatible.

### Key Changes

1. **`CompileOptions`** (`stencila/rust/node-execute/src/lib.rs`)
   - Added `execute_template_describe: Option<bool>` (defaults to `None`)
   - Existing constructors and pattern matches remain valid thanks to struct update syntax

2. **`InstructionBlock::compile()`** (`stencila/rust/node-execute/src/instruction_block.rs`)
   - Executes `TemplateDescribe` blocks when `execute_template_describe == Some(true)`
   - Temporarily injects `execute_options` and resets them afterwards
   - Suppresses execution errors during compile to avoid breaking workflows

3. **CLI Commands** (`stencila/rust/cli/src/compile.rs`, `.../render.rs`)
   - Pass `execute_template_describe: Some(true)` so CLI runs the experimental blocks
   - Other entry points (IDE auto-compile, LSP, lint) keep default `None`

### Safety Notes

- Backward compatibility maintained: defaults keep current behavior
- Feature remains isolated to `TemplateDescribe`
- Normal workflows (IDE, LSP, linting) remain unchanged
- Compile-time execution suppresses errors, but a patch-path warning still needs follow-up

### Known Issue

`InstructionBlock::apply()` can log `Patch path for instruction is unexpectedly empty` when compile-time execution emits patches with empty paths. Options:

- Harden empty-path handling in `InstructionBlock::apply()`
- Ensure generated patches include valid paths
- Defer execution to the execute phase if the warning becomes disruptive

### Recommendations

- Investigate and resolve the patch-path warning
- Add regression tests covering CLI execution of `TemplateDescribe`
- Document the opt-in behavior for CLI users

