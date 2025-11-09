# Test Change: Verifying the Development Build

## What We Changed

Added a temporary log message to the LSP server startup to verify that the Extension Development Host is running the repository build.

**File:** `stencila/rust/lsp/src/run.rs`
**Line:** After logging setup

**Change:**
```rust
// 🧪 DEVELOPMENT TEST: This log confirms the local build is being used
tracing::info!("🧪 Stencila LSP Server started - USING LOCAL DEVELOPMENT BUILD");
```

## How to Verify

1. **Rebuild the CLI** (if not already done):
   ```bash
   cd stencila
   cargo build --bin stencila
   ```

2. **In the Extension Development Host**:
   - Open the Output panel: View > Output
   - Select "Stencila" from the dropdown
   
3. **Restart the LSP server**:
   - Command Palette (`Cmd+Shift+P`)
   - "Stencila: Restart Language Server"

4. **Look for the test message**:
   ```
   🧪 Stencila LSP Server started - USING LOCAL DEVELOPMENT BUILD
   ```

## Interpreting the Result

- ✅ Message present → the extension is wiring through the repository build.
- ❌ Message absent → rebuild the CLI, restart the language server, check the Output panel for errors, and ensure `stencila/target/debug/stencila` exists.

## Reverting the Change

To remove this test log:

```rust
// Remove these lines from stencila/rust/lsp/src/run.rs:
// 🧪 DEVELOPMENT TEST: This log confirms the local build is being used
tracing::info!("🧪 Stencila LSP Server started - USING LOCAL DEVELOPMENT BUILD");
```

Then rebuild:
```bash
cd stencila
cargo build --bin stencila
```

