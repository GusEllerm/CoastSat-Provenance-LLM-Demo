# CoastSat Interface Workflow Helper

The `extract_steps.py` and `extract_steps_mini.py` scripts expose the workflow encoded in `interface.crate/ro-crate-metadata.json`. Both return the same Python data structure:

```python
steps: dict[str, dict[str, Any]]
```

Each **key** in the dictionary is the step identifier (matching the notebook or script filename, e.g. `tidal_correction-1.ipynb`). Each **value** is a dictionary containing metadata about that step.

## Top-Level Fields

For each `step_id, info`:

- `info["@id"]`: same as `step_id`.
- `info["@type"]`: RO-Crate `@type` list (e.g. `["File", "HowToStep", "SoftwareSourceCode"]`).
- `info["name"]`: human-readable name (usually the notebook filename).
- `info["position"]`: integer order within the workflow (0-based, contiguous).
- `info["input"]` / `info["output"]`: lists of formal parameter identifiers consumed/produced.
- `info["notebook"]`: absolute filesystem path to the notebook/script inside `interface.crate`.
- `info["exampleOfWork"]`: (optional) RO-Crate reference pointing at the nested notebook crate.
- `info["notebook_crate"]`: (optional) summary of the nested RO-Crate (present for notebooks; absent for `make_xlsx.py`).

## Nested Notebook Crate Summary

When present, `info["notebook_crate"]` is a dictionary with:

- `"path"`: absolute path to the notebook’s `ro-crate-metadata.json`.
- `"dataset"`: metadata for the notebook crate root dataset (`@id`, `name`).
- `"main_entity"`:
  - `"@id"` / `"name"`: identifier + label of the notebook entity.
  - `"input"` / `"output"`: lists of formal parameter identifiers.
  - `"step_ids"`: ordered list of code cell step identifiers (`#step-1`, …).
- `"steps"`: list of per-code-cell dictionaries, each containing:
  - `@id`: step identifier (`#step-n`).
  - `name`: e.g. `"Code cell 7"`.
  - `position`: integer order inside the notebook.
  - `workExample`: `{"@id": "<relative path>", "path": "<absolute path>"}` pointing to the extracted cell file.

These absolute paths let you open notebook cells or derived assets directly for debugging.

## Iteration Examples

### List workflow steps in order

```python
for step_id, metadata in steps.items():
    print(step_id, metadata["position"])
```

Because the dictionary is position-sorted before construction, iterating `.items()` maintains workflow order.

### Access notebook crate details

```python
for step_id, metadata in steps.items():
    crate = metadata.get("notebook_crate")
    if crate:
        print(f"{step_id} uses nested crate: {crate['path']}")
        for cell in crate["steps"]:
            print(" ", cell["position"], cell["workExample"]["path"])
```

### Retrieve formal parameters

```python
for step_id, metadata in steps.items():
    inputs = [param["@id"] for param in metadata.get("input", [])]
    outputs = [param["@id"] for param in metadata.get("output", [])]
    print(step_id, "inputs:", inputs, "outputs:", outputs)
```

### Convert to DataFrame

```python
import pandas as pd
rows = [{**metadata, "step_id": step_id} for step_id, metadata in steps.items()]
df = pd.DataFrame(rows)[["step_id", "position", "name", "notebook"]]
print(df)
```

### Full Flattening Helper

```python
import pandas as pd
from pandas import json_normalize


def steps_to_dataframe(steps: dict) -> pd.DataFrame:
    """
    Flatten the workflow structure into a single DataFrame.

    - Top-level step fields become columns.
    - Nested notebook crate metadata is expanded with `notebook_crate.` prefixes.
    - Per-cell data stays in the `notebook_crate.steps` column (list of dicts).
    """
    rows = [{"step_id": step_id, **metadata} for step_id, metadata in steps.items()]
    df = json_normalize(rows, sep=".", max_level=1)

    # Convenience fields for quick filtering
    if "notebook_crate" in df.columns:
        df["has_notebook_crate"] = df["notebook_crate"].notna()
    else:
        df["has_notebook_crate"] = False

    if "notebook" in df.columns:
        df.rename(columns={"notebook": "notebook_path"}, inplace=True)

    return df


# Usage
df_steps = steps_to_dataframe(steps)
print(df_steps[["step_id", "position", "name", "notebook_path", "has_notebook_crate"]])

# To drill into notebook cell metadata:
cells = df_steps.explode("notebook_crate.steps", ignore_index=True)
cell_details = json_normalize(
    cells.dropna(subset=["notebook_crate.steps"])["notebook_crate.steps"],
    sep="."
)
print(cell_details[["position", "workExample.path"]])
```

### Dictionary Views for Interoperability

Both scripts expose helpers that return workflow steps as plain dictionaries:

```python
from extract_steps import extract_workflow_step_dicts
# or, using the compact script:
# from extract_steps_mini import extract_step_dicts

step_dicts = extract_workflow_step_dicts("interface.crate")

for step in step_dicts:
    print(step["name"], "->", step["notebook"])
    crate = step.get("notebook_crate")
    if crate:
        for cell in crate["steps"]:
            print("   cell", cell["position"], "=>", cell["workExample"]["path"])
```

These dictionary-based views work cleanly inside Stencila templates (`{{step["name"]}}`) and remain JSON-serializable for downstream tooling.

Use this helper as a quick reference when working inside `.smd` notebooks or REPL sessions. Adjust paths as needed if your working directory differs (the scripts resolve absolute paths relative to the crate).

## Fields Returned by `extract_step_dicts`

Each entry in the list returned by `extract_workflow_step_dicts` / `extract_step_dicts` has the following structure:

- `id`: step identifier (e.g. `tidal_correction-1.ipynb`)
- `types`: list of RO-Crate `@type` values
- `name`: human-readable name (notebook or script filename)
- `position`: zero-based order in the workflow
- `inputs`: list of formal parameter identifiers consumed by the step
- `outputs`: list of formal parameter identifiers produced by the step
- `notebook`: absolute filesystem path to the notebook or script
- `codeRepository`: upstream repository URL (if defined)
- `programmingLanguage`: normalized language identifier/name (if present)
- `encodingFormat`: MIME-type-like string for the asset
- `sha256`: SHA-256 hash of the step artifact (if present)
- `notebook_crate`: nested dictionary (or `None`) summarizing the notebook’s RO-Crate:
  - `path`: absolute path to the nested `ro-crate-metadata.json`
  - `dataset`: `{"@id": ..., "name": ...}`
  - `main_entity`: `{"@id": ..., "name": ..., "input": [...], "output": [...], "step_ids": [...]}` 
  - `steps`: list of code-cell dictionaries, each with:
    - `id`: cell identifier (e.g. `#step-7`)
    - `name`: cell label (“Code cell 7”)
    - `position`: integer order inside the notebook
    - `workExample`: `{"@id": "<relative path>", "path": "<absolute path>", "content": "<inline text>", "content_truncated": true?}` or `None`
- `raw`: original metadata dictionary produced by `extract_workflow_steps`

These keys are safe to access inside Stencila templates (e.g. `{{step["position"]}}`, `{{step["notebook_crate"]["steps"][0]["workExample"]["path"]}}`).

> **Note:** the `content` field is limited to roughly 20 KB per cell to keep prompts small. When truncated, `content_truncated` is set to `True`.

