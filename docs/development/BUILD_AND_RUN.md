# Building and Running Your Local Stencila Build

## ✅ Current Status

Your local build is **working**! Here's what you have:

- **Global Stencila**: 2.6.0 (at `/usr/local/bin/stencila`)
- **Local Build**: 2.7.0 (at `./stencila/target/debug/stencila`)

## Quick Start

### Method 1: Using Cargo Run (Recommended for Development)

This automatically rebuilds if you make changes:

```bash
cd stencila
cargo run --bin stencila -- --help
cargo run --bin stencila -- kernels list
cargo run --bin stencila -- convert input.json output.yaml
```

### Method 2: Using the Helper Script

```bash
# From project root
./scripts/run-cli.sh --help
./scripts/run-cli.sh kernels list
./scripts/run-cli.sh convert input.json output.yaml
```

### Method 3: Direct Path (After Building)

```bash
# Development build (faster, easier to debug)
./stencila/target/debug/stencila --help
./stencila/target/debug/stencila kernels list

# Release build (optimized, slower compile)
./stencila/target/release/stencila --help
```

## Building

### Development Build (Default)

```bash
cd stencila
cargo build --bin stencila
```

Location: `target/debug/stencila`

### Release Build (Optimized)

```bash
cd stencila
cargo build --release --bin stencila
```

Location: `target/release/stencila`

**Note**: Release builds are slower to compile but run faster.

## Testing Your Changes

### 1. Make Changes

Edit files in `stencila/`, for example:
- `stencila/rust/cli/src/main.rs` - CLI entry point
- `stencila/rust/cli/src/commands/` - Individual commands

### 2. Test Your Changes

```bash
cd stencila

# Quick test - rebuild and run
cargo run --bin stencila -- --help

# Or test specific command
cargo run --bin stencila -- kernels list
```

### 3. Compare with Global Version

```bash
# Global version
stencila --version          # => 2.6.0
stencila kernels list

# Your local version
cargo run --bin stencila -- --version  # => 2.7.0
cargo run --bin stencila -- kernels list
```

## Testing Workflow

### Quick Iteration

```bash
cd stencila

# Make your changes
vim rust/cli/src/main.rs

# Test immediately (cargo rebuilds automatically)
cargo run --bin stencila -- --help
```

### Watch Mode (Auto-rebuild on Changes)

```bash
# Install cargo-watch if needed
cargo install cargo-watch

# Watch for changes and run tests
cd stencila/rust
cargo watch -x 'run --bin stencila -- --help'
```

## Common Commands to Test

```bash
cd stencila

# Version info
cargo run --bin stencila -- --version

# List kernels
cargo run --bin stencila -- kernels list

# Convert a document
cargo run --bin stencila -- convert input.json output.yaml

# Help for specific command
cargo run --bin stencila -- convert --help
```

## Example: Testing Format Conversion

```bash
cd stencila

# Create a test document
echo '{"type": "Article", "content": [{"type": "Paragraph", "content": ["Hello"]}]}' > test.json

# Convert using local build
cargo run --bin stencila -- convert test.json test.yaml

# Check the output
cat test.yaml
```

## Troubleshooting

### "Binary not found" Error

Make sure you've built it:
```bash
cd stencila
cargo build --bin stencila
```

### Want to Rebuild from Scratch

```bash
cd stencila
cargo clean
cargo build --bin stencila
```

### Check What Changed Between Global and Local

```bash
# Compare versions
stencila --version                              # Global: 2.6.0
./stencila/target/debug/stencila --version      # Local: 2.7.0

# Compare help output
diff <(stencila --help) <(./stencila/target/debug/stencila --help)
```

## Performance Tips

1. **For active development**: Use `cargo run` - it's smart about rebuilding
2. **For testing performance**: Use release build
3. **For debugging**: Use debug build (default)

## Next Steps

1. Make your modifications in `stencila/`
2. Test with `cargo run --bin stencila -- <command>`
3. Iterate and refine
4. See `USING_LOCAL_BUILD.md` for more details on managing global vs local versions

