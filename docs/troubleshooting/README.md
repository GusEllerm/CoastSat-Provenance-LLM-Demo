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

### Extension Won't Compile

**Solutions:**
```bash
# Install all workspace dependencies
cd stencila
npm install

# Build TypeScript types first
cd ts && npm run build

# Then compile extension
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
