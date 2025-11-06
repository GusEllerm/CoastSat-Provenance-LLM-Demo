# Using Cursor to Develop and Test the Stencila Extension

Cursor is built on VS Code, so it supports the same extension development workflow. Here's how to set it up for testing your local Stencila CLI build.

## Quick Start

### 1. Open the Extension Workspace

Open the extension directory in Cursor:

```bash
cd /Users/eller/Projects/stencila_dev/stencila/vscode
cursor .
```

Or in Cursor: **File > Open Folder** → navigate to `stencila/vscode`

### 2. Install Dependencies

```bash
cd /Users/eller/Projects/stencila_dev/stencila/vscode
npm install
```

### 3. Build the Extension

```bash
npm run compile
```

This will:
- Compile TypeScript to JavaScript
- Build the web components
- Compile syntax files

### 4. Start Debugging

**Method 1: Keyboard Shortcut**
- Press **F5** (or **Cmd+F5** on Mac)
- A new Cursor window will open with the extension loaded in development mode

**Method 2: Run and Debug Panel**
- Press **Cmd+Shift+D** (or **Ctrl+Shift+D** on Windows/Linux)
- Click the green play button next to "Run Extension (Development)"
- Or click the dropdown and select "Run Extension (Development)"

**Method 3: Command Palette**
- Press **Cmd+Shift+P** (or **Ctrl+Shift+P**)
- Type "Debug: Start Debugging"
- Select "Run Extension (Development)"

### 5. Verify It's Working

In the **development window** (the new Cursor window that opened):

1. **Check the extension is loaded:**
   - Look for "Stencila" in the sidebar
   - Check the bottom status bar for Stencila indicators

2. **Open a test file:**
   - File > Open Folder → `/Users/eller/Projects/stencila_dev/test-files`
   - Open `examples/simple-article.smd`

3. **Verify it's using your local CLI:**
   - Command Palette (`Cmd+Shift+P`)
   - "Stencila: Stencila Shell"
   - Run `stencila --version` - should show 2.6.0 (your local build)

## Development Workflow

### Making Changes to the CLI

1. **Edit the CLI code:**
   ```bash
   # Edit files in stencila/rust/cli/
   ```

2. **Rebuild the CLI:**
   ```bash
   cd /Users/eller/Projects/stencila_dev/stencila
   cargo build --bin stencila
   ```

3. **Restart the LSP server** in the development window:
   - Command Palette (`Cmd+Shift+P`)
   - "Stencila: Restart Language Server"

### Making Changes to the Extension

1. **Edit extension code:**
   ```bash
   # Edit files in stencila/vscode/src/
   ```

2. **Rebuild the extension:**
   ```bash
   cd /Users/eller/Projects/stencila_dev/stencila/vscode
   npm run compile
   ```

3. **Reload the development window:**
   - Command Palette (`Cmd+Shift+P`)
   - "Developer: Reload Window"

### Watch Mode (Auto-rebuild)

For extension code, you can use watch mode:

```bash
cd /Users/eller/Projects/stencila_dev/stencila/vscode
npm run watch
```

This will automatically recompile TypeScript when you make changes.

## Debugging

### Extension Code Debugging

1. **Set breakpoints** in `src/` files
2. **Start debugging** (F5)
3. **Breakpoints will hit** when code executes in the development window

### CLI Debugging

To debug the CLI itself:

1. **Build with debug symbols** (already done in debug mode):
   ```bash
   cd stencila
   cargo build --bin stencila
   ```

2. **Use a debugger:**
   ```bash
   lldb target/debug/stencila
   ```

3. **Or check logs:**
   - View > Output
   - Select "Stencila" from dropdown
   - See LSP server logs

## Troubleshooting

### "Cannot find module" errors

Make sure you've compiled the extension:
```bash
cd stencila/vscode
npm run compile
```

### Extension not loading in development window

1. **Check the debug console** in the original Cursor window
2. **Look for errors** in the Output panel
3. **Verify extension is built:**
   ```bash
   ls -la stencila/vscode/out/extension.js
   ```

### CLI not found

1. **Verify local build exists:**
   ```bash
   ls -la stencila/target/debug/stencila
   ```

2. **Rebuild if needed:**
   ```bash
   cd stencila
   cargo build --bin stencila
   ```

3. **Check extension logs** in Output panel

### Development window not opening

1. **Check launch.json exists:**
   ```bash
   ls -la stencila/vscode/.vscode/launch.json
   ```

2. **If missing, create it** (should already be created by setup)

3. **Try restarting Cursor**

## Tips

- **Keep two windows open**: One for editing extension code, one for testing
- **Use the Output panel** to see extension logs
- **Restart LSP server** after CLI changes (faster than reloading window)
- **Use watch mode** for extension TypeScript changes

## Summary

The key steps:
1. Open `stencila/vscode` in Cursor
2. Press **F5** to launch development window
3. Test your changes in the development window
4. Rebuild CLI → Restart LSP for CLI changes
5. Rebuild extension → Reload window for extension changes

The development window will automatically use your local CLI build (`stencila/target/debug/stencila`)!

