# Development Workflow Guide

This document describes the recommended workflow for developing and testing Stencila.

## Workflow Overview

```
┌─────────────────┐
│  Make Changes   │
│  in stencila/   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Run Tests      │
│  (Component)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  Tests Pass?    │ No   │  Fix Issues  │
└────────┬────────┘──────┘──────┬───────┘
         │ Yes                   │
         ▼                       │
┌─────────────────┐              │
│  Full Test      │              │
│  Suite          │◄─────────────┘
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Build & Verify │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Test CLI       │
└─────────────────┘
```

## Typical Development Session

### 1. Start the session

```bash
# Navigate to the repository root
cd /path/to/stencila_dev

# Optional: fetch latest changes
cd stencila
git pull

# Quick sanity check
./scripts/test-rust.sh
```

### 2. Make Your Changes

Edit files in `stencila/` directory. Common areas:

- **CLI changes**: `stencila/rust/cli/src/`
- **Format converters**: `stencila/rust/codecs/`
- **Kernels**: `stencila/rust/kernels/`
- **Schema**: `stencila/schema/`
- **SDKs**: `stencila/python/`, `stencila/node/`

### 3. Test Your Changes

**Quick iteration (recommended for active development):**

```bash
# For Rust changes
cd stencila/rust
cargo test --lib

# Or use watch mode for continuous testing
./scripts/watch.sh
```

**Full test suite (before committing):**

```bash
./scripts/test.sh
```

**Component-specific:**

```bash
./scripts/test-rust.sh
./scripts/test-node.sh
./scripts/test-python.sh
```

### 4. Build and Verify

```bash
# Build everything
./scripts/build.sh

# Or build specific component
cd stencila/rust
cargo build --bin stencila
```

### 5. Test the CLI

```bash
# Run a command
./scripts/run-cli.sh kernels list

# Or interactive
./scripts/run-cli.sh --help
```

### 6. Code Quality Checks

Before committing or sharing:

```bash
cd stencila
make fix      # Auto-fix formatting
make lint     # Check for issues
make audit    # Security audit
```

## Development Tips

### Using Watch Mode

For rapid iteration on Rust code:

```bash
./scripts/watch.sh
```

This will:
- Watch for file changes
- Automatically run tests
- Show results immediately

### Running Specific Tests

```bash
cd stencila/rust

# Run a specific test
cargo test test_name

# Run tests in a specific module
cargo test --lib codec_json

# Run with output
cargo test -- --nocapture
```

### Debugging

**Rust debugging:**

```bash
cd stencila/rust
cargo build --bin stencila
lldb target/debug/stencila
```

**Node.js debugging:**

```bash
cd stencila/node
npm run test:debug
```

### Profiling

```bash
cd stencila/rust
cargo build --release --bin stencila
./target/release/stencila --profile <command>
```

## Branching Strategy

If you're working on a feature:

```bash
cd stencila
git checkout -b feature/my-feature

# Make changes, test, etc.

# When ready to share
git commit -m "Add feature X"
git push origin feature/my-feature
```

## Testing Your Custom Experiments

Create test files in the `tests/` directory:

```bash
# Create a test
cat > tests/test_my_feature.sh << 'EOF'
#!/bin/bash
set -e
cd stencila
cargo run --bin stencila -- kernels list
EOF
chmod +x tests/test_my_feature.sh

# Run it
./tests/test_my_feature.sh
```

## Common Issues and Solutions

### Issue: Build fails with "linker not found"

**Solution:**
```bash
# On macOS, install Xcode Command Line Tools
xcode-select --install
```

### Issue: Tests fail after pulling changes

**Solution:**
```bash
cd stencila
make clean
make install
make test
```

### Issue: Rust version mismatch

**Solution:**
```bash
rustup update
cd stencila
# rust-toolchain.toml will ensure correct version
cargo build
```

### Issue: Node.js version mismatch

**Solution:**
Install `mise` (recommended) or use `nvm`:
```bash
# With mise
cd stencila
mise install

# Or with nvm
nvm use 22
```

## Performance Optimization

For faster builds:

1. **Use release mode for testing:**
   ```bash
   cargo test --release
   ```

2. **Use incremental compilation:**
   ```bash
   # Already enabled by default in dev mode
   ```

3. **Parallel builds:**
   ```bash
   # Set in ~/.cargo/config.toml
   [build]
   jobs = 8  # Adjust to your CPU cores
   ```

## Next Steps

- Read the main [README.md](./README.md) for more details
- Check [QUICKSTART.md](./QUICKSTART.md) for a fast setup
- Explore the codebase structure
- Join the community on [Discord](https://discord.gg/GADr6Jv)


