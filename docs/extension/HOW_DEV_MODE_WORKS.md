# How Extension Development Mode Locates the Repository CLI

## How It Works: Relative Path Resolution

When the extension runs in development or test mode, it detects that status and resolves a **relative path** to the CLI built in the repository.

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

## Verification

To confirm which CLI was launched:

1. **Check the Output panel** in the development window:
   - View > Output
   - Select "Stencila" from dropdown
   - Look for LSP server startup messages showing the CLI path

2. **Use the Stencila Shell**:
   - Command Palette → "Stencila: Stencila Shell"
   - Run `stencila --version` and confirm it matches the repository build

3. **Check the code path**:
   ```bash
   # The extension looks for:
   stencila/target/debug/stencila
   
   # From vscode/out/:
   ../../target/debug/stencila
   ```

## What Happens If CLI Not Found

If the CLI binary doesn't exist at the expected path:
The extension logs a warning (`Debug binary not found at ...`) and falls back to whatever `stencila` is available on `PATH`. The Output panel records the message.

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

Extension development mode relies on relative path resolution from the compiled extension directory to `../../target/debug/stencila`. No extra configuration is needed, and the mechanism gracefully falls back to `stencila` on `PATH` if the repository build is missing.

