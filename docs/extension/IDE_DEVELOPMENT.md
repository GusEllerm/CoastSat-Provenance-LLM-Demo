# Developing the Extension in VS Code

These notes cover the standard workflow for iterating on the Stencila extension.

## Prerequisites

- Local repository checkout
- Node.js (for the extension bundle)
- Rust toolchain (for the CLI build)

## Quick Start

```bash
# 1. Open the extension workspace
cd stencila/vscode
code .

# 2. Install dependencies
npm install

# 3. Build the extension bundle
npm run compile
```

Launch the development host by pressing **F5** (or running “Run Extension” from the Run and Debug view). A new VS Code window opens with the extension bound to the repository build at `stencila/target/debug/stencila`.

## Everyday Loop

### Extension changes

```bash
cd stencila/vscode
npm run compile      # or npm run watch for incremental rebuilds
```

Reload the development window (Command Palette → “Developer: Reload Window”) to pick up the new bundle.

### CLI changes

```bash
cd stencila
cargo build --bin stencila
```

Restart the Stencila language server in the development window (Command Palette → “Stencila: Restart Language Server”) after rebuilding.

## Troubleshooting

- **Extension code not building**  
  Ensure `npm run compile` succeeds and that `stencila/vscode/out/extension.js` exists.

- **CLI binary missing**  
  Verify `stencila/target/debug/stencila` has been built. Re-run `cargo build --bin stencila` if needed.

- **Debug host not launching**  
  Check `.vscode/launch.json` inside `stencila/vscode` and retry F5.

## Tips

- Keep one window for editing the extension and the spawned debug window for testing.
- Use the Output panel (Stencila channel) for extension logs.
- Prefer watch mode during heavy TypeScript edits; it shortens the rebuild cycle.

