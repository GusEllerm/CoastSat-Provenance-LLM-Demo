"""Utilities for loading RO-Crate metadata for the CoastSat workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from rocrate.model.contextentity import ContextEntity  # type: ignore[import]
from rocrate.rocrate import ROCrate  # type: ignore[import]

MAX_INLINE_BYTES = 20_000

__all__ = [
    "MAX_INLINE_BYTES",
    "_normalize_ids",
    "_require_entity",
    "_step_path",
    "_resolve_crate",
    "_load_crate_entities",
    "_entity_path",
    "_clean_summary",
    "_entity_summary",
    "_build_example_index",
    "_summarise_notebook",
    "_build_step",
    "extract_steps",
]


def _normalize_ids(nodes: Any) -> list[str]:
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


def _load_crate_entities(crate_root: Path) -> dict[str, dict]:
    """Load the root RO-Crate metadata into a dictionary keyed by @id."""
    metadata_path = crate_root / "ro-crate-metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Root metadata not found at {metadata_path}")

    with metadata_path.open("r", encoding="utf-8") as fh:
        graph = json.load(fh).get("@graph", [])

    return {
        entity.get("@id", str(index)): entity
        for index, entity in enumerate(graph)
        if isinstance(entity, dict)
    }


def _entity_path(entity: dict, crate_root: Path) -> Optional[str]:
    entity_id = entity.get("@id")
    candidates: list[Path] = []

    source = entity.get("source") or getattr(entity, "source", None)
    if source:
        candidates.append(Path(source))

    content_url = entity.get("contentUrl") or entity.get("url")
    if isinstance(content_url, str) and not content_url.startswith(("http://", "https://")):
        candidates.append(crate_root / content_url)

    if isinstance(entity_id, str) and not entity_id.startswith(("http://", "https://", "#")):
        candidates.append(crate_root / entity_id)

    for candidate in candidates:
        try:
            resolved = Path(candidate).resolve()
        except OSError:
            continue
        if resolved.exists():
            return resolved.as_posix()

    return None


def _clean_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in summary.items() if value not in (None, "", [], {})}


def _entity_summary(entity: Optional[dict], crate_root: Path) -> dict[str, Any]:
    if not entity:
        return {}

    entity_id = entity.get("@id")
    summary = {
        "id": entity_id,
        "name": entity.get("name"),
        "type": entity.get("@type"),
        "description": entity.get("description"),
        "encodingFormat": entity.get("encodingFormat"),
        "sha256": entity.get("sha256"),
        "contentSize": entity.get("size") or entity.get("contentSize"),
        "url": entity.get("contentUrl") or entity.get("url"),
    }

    path = _entity_path(entity, crate_root)
    if path:
        summary["path"] = path

    return _clean_summary(summary)


def _build_example_index(entities: dict[str, dict], crate_root: Path) -> dict[str, list[dict[str, Any]]]:
    example_index: dict[str, list[dict[str, Any]]] = {}

    for entity in entities.values():
        example = entity.get("exampleOfWork")
        if not example:
            continue

        for example_id in _normalize_ids(example):
            example_index.setdefault(example_id, []).append(_entity_summary(entity, crate_root))

    return example_index


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


def _build_step(
    crate: ROCrate,
    crate_root: Path,
    step_id: str,
    entities: dict[str, dict],
    example_index: dict[str, list[dict[str, Any]]],
) -> dict:
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

    input_ids = _normalize_ids(data.get("input", []))
    output_ids = _normalize_ids(data.get("output", []))

    data["inputs_detail"] = [
        _entity_summary(entities.get(entity_id), crate_root) | {"id": entity_id}
        for entity_id in input_ids
    ]
    data["outputs_detail"] = [
        _entity_summary(entities.get(entity_id), crate_root) | {"id": entity_id}
        for entity_id in output_ids
    ]

    def _links_for(ids: list[str]) -> list[dict[str, Any]]:
        links = []
        for entity_id in ids:
            files = example_index.get(entity_id, [])
            if files:
                links.append({"parameter": entity_id, "files": files})
        return links

    linked_inputs = _links_for(input_ids)
    linked_outputs = _links_for(output_ids)
    data["linked_files"] = {}
    if linked_inputs:
        data["linked_files"]["inputs"] = linked_inputs
    if linked_outputs:
        data["linked_files"]["outputs"] = linked_outputs
    if not data["linked_files"]:
        data["linked_files"] = []

    return data


def extract_steps(
    crate_dir: str | Path | ROCrate = "interface.crate",
    interface_id: str = "E2.2-wms",
) -> dict:
    crate, crate_root = _resolve_crate(crate_dir)
    interface = _require_entity(crate, interface_id)

    entities = _load_crate_entities(crate_root)
    example_index = _build_example_index(entities, crate_root)

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
        (
            _build_step(
                crate,
                crate_root,
                step_id,
                entities,
                example_index,
            )
            for step_id in step_ids
        ),
        key=lambda entry: entry["position"],
    )

    return {step["@id"]: step for step in steps}
