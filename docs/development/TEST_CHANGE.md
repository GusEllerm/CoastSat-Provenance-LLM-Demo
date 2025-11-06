# Test Change: Verifying Local Build Works

## What We Changed

Added a simple log message to the LSP server startup to verify the extension is using your local build.

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

2. **In your development window** (Extension Development Host):
   - Open the Output panel: View > Output
   - Select "Stencila" from the dropdown
   
3. **Restart the LSP server**:
   - Command Palette (`Cmd+Shift+P`)
   - "Stencila: Restart Language Server"

4. **Look for the test message**:
   You should see:
   ```
   🧪 Stencila LSP Server started - USING LOCAL DEVELOPMENT BUILD
   ```

## If You See the Message

✅ **Success!** The extension is using your local build. Your changes will be reflected.

## If You Don't See the Message

❌ Check:
- Did you rebuild the CLI? (`cargo build --bin stencila`)
- Did you restart the LSP server?
- Check the Output panel for errors
- Verify the CLI exists: `ls -la stencila/target/debug/stencila`

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

