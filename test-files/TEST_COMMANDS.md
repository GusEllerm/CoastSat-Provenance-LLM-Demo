# Test Commands for Stencila CLI

Use these commands to test your local Stencila build with the files in this directory.

## Note

If you encounter an error about `--no-color` and `--force-color` flags, this is a known issue in the current build. Try setting `NO_COLOR=1` environment variable or using the `--no-color` flag explicitly.

## Document Conversion

### JSON to YAML
```bash
cd stencila
# If you get a color flag error, try:
NO_COLOR=1 cargo run --bin stencila -- convert ../test-files/inputs/simple-article.json ../test-files/outputs/simple-article.yaml

# Or use the --no-color flag if supported:
cargo run --bin stencila -- convert --no-color ../test-files/inputs/simple-article.json ../test-files/outputs/simple-article.yaml
```

### YAML to JSON
```bash
cd stencila
cargo run --bin stencila -- convert ../test-files/inputs/simple-article.yaml ../test-files/outputs/simple-article.json
```

### JSON to JSON5
```bash
cd stencila
cargo run --bin stencila -- convert ../test-files/inputs/simple-article.json ../test-files/outputs/simple-article.json5
```

### Check Format Support
```bash
cd stencila
cargo run --bin stencila -- convert --help
```

## Document Execution

### Execute a Document with Code
```bash
cd stencila
cargo run --bin stencila -- execute ../test-files/examples/article-with-code.smd
```

## Document Rendering

### Render to HTML
```bash
cd stencila
cargo run --bin stencila -- render ../test-files/examples/simple-article.smd --output ../test-files/outputs/simple-article.html
```

## Document Validation

### Lint a Document
```bash
cd stencila
cargo run --bin stencila -- lint ../test-files/examples/simple-article.smd
```

## Document Information

### Get Document Config
```bash
cd stencila
cargo run --bin stencila -- config ../test-files/examples/simple-article.smd
```

## Working with Kernels

### List Available Kernels
```bash
cd stencila
cargo run --bin stencila -- kernels list
```

### Check Kernel Status
```bash
cd stencila
cargo run --bin stencila -- kernels status
```

## Quick Test Script

You can also create a simple test script:

```bash
#!/bin/bash
cd stencila

echo "Testing JSON to YAML conversion..."
cargo run --bin stencila -- convert ../test-files/inputs/simple-article.json ../test-files/outputs/simple-article.yaml

echo "Testing YAML to JSON conversion..."
cargo run --bin stencila -- convert ../test-files/inputs/simple-article.yaml ../test-files/outputs/simple-article-converted.json

echo "Checking outputs..."
ls -lh ../test-files/outputs/
```

## Notes

- All output files are written to `outputs/` directory
- The `outputs/` directory is gitignored (see `.gitignore`)
- Use `inputs/` for source files you want to test
- Use `examples/` for complete example documents

