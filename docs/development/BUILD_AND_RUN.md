# Building and Running the Stencila CLI Locally

This guide summarizes the common ways to compile the CLI and exercise it during development.

## Quick Start

### Option 1: `cargo run` (recommended during development)

Automatically rebuilds as needed:

```bash
cd stencila
cargo run --bin stencila -- --help
cargo run --bin stencila -- kernels list
cargo run --bin stencila -- convert input.json output.yaml
```

### Option 2: Helper script

```bash
# From the repository root
./scripts/run-cli.sh --help
./scripts/run-cli.sh kernels list
./scripts/run-cli.sh convert input.json output.yaml
```

### Option 3: Execute the compiled binary

```bash
# Debug build (default)
./stencila/target/debug/stencila --help

# Release build (after running cargo build --release)
./stencila/target/release/stencila --help
```

## Building

```bash
cd stencila

# Debug build
cargo build --bin stencila

# Release build
cargo build --release --bin stencila
```

Compile artefacts land in `stencila/target/debug/` or `stencila/target/release/`.

## Iteration Workflow

1. Edit the CLI sources under `stencila/rust/cli/` (e.g. `src/main.rs`, `src/commands/`).
2. Rebuild with `cargo run --bin stencila -- --help` or `cargo build --bin stencila`.
3. Test specific commands as needed:

```bash
cargo run --bin stencila -- --version
cargo run --bin stencila -- kernels list
cargo run --bin stencila -- convert input.json output.yaml
```

## Optional Tools

- **cargo-watch** for automatic rebuilding:

  ```bash
  cargo install cargo-watch
  cd stencila/rust
  cargo watch -x 'run --bin stencila -- --help'
  ```

- **Scripted workflows**: see `scripts/watch.sh` for combined CLI + extension watch tasks.

## Troubleshooting

- **`Binary not found`**  
  Run `cargo build --bin stencila` to ensure the binary exists.

- **Resetting build artefacts**  
  `cargo clean && cargo build --bin stencila`

- **Comparing against a globally installed CLI**  
  Use `stencila --version` vs `./stencila/target/debug/stencila --version`, or diff help output with:

  ```bash
  diff <(stencila --help) <(./stencila/target/debug/stencila --help)
  ```

## Next Steps

- Continue iterating with `cargo run --bin stencila -- <command>`.
- Consult `docs/development/USING_LOCAL_BUILD.md` for guidance on switching between global and local installations.