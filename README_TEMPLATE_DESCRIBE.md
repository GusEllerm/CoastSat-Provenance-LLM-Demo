# Template Describe Instruction Type

## Overview

This document outlines the implementation plan for adding a new experimental instruction type `TemplateDescribe` (syntax: `::: template_describe :::`) to compartmentalize experimental features without affecting existing instruction types.

## Rationale

By creating a separate instruction type, we can:
- **Isolate experimental changes**: Test new features without breaking existing functionality
- **Maintain backward compatibility**: Existing `::: describe :::` blocks continue to work unchanged
- **Enable A/B testing**: Compare behavior between `describe` and `template_describe`
- **Gradual migration**: Eventually promote features from `template_describe` to `describe` once proven

## Implementation Plan

### Phase 1: Schema Definition

1. **Add to `stencila/schema/InstructionType.yaml`**
   ```yaml
   - const: TemplateDescribe
     "@id": stencila:TemplateDescribe
     description: |
       Experimental version of Describe that supports enhanced variable resolution
       and template features. Use this for testing new features before they are
       promoted to the standard Describe instruction type.
   ```

2. **Regenerate Schema**
   - Run schema generation (likely `cargo run` in `schema-gen` crate or similar)
   - This will update:
     - `rust/schema/src/types/instruction_type.rs`
     - `ts/src/types/InstructionType.ts`
     - `python/stencila_types/src/stencila_types/types.py`
     - JSON/JSON-LD schemas

### Phase 2: Markdown Parsing

3. **Update `rust/codec-markdown/src/decode/shared.rs`**
   - Add `"template_describe".value(InstructionType::TemplateDescribe)` to the parser
   - This enables parsing `::: template_describe :::` syntax

### Phase 3: Prompt Template

4. **Create Prompt Template**
   - Option A: Create `prompts/template_describe/block.smd` (new template)
   - Option B: Reuse `prompts/describe/block.smd` initially
   - The prompt template defines the system prompt sent to the LLM

### Phase 4: Execution Logic

5. **Add Special Handling (if needed)**
   - In `rust/node-execute/src/instruction_block.rs`, add conditional logic:
   ```rust
   match self.instruction_type {
       InstructionType::TemplateDescribe => {
           // Experimental features here
           // e.g., enhanced variable resolution, template processing, etc.
       }
       _ => {
           // Standard behavior
       }
   }
   ```

### Phase 5: Testing

6. **Test Cases**
   - Parse `::: template_describe :::` syntax
   - Verify prompt template selection
   - Test variable resolution (if enhanced)
   - Compare behavior with standard `::: describe :::`

## Example Usage

```markdown
```python exec
x = 4
y = "hello"
```

::: template_describe [openai/gpt-4] Describe these values: {{x}} and {{y}} :::
```

## Current Status

- [x] Schema definition added
- [x] Schema regenerated
- [x] Markdown parser updated
- [x] Prompt template created
- [x] Execution logic implemented (reuses Describe behavior)
- [x] Basic parsing test verified

## Implementation Complete ✅

The `template_describe` instruction type has been successfully implemented and is ready for testing. It currently behaves identically to `describe` but is isolated for experimental features.

### Bug Fixes
- **Encoding bug fixed**: Preserved underscore in `template_describe` when encoding back to markdown (was being converted to `templatedescribe`)

## Future Enhancements

Once `template_describe` is stable, features can be:
1. Promoted to standard `describe` instruction type
2. Kept as experimental for advanced users
3. Deprecated if not useful

## Files to Modify

1. `stencila/schema/InstructionType.yaml` - Add new enum variant
2. `stencila/rust/codec-markdown/src/decode/shared.rs` - Add parser
3. `stencila/prompts/template_describe/block.smd` - Create prompt template (optional)
4. `stencila/rust/node-execute/src/instruction_block.rs` - Add execution logic (if needed)

## Notes

- The schema generation process may require running a specific build command
- Prompt templates are stored in `prompts/` directory and embedded in the binary
- Instruction types are case-insensitive in parsing (due to `strum(ascii_case_insensitive)`)

