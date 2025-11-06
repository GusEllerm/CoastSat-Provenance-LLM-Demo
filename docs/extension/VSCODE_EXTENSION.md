# Using the Stencila VS Code Extension with Your Local Build

## How the Extension Finds the CLI

The Stencila VS Code extension uses the CLI in two ways:

1. **Language Server (LSP)**: The extension starts a Stencila LSP server using `stencila lsp` command
2. **Commands**: The extension runs various `stencila` commands for document operations

### CLI Discovery Logic

Looking at `stencila/vscode/src/cli.ts`, the extension finds the CLI based on its mode:

**Development/Test Mode** (when developing the extension):
- Looks for: `vscode/../../target/debug/stencila` (relative to extension location)
- This would be: `stencila/target/debug/stencila` if loaded from the repo
- Falls back to `stencila` on PATH if not found

**Production Mode** (installed extension):
- Looks for: `extension/cli/stencila` (bundled CLI in extension)
- Falls back to: `stencila` on PATH (your global install)

## Current Situation

You have:
- **Global Stencila**: 2.6.0 at `/usr/local/bin/stencila`
- **Local Build**: 2.6.0 at `./stencila/target/debug/stencila`
- **Installed Extension**: Likely using the global CLI (2.6.0)

## Options to Use Your Local Build

### Option 1: Load Extension in Development Mode (Recommended)

This is the best way to test your local changes with the extension:

1. **Open the extension workspace in Cursor:**
   ```bash
   cd /Users/eller/Projects/stencila_dev/stencila/vscode
   cursor .
   ```
   Or open Cursor and use File > Open Folder to navigate to `stencila/vscode`

2. **Install dependencies (if not already done):**
   ```bash
   npm install
   ```

3. **Build the extension:**
   ```bash
   npm run compile
   ```

4. **Start debugging in Cursor:**
   - Press **F5** (or Cmd+F5 on Mac)
   - Or go to Run and Debug panel (Cmd+Shift+D) and click "Run Extension (Development)"
   - This launches a new Cursor window with the extension in development mode

5. **In the development window**, the extension will automatically use:
   - `stencila/target/debug/stencila` (your local build)

**Benefits:**
- Automatically uses your local CLI build
- Changes to CLI are reflected immediately (after rebuilding CLI)
- Changes to extension code are reflected immediately (with hot reload)

### Option 2: Modify Extension to Use Local Build Path

If you want the installed extension to use your local build, you can modify the `cliPath` function:

1. **Find your installed extension:**
   ```bash
   # On macOS
   ~/.vscode/extensions/stencila.stencila-*/
   ```

2. **Edit the extension's `cli.ts`** (not recommended - will be overwritten on update)

3. **Or create a symlink:**
   ```bash
   # Create a symlink from extension's cli directory to your local build
   mkdir -p ~/.vscode/extensions/stencila.stencila-*/cli
   ln -s ~/Projects/stencila_dev/stencila/target/debug/stencila \
        ~/.vscode/extensions/stencila.stencila-*/cli/stencila
   ```

### Option 3: Override PATH (Temporary)

You can temporarily override the PATH for VS Code:

1. **Create a wrapper script:**
   ```bash
   # Create ~/.vscode-stencila.sh
   cat > ~/.vscode-stencila.sh << 'EOF'
   #!/bin/bash
   export PATH="$HOME/Projects/stencila_dev/stencila/target/debug:$PATH"
   exec /Applications/Visual\ Studio\ Code.app/Contents/MacOS/Electron "$@"
   EOF
   chmod +x ~/.vscode-stencila.sh
   ```

2. **Launch VS Code with the wrapper** (this is complex and not recommended)

### Option 4: Build and Install Extension with Your Local CLI

1. **Copy your local CLI to extension:**
   ```bash
   cd stencila/vscode
   mkdir -p cli
   cp ../target/debug/stencila cli/stencila
   ```

2. **Package and install the extension:**
   ```bash
   npm run package
   code --install-extension stencila-*.vsix --force
   ```

## Recommended Workflow

### For Active Development

1. **Keep Cursor open in the extension directory:**
   ```bash
   cd /Users/eller/Projects/stencila_dev/stencila/vscode
   cursor .
   ```

2. **Press F5** (or use Run and Debug panel) to launch extension in development mode

3. **Make changes to CLI:**
   ```bash
   cd /Users/eller/Projects/stencila_dev/stencila
   # Edit Rust code
   cargo build --bin stencila
   ```

4. **Restart the LSP server** in the development window:
   - Command Palette (`Cmd+Shift+P`)
   - "Stencila: Restart Language Server"

5. **Test your changes** in the development window

### For Testing with Your Documents

1. **Use the development window** (Option 1 above)

2. **Open your test files:**
   ```bash
   # In the development VS Code window
   File > Open Folder > /Users/eller/Projects/stencila_dev/test-files
   ```

3. **Test your changes** - the extension will use your local CLI build

## Verifying Which CLI is Being Used

### Check in Extension Output

1. Open the development VS Code window
2. View > Output
3. Select "Stencila" from the dropdown
4. Look for LSP server startup messages - they should show the CLI path

### Check via Extension Shell

The extension provides a "Stencila Shell" command that uses the same CLI:

1. Command Palette (`Cmd+Shift+P`)
2. "Stencila: Stencila Shell"
3. This opens a terminal with the CLI on PATH
4. Run `stencila --version` to see which version

## Troubleshooting

### Extension Not Using Local Build

1. **Check if you're in development mode:**
   - The window title should say "[Extension Development Host]"
   - If not, press F5 from the extension workspace

2. **Check if local build exists:**
   ```bash
   ls -la stencila/target/debug/stencila
   ```

3. **Rebuild the CLI:**
   ```bash
   cd stencila
   cargo build --bin stencila
   ```

4. **Restart the LSP server** in the extension

### Changes Not Reflecting

1. **Rebuild the CLI** after making changes:
   ```bash
   cd stencila
   cargo build --bin stencila
   ```

2. **Restart the LSP server:**
   - Command Palette → "Stencila: Restart Language Server"

3. **Reload the VS Code window:**
   - Command Palette → "Developer: Reload Window"

## Summary

**Best approach for development:**
- Use Option 1: Load extension in development mode (F5)
- This automatically uses your local CLI build
- Changes to CLI require: rebuild → restart LSP server
- Changes to extension require: rebuild → reload window

**Your installed extension** (from marketplace) will continue using the global CLI (2.6.0) unless you:
- Modify the extension code
- Use the symlink approach
- Package a custom extension

The development mode approach is the cleanest way to test your local changes!

