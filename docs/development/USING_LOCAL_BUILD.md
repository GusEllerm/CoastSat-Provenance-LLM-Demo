# Using a Local Stencila Build

Many contributors keep both a globally installed `stencila` binary and a repository build produced by `cargo`. This guide outlines common ways to run the local build without disturbing the global installation.

## Options for Running the Local CLI

### Use the compiled binary directly

```bash
# After building in debug mode
./stencila/target/debug/stencila --help

# After building with --release
./stencila/target/release/stencila --help
```

### Use `cargo run` (automatic rebuilds)

```bash
cd stencila
cargo run --bin stencila -- --help
cargo run --bin stencila -- kernels list
```

Helper wrapper:

```bash
./scripts/run-cli.sh kernels list
./scripts/run-cli.sh convert input.json output.yaml
```

### Define a shell alias (optional)

```bash
# Example: add to ~/.zshrc or ~/.bashrc
alias stencila-dev='cargo run --manifest-path /path/to/stencila/Cargo.toml --bin stencila --'

# Usage
stencila-dev --help
```

### Temporarily extend `PATH`

```bash
export PATH="/path/to/stencila/target/debug:$PATH"
stencila --version   # Invokes the repo build while the session is active
```

## Quick Reference

```bash
# Direct path (after building)
./stencila/target/debug/stencila <command>

# Cargo-managed
cd stencila && cargo run --bin stencila -- <command>

# Helper script
./scripts/run-cli.sh <command>
```

## Building the CLI

```bash
cd stencila
cargo build --bin stencila              # Debug build
cargo build --release --bin stencila    # Release build
```

Build artefacts appear in `stencila/target/debug/` or `stencila/target/release/`.

## Determining Which Binary Is Running

```bash
stencila --version                        # Global installation
./stencila/target/debug/stencila --version
cd stencila && cargo run --bin stencila -- --version
```

`diff <(stencila --help) <(./stencila/target/debug/stencila --help)` is also useful when comparing behaviour.

## Recommended Workflow

1. **Active development**
   ```bash
   cd stencila
   cargo run --bin stencila -- <command>
   ```
   `cargo` rebuilds only when source files change.

2. **Targeted testing**
   ```bash
   ./scripts/run-cli.sh kernels list
   ./scripts/run-cli.sh convert input.json output.yaml
   ```

3. **Release validation**
   ```bash
   cd stencila
   cargo build --release --bin stencila
   ./target/release/stencila --version
   ```

## Example Loop

```bash
# Edit sources
$EDITOR stencila/rust/cli/src/main.rs

# Rebuild and exercise the CLI
cd stencila
cargo run --bin stencila -- --help

# Compare with a global install if needed
stencila --help
```

## Troubleshooting

- **`stencila`: command not found**  
  Build the binary first: `cd stencila && cargo build --bin stencila`.

- **Need a clean rebuild**  
  `cargo clean && cargo build --bin stencila`

- **Temporarily replacing the global install**  
  Prefer the methods above; copying binaries into `/usr/local/bin` is risky unless intentionally testing an installation flow.
