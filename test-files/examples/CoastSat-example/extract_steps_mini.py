from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

from rocrate.model.contextentity import ContextEntity  # type: ignore[import]
from rocrate.rocrate import ROCrate  # type: ignore[import]

MAX_INLINE_BYTES = 20_000


def _normalize_ids(nodes):
    if isinstance(nodes, dict):
        nodes = [nodes]
    elif not isinstance(nodes, (list, tuple)):
        return []
    return [node["@id"] for node in nodes if isinstance(node, dict) and "@id" in node]


def _require_entity(crate: ROCrate, entity_id: str) -> ContextEntity:
    entity = crate.get(entity_id)
    if entity is None:
        raise KeyError(f"Missing entity '{entity_id}' in crate.")
    return entity


def _step_path(step: ContextEntity, crate_root: Path, step_id: str) -> Path:
    source = getattr(step, "source", None)
    path = crate_root.parent / source if source else crate_root / step_id
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"Notebook for '{step_id}' not found at {path}")
    return path


def _resolve_crate(crate_or_path: str | Path | ROCrate) -> tuple[ROCrate, Path]:
    if isinstance(crate_or_path, ROCrate):
        crate = crate_or_path
        source = getattr(crate, "source", None)
        if source is None:
            raise ValueError("Provided ROCrate instance does not expose a 'source' path.")
        crate_root = Path(source).resolve()
        if crate_root.is_file():
            crate_root = crate_root.parent
    else:
        crate_root = Path(crate_or_path).resolve()
        if not crate_root.is_dir():
            raise FileNotFoundError(f"Crate directory not found: {crate_root}")
        crate = ROCrate(str(crate_root))

    if not crate_root.exists():
        raise FileNotFoundError(f"Crate path does not exist: {crate_root}")

    return crate, crate_root


def _summarise_notebook(crate_root: Path, example_ref: dict) -> dict:
    crate_id = example_ref.get("@id")
    if not crate_id:
        raise ValueError("exampleOfWork is missing an '@id'.")

    crate_path = (crate_root / crate_id).resolve()
    if not crate_path.exists():
        raise FileNotFoundError(f"Notebook crate missing: {crate_path}")

    with crate_path.open("r", encoding="utf-8") as fh:
        graph = json.load(fh).get("@graph", [])

    entities = {entity.get("@id", str(i)): entity for i, entity in enumerate(graph)}
    dataset = entities.get("./", {})
    main_entity = entities.get(dataset.get("mainEntity", {}).get("@id", ""), {})

    steps = []
    for step_id in _normalize_ids(main_entity.get("step", [])):
        step = entities.get(step_id, {})
        position = step.get("position")
        try:
            position = int(position)
        except (TypeError, ValueError):
            pass

        work_example = step.get("workExample")
        if isinstance(work_example, dict):
            work_example_id = work_example.get("@id")
        elif isinstance(work_example, str):
            work_example_id = work_example
        else:
            work_example_id = None

        work_example_data = None
        if work_example_id:
            we_path = (crate_path.parent / work_example_id).resolve()
            if not we_path.exists():
                raise FileNotFoundError(
                    f"Work example '{work_example_id}' missing for notebook crate {crate_id}"
                )
            content = None
            truncated = False
            try:
                content_text = we_path.read_text(encoding="utf-8")
                encoded = content_text.encode("utf-8")
                if len(encoded) > MAX_INLINE_BYTES:
                    content = encoded[:MAX_INLINE_BYTES].decode("utf-8", errors="ignore")
                    truncated = True
                else:
                    content = content_text
            except Exception:
                content = None
            work_example_data = {
                "@id": work_example_id,
                "path": we_path.as_posix(),
                "content": content,
            }
            if truncated:
                work_example_data["content_truncated"] = True

        steps.append(
            {
                "@id": step.get("@id", step_id),
                "name": step.get("name"),
                "position": position,
                "workExample": work_example_data,
            }
        )

    steps.sort(key=lambda entry: (entry["position"] is None, entry["position"]))

    return {
        "path": crate_path.as_posix(),
        "dataset": {"@id": dataset.get("@id"), "name": dataset.get("name")},
        "main_entity": {
            "@id": main_entity.get("@id"),
            "name": main_entity.get("name"),
            "input": _normalize_ids(main_entity.get("input")),
            "output": _normalize_ids(main_entity.get("output")),
            "step_ids": _normalize_ids(main_entity.get("step")),
        },
        "steps": steps,
    }


def _build_step(crate: ROCrate, crate_root: Path, step_id: str) -> dict:
    step = _require_entity(crate, step_id)
    data = dict(step.properties())

    try:
        data["position"] = int(data["position"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Step '{step_id}' is missing a valid position.") from exc

    data["notebook"] = _step_path(step, crate_root, step_id).as_posix()

    example = data.get("exampleOfWork")
    if isinstance(example, dict):
        data["notebook_crate"] = _summarise_notebook(crate_root, example)

    return data


def extract_steps(crate_dir: str | Path | ROCrate = "interface.crate", interface_id: str = "E2.2-wms") -> dict:
    crate, crate_root = _resolve_crate(crate_dir)
    interface = _require_entity(crate, interface_id)

    has_part = interface.properties().get("hasPart")
    workflow_ids = _normalize_ids(has_part)
    if len(workflow_ids) != 1:
        raise ValueError(f"Expected a single workflow for '{interface_id}', got {workflow_ids!r}")

    workflow = _require_entity(crate, workflow_ids[0])
    step_refs = workflow.properties().get("step")
    if not step_refs:
        raise ValueError(f"Workflow '{workflow['@id']}' defines no steps.")

    step_ids = _normalize_ids(step_refs)
    steps = sorted(
        (_build_step(crate, crate_root, step_id) for step_id in step_ids),
        key=lambda entry: entry["position"],
    )

    return {step["@id"]: step for step in steps}


def _to_notebook_cell(cell: dict) -> dict:
    work_example = cell.get("workExample") or {}
    work_example_id = work_example.get("@id")
    work_example_path = work_example.get("path")
    content = work_example.get("content")
    truncated = bool(work_example.get("content_truncated"))
    if work_example_path and content is None and work_example_id:
        path_obj = Path(work_example_path)
        if path_obj.exists():
            try:
                text = path_obj.read_text(encoding="utf-8")
                encoded = text.encode("utf-8")
                if len(encoded) > MAX_INLINE_BYTES:
                    content = encoded[:MAX_INLINE_BYTES].decode("utf-8", errors="ignore")
                    truncated = True
                else:
                    content = text
            except Exception:
                content = None

    work_example_dict = None
    if work_example_id or work_example_path or content is not None:
        work_example_dict = {
            "@id": work_example_id,
            "path": work_example_path,
            "content": content,
        }
        if truncated:
            work_example_dict["content_truncated"] = True

    return {
        "id": cell.get("@id", ""),
        "name": cell.get("name"),
        "position": cell.get("position"),
        "workExample": work_example_dict,
    }


def _to_notebook_crate_model(data: Optional[dict]) -> Optional[dict]:
    if not data:
        return None

    dataset = data.get("dataset") or {}
    main = data.get("main_entity") or {}
    steps = [_to_notebook_cell(cell) for cell in data.get("steps", [])]

    return {
        "path": data.get("path"),
        "dataset": {"@id": dataset.get("@id"), "name": dataset.get("name")},
        "main_entity": {
            "@id": main.get("@id"),
            "name": main.get("name"),
            "input": list(main.get("input", [])),
            "output": list(main.get("output", [])),
            "step_ids": list(main.get("step_ids", [])),
        },
        "steps": steps,
    }


def _programming_language(step: dict) -> Optional[str]:
    value = step.get("programmingLanguage")
    if isinstance(value, dict):
        return value.get("@id") or value.get("name")
    if isinstance(value, str):
        return value
    return None


def _step_view(step: dict) -> dict:
    return {
        "id": step["@id"],
        "types": list(step.get("@type", [])),
        "name": step.get("name"),
        "position": step["position"],
        "inputs": _normalize_ids(step.get("input", [])),
        "outputs": _normalize_ids(step.get("output", [])),
        "notebook": step["notebook"],
        "codeRepository": step.get("codeRepository"),
        "programmingLanguage": _programming_language(step),
        "encodingFormat": step.get("encodingFormat"),
        "sha256": step.get("sha256"),
        "notebook_crate": _to_notebook_crate_model(step.get("notebook_crate")),
        "raw": step,
    }


def extract_step_dicts(
    crate_dir: str | Path | ROCrate = "interface.crate", interface_id: str = "E2.2-wms"
) -> list[dict]:
    step_map = extract_steps(crate_dir, interface_id)
    return [_step_view(step) for step in step_map.values()]


# Backwards compatibility alias
extract_step_models = extract_step_dicts


def main(arg: Any = None) -> dict:
    if isinstance(arg, list):
        crate_input = arg[1] if len(arg) > 1 else "interface.crate"
    elif arg is None:
        crate_input = "interface.crate"
    else:
        crate_input = arg

    steps = extract_steps(crate_input)
    if isinstance(arg, list) or (arg is None and __name__ == "__main__"):
        print(json.dumps(steps, indent=2))
    return steps


if __name__ == "__main__":
    main(sys.argv)
