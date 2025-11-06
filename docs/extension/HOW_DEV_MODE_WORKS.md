# How Extension Development Mode Finds Your Local CLI

## How It Works: Relative Path Resolution

When you launch the extension in development mode (F5), the extension automatically detects it's in development and uses a **relative path** to find your local CLI build.

## The Code

Looking at `stencila/vscode/src/cli.ts`, line 18:

```typescript
case vscode.ExtensionMode.Development:
case vscode.ExtensionMode.Test: {
  // In development, look for the debug binary
  const debugPath = path.join(__dirname, '..', '..', 'target', 'debug', 'stencila')
  if (fs.existsSync(debugPath)) {
    return debugPath
  } else {
    console.warn(`Debug binary not found at ${debugPath}, falling back to system path`)
    return 'stencila'
  }
}
```

## How It Works

### Path Resolution

1. **`__dirname`** = Where the compiled extension code lives
   - In development: `stencila/vscode/out/`
   - This is where the compiled JavaScript files are

2. **Go up two levels** (`..`, `..`):
   - `stencila/vscode/out/` → `stencila/vscode/` → `stencila/`

3. **Then look for**: `target/debug/stencila`
   - Final path: `stencila/target/debug/stencila`

### Visual Path

```
stencila/
├── vscode/
│   └── out/          ← __dirname (compiled extension code)
│       └── extension.js
│
└── target/
    └── debug/
        └── stencila   ← What it's looking for (../../target/debug/stencila)
```

## Why This Works

The extension code assumes a specific repository structure:
- Extension code is in `vscode/`
- Compiled extension is in `vscode/out/`
- CLI build is in `target/debug/` (relative to repo root)

When you run in development mode from `stencila/vscode/`, this relative path calculation finds your local build automatically!

## Verification

You can verify which CLI is being used:

1. **Check the Output panel** in the development window:
   - View > Output
   - Select "Stencila" from dropdown
   - Look for LSP server startup messages showing the CLI path

2. **Use the Stencila Shell**:
   - Command Palette → "Stencila: Stencila Shell"
   - Run `stencila --version`
   - Should show 2.7.0 (your local build)

3. **Check the code path**:
   ```bash
   # The extension looks for:
   stencila/target/debug/stencila
   
   # From vscode/out/:
   ../../target/debug/stencila
   ```

## What Happens If CLI Not Found

If the CLI binary doesn't exist at the expected path:
- The extension logs a warning: `Debug binary not found at ...`
- Falls back to using `stencila` from PATH (your global install)
- You'll see this in the Output panel

## Making Sure It Works

1. **Build the CLI**:
   ```bash
   cd stencila
   cargo build --bin stencila
   ```

2. **Verify the binary exists**:
   ```bash
   ls -la stencila/target/debug/stencila
   ```

3. **Restart the LSP server** in development window:
   - Command Palette → "Stencila: Restart Language Server"

## Summary

The extension uses **relative path resolution** from its compiled code location to find your local CLI build. This works because:
- No configuration needed
- Works automatically in development mode
- Finds your local build without any setup
- Falls back gracefully if not found

The path: `vscode/out/` → `../../target/debug/stencila` → `stencila/target/debug/stencila`

