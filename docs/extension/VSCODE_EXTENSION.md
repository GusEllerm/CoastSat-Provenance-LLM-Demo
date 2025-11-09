# Using the Stencila VS Code Extension with a Local CLI Build

The extension talks to the Stencila CLI both for the language server (`stencila lsp`) and for document commands. When running from source in development mode it prefers the repository build at `stencila/target/debug/stencila`; otherwise it falls back to whatever `stencila` it finds on `PATH`, or to the bundled binary inside a packaged extension.

## Recommended Development Loop

```bash
cd stencila/vscode     # open the extension workspace
code .                 # or launch any VS Code–compatible IDE

npm install            # once per checkout
npm run compile        # build the extension bundle
F5                     # start “Run Extension” (Extension Development Host)
```

In the spawned Extension Development Host window:
- open a folder containing your test documents (e.g. `test-files/`)
- use the Command Palette → “Stencila: Stencila Shell” to confirm `stencila --version` points to the repository build

### When editing the extension

```bash
npm run compile        # rebuild, or `npm run watch` for incremental builds
```

Then reload the Extension Development Host (Command Palette → “Developer: Reload Window”).

### When editing the CLI

```bash
cd stencila
cargo build --bin stencila
```

Then restart the language server from the Extension Development Host (Command Palette → “Stencila: Restart Language Server”).

## Alternative Ways to Use a Local CLI

- **Package the extension with your CLI**  
  Copy `stencila/target/debug/stencila` into `stencila/vscode/cli/`, run `npm run package`, and install the resulting `.vsix`. The bundled binary will ship with the extension.

- **Symlink into the installed extension**  
  Create `~/.vscode/extensions/stencila.stencila-*/cli/stencila` as a symlink to the repository build. Useful for quick experiments but will be overwritten when the extension updates.

## Troubleshooting

- **Extension uses the wrong CLI**  
  Ensure you are running inside the Extension Development Host (title bar shows `[Extension Development Host]`) and that `stencila/target/debug/stencila` exists. Rebuild the CLI and restart the language server if needed.

- **Extension bundle missing**  
  Run `npm run compile` and verify `stencila/vscode/out/extension.js` was produced.

- **Extension host fails to launch**  
  Check `.vscode/launch.json` within `stencila/vscode` and retry F5.

The development host remains the most reliable way to exercise local CLI changes while iterating on extension code.

