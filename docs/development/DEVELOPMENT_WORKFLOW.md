# Automated Development Workflow

This guide shows you how to quickly start developing Stencila with everything automated.

## Quick Start (One Command)

From the project root, run:

```bash
./scripts/start-dev.sh
```

This will:
1. ✅ Build the Stencila CLI
2. ✅ Compile the VS Code extension
3. ✅ Open Cursor/VS Code with the extension workspace
4. Press **F5** to launch the development window!

## Daily Development Workflow

### First Time Setup (One Time)

```bash
# From project root
./scripts/dev.sh
```

This sets up everything. After that, you can use the quick start script.

### Starting Your Development Session

**Option 1: Full Setup (if you've made changes to dependencies)**
```bash
./scripts/start-dev.sh
```

**Option 2: Quick Start (if everything is already built)**
```bash
./scripts/quick-dev.sh
```

Then in Cursor/VS Code:
1. Press **F5** to launch development window
2. Open your test files in the development window

### Making Changes

#### CLI Changes

1. **Edit Rust code** in `stencila/rust/cli/`
2. **Rebuild:**
   ```bash
   cd stencila
   cargo build --bin stencila
   ```
3. **Restart LSP server** in development window:
   - Command Palette (`Cmd+Shift+P`)
   - "Stencila: Restart Language Server"

#### Extension Changes

1. **Edit TypeScript code** in `stencila/vscode/src/`
2. **Rebuild:**
   ```bash
   cd stencila/vscode
   npm run compile
   ```
3. **Reload window** in development window:
   - Command Palette (`Cmd+Shift+P`)
   - "Developer: Reload Window"

### Watch Mode (Auto-Rebuild)

For automatic rebuilding on file changes:

```bash
# Terminal 1: Watch CLI
cd stencila/rust
cargo watch -x 'build --bin stencila'

# Terminal 2: Watch Extension (optional)
cd stencila/vscode
npm run watch
```

Or use the combined watch script:
```bash
./scripts/watch.sh
```

Then just restart LSP server or reload window after changes are detected.

## Scripts Reference

### `./scripts/start-dev.sh`
**Full setup and launch** - Builds everything and opens the extension workspace.

**When to use:**
- Starting a new development session
- After pulling changes
- When dependencies have changed

### `./scripts/quick-dev.sh`
**Quick launch** - Just opens the extension workspace (assumes everything is built).

**When to use:**
- Starting a session when everything is already set up
- Just need to launch the dev window

### `./scripts/dev.sh`
**Setup only** - Builds everything but doesn't launch the IDE.

**When to use:**
- Just want to build/verify everything
- Part of CI or other automation

### `./scripts/watch.sh`
**Watch mode** - Automatically rebuilds CLI and extension on changes.

**When to use:**
- During active development
- Want automatic rebuilds

## Complete Workflow Example

```bash
# 1. Start development (one time per session)
cd /Users/eller/Projects/stencila_dev
./scripts/start-dev.sh

# 2. In Cursor/VS Code that opens:
#    - Press F5 to launch development window
#    - Open test-files/ in the development window

# 3. Make changes to CLI
vim stencila/rust/cli/src/main.rs
cd stencila && cargo build --bin stencila

# 4. In development window:
#    - Command Palette → "Stencila: Restart Language Server"
#    - Test your changes!

# 5. Make changes to extension
vim stencila/vscode/src/extension.ts
cd stencila/vscode && npm run compile

# 6. In development window:
#    - Command Palette → "Developer: Reload Window"
#    - Test your changes!
```

## Tips

1. **Keep the development window open** - It's your testing environment
2. **Use watch mode** during active development to save time
3. **Restart LSP server** (faster than reloading window) for CLI changes
4. **Reload window** (faster than restarting) for extension changes
5. **Check Output panel** in development window to see logs and errors

## Troubleshooting

### "Command not found" errors

Make sure scripts are executable:
```bash
chmod +x scripts/*.sh
```

### IDE doesn't open

Check if Cursor/VS Code is in your PATH:
```bash
which cursor  # or which code
```

If not, add it to your PATH or use the full path.

### Changes not reflecting

1. **CLI changes:** Rebuild → Restart LSP server
2. **Extension changes:** Rebuild → Reload window
3. **Check Output panel** for errors

### Watch mode not working

Install cargo-watch:
```bash
cargo install cargo-watch
```

## Summary

**One command to start:**
```bash
./scripts/start-dev.sh
```

**Then press F5** and you're ready to develop!

The development window will automatically use your local CLI build, so all your changes are immediately testable.

