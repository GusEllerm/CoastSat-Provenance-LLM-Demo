# Quick Start Guide

Get up and running with Stencila development in 5 minutes.

## One-Command Start (Recommended)

**Just run this:**
```bash
./scripts/start-dev.sh
```

Then press **F5** in VS Code (or any VS Code–compatible IDE) and you're ready! 

See [Development Workflow](../development/DEVELOPMENT_WORKFLOW.md) for the full automated workflow.

---

## Manual Setup (Alternative)

## Step 1: Initial Setup (One-time)

Run the setup script to install all dependencies:

```bash
./scripts/setup.sh
```

This will:
- Install Rust development tools (cargo-audit, cargo-watch, etc.)
- Install all project dependencies (Rust, Node.js, Python)

⏱️ This may take 10-15 minutes on first run.

## Step 2: Build

Build the entire project:

```bash
./scripts/build.sh
```

Or build manually:
```bash
cd stencila
make build
```

## Step 3: Test

Run all tests to verify everything works:

```bash
./scripts/test.sh
```

Or run tests for specific components:
```bash
./scripts/test-rust.sh    # Rust only
./scripts/test-node.sh    # Node.js only
./scripts/test-python.sh  # Python only
```

## Step 4: Start Developing

### Make Changes

Edit files in the `stencila/` directory. For example:
- `stencila/rust/cli/src/main.rs` - CLI entry point
- `stencila/rust/cli/src/commands/` - CLI commands
- `stencila/rust/codecs/` - Format converters

### Test Your Changes

1. **Quick test** (Rust only):
   ```bash
   cd stencila/rust
   cargo test
   ```

2. **Full test suite**:
   ```bash
   ./scripts/test.sh
   ```

3. **Watch mode** (auto-test on file changes):
   ```bash
   ./scripts/watch.sh
   ```

### Run the CLI

Test your changes by running the CLI:

```bash
./scripts/run-cli.sh --help
./scripts/run-cli.sh kernels list
```

Or manually:
```bash
cd stencila
cargo run --bin stencila -- --help
```

## Common Workflows

### Iterative Development

1. Make a change in `stencila/`
2. Run `./scripts/test-rust.sh` (or the specific component)
3. If tests pass, run `./scripts/test.sh` for full suite
4. Repeat

### Debugging

For Rust debugging:
```bash
cd stencila/rust
cargo build --bin stencila
lldb target/debug/stencila
```

### Code Quality

Before committing:
```bash
cd stencila
make fix      # Auto-fix formatting/linting
make lint     # Check for issues
make audit    # Security audit
```

## Troubleshooting

### Build Fails

```bash
./scripts/clean.sh
./scripts/build.sh
```

### Tests Fail

```bash
cd stencila
make clean
make install
make test
```

### Need Help?

- Check the main [README.md](./README.md) for detailed documentation
- See [Stencila GitHub Issues](https://github.com/stencila/stencila/issues)
- Join [Stencila Discord](https://discord.gg/GADr6Jv)

## Next Steps

- Explore the codebase structure in `stencila/`
- Read component READMEs (e.g., `stencila/rust/README.md`)
- Check out examples in `stencila/examples/`
- Create your own tests in `tests/`


