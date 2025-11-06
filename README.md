# Stencila Development Environment

A complete development setup for the [Stencila](https://github.com/stencila/stencila) project, allowing you to modify, build, and test custom versions of the software.

## Quick Start

**One command to get started:**

```bash
./scripts/start-dev.sh
```

Then press **F5** in Cursor/VS Code to launch the development window!

## Documentation

### Getting Started
- **[Quick Start Guide](docs/getting-started/QUICKSTART.md)** - Get up and running in 5 minutes
- **[Development Workflow](docs/development/DEVELOPMENT_WORKFLOW.md)** - Automated workflow guide

### Development
- **[Building and Running](docs/development/BUILD_AND_RUN.md)** - How to build and test your changes
- **[Using Local Build](docs/development/USING_LOCAL_BUILD.md)** - Managing global vs local versions
- **[Detailed Workflow](docs/development/workflow-detailed.md)** - Complete development workflow

### Extension Development
- **[VS Code Extension Guide](docs/extension/VSCODE_EXTENSION.md)** - Working with the extension
- **[Cursor Development](docs/extension/CURSOR_DEVELOPMENT.md)** - Cursor-specific setup
- **[How Dev Mode Works](docs/extension/HOW_DEV_MODE_WORKS.md)** - Understanding extension development mode

## Project Structure

```
stencila_dev/
├── README.md              # This file
├── docs/                  # Organized documentation
│   ├── getting-started/   # Quick start guides
│   ├── development/       # Development workflows
│   └── extension/         # Extension-specific guides
├── scripts/               # Helper scripts
│   ├── start-dev.sh      # One-command startup
│   ├── dev.sh            # Setup script
│   ├── build.sh          # Build everything
│   └── ...
├── stencila/             # Cloned Stencila repository
│   ├── rust/            # Core Rust implementation
│   ├── vscode/          # VS Code extension
│   └── ...
└── test-files/          # Test documents
    ├── inputs/         # Source files
    ├── examples/       # Example documents
    └── outputs/        # Generated files
```

## Available Scripts

| Script | Purpose |
|--------|---------|
| `./scripts/start-dev.sh` | **Start everything** - Builds and opens extension workspace |
| `./scripts/quick-dev.sh` | Quick launch (assumes everything is built) |
| `./scripts/dev.sh` | Setup only - Builds everything |
| `./scripts/build.sh` | Build the entire project |
| `./scripts/test.sh` | Run all tests |
| `./scripts/watch.sh` | Auto-rebuild on file changes |
| `./scripts/run-cli.sh` | Run local CLI build |

See [Development Workflow](docs/development/DEVELOPMENT_WORKFLOW.md) for details.

## Key Features

- ✅ **Automated Setup** - One command to get started
- ✅ **Local Build Support** - Test your CLI changes immediately
- ✅ **Extension Integration** - Use your local build with VS Code/Cursor extension
- ✅ **Test Files** - Ready-to-use test documents
- ✅ **Watch Mode** - Auto-rebuild on changes

## First Time Setup

1. **Clone and setup** (one-time):
   ```bash
   ./scripts/dev.sh
   ```

2. **Start developing**:
   ```bash
   ./scripts/start-dev.sh
   ```

3. **In Cursor/VS Code**:
   - Press **F5** to launch development window
   - Open `test-files/` in the development window
   - Start coding!

## Daily Workflow

```bash
# Start your session
./scripts/start-dev.sh

# Make changes to CLI
cd stencila
cargo build --bin stencila

# Restart LSP server in development window
# (Command Palette → "Stencila: Restart Language Server")

# Or use watch mode for auto-rebuild
./scripts/watch.sh
```

## Current Status

- **Global Stencila**: 2.6.0 (installed at `/usr/local/bin/stencila`)
- **Local Build**: 2.6.0 (at `stencila/target/debug/stencila`)
- **Extension**: Uses local build automatically in development mode
- **Note**: Working with v2.6.0 release (previous stable version)

## Need Help?

- Check [Getting Started](docs/getting-started/QUICKSTART.md) for quick reference
- See [Development Workflow](docs/development/DEVELOPMENT_WORKFLOW.md) for detailed workflows
- Review [Extension Guide](docs/extension/VSCODE_EXTENSION.md) for extension-specific help

## Resources

- [Stencila GitHub Repository](https://github.com/stencila/stencila)
- [Stencila Documentation](https://stencila.io/)
- [Stencila Discord](https://discord.gg/GADr6Jv)

## License

This development environment uses the Stencila repository which is licensed under Apache-2.0.
