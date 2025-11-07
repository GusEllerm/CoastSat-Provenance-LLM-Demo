# CoastSat Example

This directory contains an example using the CoastSat interface.crate for creating a larger .smd file example.

## Fetching the Interface Crate

The `fetch-interface-crate.sh` script downloads the latest `interface.crate` from the [CoastSat-interface.crate](https://github.com/GusEllerm/CoastSat-interface.crate) repository.

### Usage

Run the script from this directory:

```bash
./fetch-interface-crate.sh
```

The script will download `interface.crate` into the current directory, replacing any existing version.

### How It Works

The script attempts to fetch `interface.crate` using multiple methods (in order of preference):

1. **Release Assets**: Downloads `interface.crate` directly from the latest GitHub release assets if available
2. **Release Archive**: Extracts `interface.crate` from the latest release source code archive
3. **Repository Clone**: Falls back to cloning the repository and copying `interface.crate` from the main branch

### Requirements

- `curl` - for downloading files
- `git` - for cloning the repository (fallback method)
- `tar` - for extracting archives
- `python3` or `jq` (optional) - for better JSON parsing from GitHub API

### Notes

- The script automatically cleans up temporary files on exit
- If `interface.crate` exists as a file or directory, it will be replaced
- The script supports both file and directory formats for `interface.crate` (RO-Crate structure)

## Compiling the Example

The `compile_coastsat_llm.sh` script compiles the `coastsat_llm.smd` file using the Stencila pipeline.

### Usage

Run the script from this directory:

```bash
./compile_coastsat_llm.sh
```

The script performs the following steps:

1. **Convert** `coastsat_llm.smd` to `outputs/DNF.json`
2. **Render** `outputs/DNF.json` to `outputs/DNF_eval.json`
3. **Convert** `outputs/DNF_eval.json` to `outputs/render.html`

All output files are generated in the `outputs/` subdirectory.

### Requirements

- Local Stencila build at `stencila/target/debug/stencila`
- The script must be run from the `CoastSat-example` directory

