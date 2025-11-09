# Troubleshooting Guide

Common issues and solutions when developing with Stencila.

## Build Issues

### Build Fails

**Solutions:**
```bash
# Clean and rebuild
cd stencila
cargo clean
cargo build --bin stencila
```

### Extension Build Fails (Tailwind CSS v4 Conflict)

**Known Issue:** The extension build may fail with Tailwind CSS errors when building the web components. This is due to a version conflict:
- The `ghost` workspace requires Tailwind CSS v4
- The `web` workspace uses Tailwind CSS v3.4.17
- Parcel auto-installs v4 plugins which conflict with v3

**Impact:** This is **not critical** for development! The CLI works fine, and the extension will still function in development mode even if the web components fail to build. The extension continues to launch the repository CLI build automatically.

**Workaround:**
1. **Continue development** - The CLI build is what matters for most development work
2. **Extension still works** - Press F5 in the extension workspace to launch development mode
3. **Skip web build** - The extension will use the repository CLI even without web components built

**If you need the web components:**
```bash
# Try building just the extension TypeScript (skips web components)
cd stencila/vscode
npm run compile:ts

# Or manually work around the Tailwind issue
cd stencila/web
# Edit .postcssrc to use @tailwindcss/postcss if needed
npm run build:vscode
```

**Status:** This is a known issue with v2.6.0. The development workflow is designed to handle this gracefully.

### Extension Won't Compile (Other Issues)

**Solutions:**
```bash
# Install all workspace dependencies
cd stencila
npm install --legacy-peer-deps

# Build TypeScript types first
cd ts && npm run build

# Then try compiling extension
cd ../vscode && npm run compile
```

## Runtime Issues

### CLI Not Found

**Solutions:**
1. Verify CLI is built: `ls -la stencila/target/debug/stencila`
2. Rebuild: `cd stencila && cargo build --bin stencila`
3. Restart LSP server in development window

### Extension Not Using Local Build

**Solutions:**
1. Verify you're in development mode
2. Check Output panel for CLI path
3. Verify CLI at: `stencila/target/debug/stencila`
4. Restart LSP server

## Getting Help

- [Getting Started Guide](../getting-started/QUICKSTART.md)
- [Development Workflow](../development/DEVELOPMENT_WORKFLOW.md)
- [Extension Guide](../extension/VSCODE_EXTENSION.md)
- [Stencila Discord](https://discord.gg/GADr6Jv)
