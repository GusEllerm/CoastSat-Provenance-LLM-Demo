# Using Your Local Stencila Build

You have Stencila installed globally (`stencila 2.6.0` at `/usr/local/bin/stencila`), but you want to use your locally built version for development and testing.

## The Problem

When you run `stencila` in your terminal, it uses the globally installed version (2.6.0), not your local development build.

## Solutions

### Option 1: Use Full Path (Recommended for Testing)

Use the full path to your local build:

```bash
# Development build (faster compile, easier debugging)
./stencila/target/debug/stencila --help

# Or release build (optimized, slower compile)
./stencila/target/release/stencila --help
```

### Option 2: Use Cargo Run (Easiest for Development)

Use `cargo run` which automatically builds and runs:

```bash
cd stencila
cargo run --bin stencila -- --help
cargo run --bin stencila -- kernels list
```

Or use the helper script:
```bash
./scripts/run-cli.sh --help
./scripts/run-cli.sh kernels list
```

### Option 3: Create a Local Alias

Add to your `~/.zshrc` (or `~/.bashrc`):

```bash
# Local Stencila development
alias stencila-dev='cargo run --manifest-path ~/Projects/stencila_dev/stencila/Cargo.toml --bin stencila --'
```

Then use:
```bash
stencila-dev --help
```

### Option 4: Temporarily Override PATH

Create a wrapper script that adds the local build to PATH:

```bash
# Create a local bin directory
mkdir -p ~/Projects/stencila_dev/bin

# Create a symlink or wrapper
ln -s ~/Projects/stencila_dev/stencila/target/debug/stencila ~/Projects/stencila_dev/bin/stencila-dev

# Or add to PATH temporarily
export PATH="$HOME/Projects/stencila_dev/stencila/target/debug:$PATH"
stencila --version  # Will use local version
```

## Quick Reference

### Running Your Local Build

```bash
# Method 1: Direct path (after building)
./stencila/target/debug/stencila <command>

# Method 2: Cargo run (builds if needed)
cd stencila
cargo run --bin stencila -- <command>

# Method 3: Helper script
./scripts/run-cli.sh <command>
```

### Building Your Local Version

```bash
# Development build (faster, includes debug info)
cd stencila
cargo build --bin stencila

# Release build (optimized, slower compile)
cargo build --release --bin stencila
```

### Checking Which Version You're Using

```bash
# Global version
stencila --version  # => 2.6.0

# Local development version
./stencila/target/debug/stencila --version  # => 2.7.0 (or whatever you're building)

# Via cargo
cd stencila && cargo run --bin stencila -- --version
```

## Recommended Workflow

1. **For active development:**
   ```bash
   cd stencila
   cargo run --bin stencila -- <command>
   ```
   This automatically rebuilds if you've made changes.

2. **For testing specific functionality:**
   ```bash
   ./scripts/run-cli.sh kernels list
   ./scripts/run-cli.sh convert input.json output.yaml
   ```

3. **For release testing:**
   ```bash
   cd stencila
   cargo build --release --bin stencila
   ./target/release/stencila --version
   ```

## Example: Testing Your Changes

```bash
# 1. Make a change to the code
vim stencila/rust/cli/src/main.rs

# 2. Test your change (cargo will rebuild automatically)
cd stencila
cargo run --bin stencila -- --help

# 3. Compare with global version
stencila --help  # Global version
cargo run --bin stencila -- --help  # Your version with changes
```

## Troubleshooting

### "Command not found" when using local build

Make sure you've built it first:
```bash
cd stencila
cargo build --bin stencila
```

### Want to replace global version temporarily?

**Not recommended**, but if you want to test:
```bash
# Backup global version
cp /usr/local/bin/stencila /usr/local/bin/stencila.backup

# Replace with local build (USE WITH CAUTION)
sudo cp ./stencila/target/release/stencila /usr/local/bin/stencila

# Restore later
sudo cp /usr/local/bin/stencila.backup /usr/local/bin/stencila
```

**Better approach**: Use one of the methods above to avoid affecting your global installation.


