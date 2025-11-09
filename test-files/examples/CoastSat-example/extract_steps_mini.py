#!/usr/bin/env python3
# coding: utf-8

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional
from collections import OrderedDict
from textwrap import shorten
from urllib.parse import urlparse

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
    candidates = []

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


def extract_steps(crate_dir: str | Path | ROCrate = "interface.crate", interface_id: str = "E2.2-wms") -> dict:
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


def _format_samples(entries, limit=3):
    entries = entries or []
    samples = []
    for entry in entries:
        if isinstance(entry, dict):
            name = entry.get("name") or entry.get("id")
            if not name:
                continue
            fmt = entry.get("encodingFormat")
            samples.append(f"{name} ({fmt})" if fmt else name)
            if len(samples) >= limit:
                break
        else:
            samples.append(str(entry))
            if len(samples) >= limit:
                break
    return samples


def _summarise_io(entries, label):
    entries = entries or []
    summary = f"{label} count: {len(entries)}"
    samples = _format_samples(entries)
    if samples:
        summary += f"; examples: {', '.join(samples)}"
    return summary, samples


def _summarise_linked(linked, kind):
    if not isinstance(linked, dict):
        return "", 0, 0, []

    param_entries = linked.get(kind) or []
    total_params = len(param_entries)
    total_files = sum(len(entry.get("files") or []) for entry in param_entries)

    if total_params == 0:
        return "", 0, 0, []

    examples = [
        f"{entry.get('parameter')} ({len(entry.get('files') or [])} files)"
        for entry in param_entries[:3]
    ]
    summary = (
        f"{kind.title()} linked parameters: {total_params}; "
        f"files referenced: {total_files}"
    )
    if examples:
        summary += f"; examples: {', '.join(examples)}"

    return summary, total_params, total_files, examples


def _to_uri(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    if urlparse(url).scheme in {"http", "https", "file"}:
        return url
    try:
        return Path(url).resolve().as_uri()
    except Exception:
        return url


def _make_markdown_link(name: str | None, url: str | None) -> str:
    if not name:
        name = url or "(unknown)"
    url = _to_uri(url)
    if url:
        return f"[{name}]({url})"
    return name or "(unknown)"


def _links_from_details(entries: list[dict[str, Any]] | None) -> list[str]:
    links = []
    if not entries:
        return links
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        url = entry.get("url") or entry.get("path")
        name = entry.get("name") or entry.get("id")
        links.append(_make_markdown_link(name, url))
    return links


def _links_from_linked_entries(entries: list[dict[str, Any]] | None) -> list[str]:
    links = []
    if not entries:
        return links
    for entry in entries:
        parameter = entry.get("parameter")
        for file_entry in entry.get("files") or []:
            if not isinstance(file_entry, dict):
                continue
            url = file_entry.get("url") or file_entry.get("path")
            name = file_entry.get("name") or file_entry.get("id") or parameter
            links.append(_make_markdown_link(name, url))
    return links


def _normalise_language(language):
    if isinstance(language, dict):
        return language.get("name") or language.get("@id") or language.get("value") or "Unknown"
    if isinstance(language, str):
        return language
    return "Unknown"


def _build_step_metadata_table(step, stats):
    rows = OrderedDict([
        ("Identifier", step.get("id")),
        ("Position", step.get("position")),
        ("Programming language", step.get("language")),
        ("Code repository", step.get("code_repository")),
        ("Inputs", stats["input_summary"]),
        ("Outputs", stats["output_summary"]),
        ("Linked inputs", stats["linked_input_summary"]),
        ("Linked outputs", stats["linked_output_summary"]),
    ])

    optional_fields = [
        ("Input links", stats.get("input_links_text")),
        ("Output links", stats.get("output_links_text")),
        ("Linked input links", stats.get("linked_input_links_text")),
        ("Linked output links", stats.get("linked_output_links_text")),
        ("Input examples", stats.get("input_examples_text")),
        ("Output examples", stats.get("output_examples_text")),
        ("Linked input examples", stats.get("linked_input_examples_text")),
        ("Linked output examples", stats.get("linked_output_examples_text")),
    ]
    for label, value in optional_fields:
        if value:
            rows[label] = value

    def _fmt(value):
        if value in (None, "", [], {}):
            return "–"
        if isinstance(value, (list, tuple)):
            return "<br />".join(str(item) for item in value if item)
        return str(value)

    columns = [
        {
            "type": "DatatableColumn",
            "name": "Field",
            "values": list(rows.keys()),
        },
        {
            "type": "DatatableColumn",
            "name": "Value",
            "values": [_fmt(value) for value in rows.values()],
        },
    ]
    return {"type": "Datatable", "columns": columns}


def _build_notebook_summary(notebook_crate: Optional[dict]) -> list[dict[str, Any]]:
    if not notebook_crate:
        return []
    summary = []
    for step in notebook_crate.get("steps", [])[:6]:
        entry: dict[str, Any] = {
            "position": step.get("position"),
            "name": step.get("name"),
        }
        work = step.get("workExample") or {}
        path = work.get("path")
        entry["path"] = path
        entry["uri"] = _to_uri(path)
        entry["id"] = work.get("@id") or step.get("id")
        preview = ""
        if path:
            try:
                content = Path(path).read_text(encoding="utf-8", errors="ignore")
                preview = shorten(content.strip(), width=200, placeholder="…")
            except Exception:
                preview = ""
        entry["preview"] = preview
        summary.append(entry)
    return summary


def _build_notebook_table(summary: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not summary:
        return None
    columns = [
        {
            "type": "DatatableColumn",
            "name": "Position",
            "values": [entry.get("position") for entry in summary],
        },
        {
            "type": "DatatableColumn",
            "name": "Name",
            "values": [entry.get("name") for entry in summary],
        },
        {
            "type": "DatatableColumn",
            "name": "Preview",
            "values": [entry.get("preview") for entry in summary],
        },
        {
            "type": "DatatableColumn",
            "name": "Path",
            "values": [entry.get("uri") or entry.get("path") for entry in summary],
        },
    ]
    return {"type": "Datatable", "columns": columns}


def _build_lineage_targets(step, outputs_detail):
    linked = step.get("linked_files") if isinstance(step.get("linked_files"), dict) else {}
    output_entries = linked.get("outputs") or []
    targets = []
    for entry in output_entries:
        files = entry.get("files") or []
        total_files = len(files)
        if total_files == 0 or total_files > 25:
            continue
        parameter_id = entry.get("parameter")
        detail = next((d for d in outputs_detail if d.get("id") == parameter_id), {})
        context_lines = [
            f"Artefact parameter: {parameter_id}",
            f"Produced by workflow step {step.get('name')} ({step.get('id')})",
            f"Total files in crate: {total_files}",
        ]
        if detail:
            metadata_parts = []
            if detail.get("name"):
                metadata_parts.append(f"name={detail.get('name')}")
            if detail.get("type"):
                metadata_parts.append(f"type={detail.get('type')}")
            if detail.get("encodingFormat"):
                metadata_parts.append(f"encodingFormat={detail.get('encodingFormat')}")
            if detail.get("sha256"):
                metadata_parts.append(f"sha256={detail.get('sha256')}")
            if metadata_parts:
                context_lines.append("Metadata: " + ", ".join(metadata_parts))
        sample_files = []
        for file_info in files[:3]:
            if not isinstance(file_info, dict):
                continue
            fname = file_info.get("name") or file_info.get("id")
            if not fname:
                continue
            size = file_info.get("contentSize")
            descriptor = f"{fname} (size {size})" if size else fname
            sample_files.append(descriptor)
        if sample_files:
            context_lines.append("Example files: " + "; ".join(sample_files))

        targets.append(
            {
                "parameter": parameter_id,
                "total_files": total_files,
                "summary": f"{parameter_id} ({total_files} files)",
                "context": "\n".join(context_lines),
            }
        )
        if len(targets) >= 2:
            break
    return targets


def _step_view(step: dict) -> dict:
    inputs_detail = step.get("inputs_detail")
    outputs_detail = step.get("outputs_detail")
    linked = step.get("linked_files")

    language = _normalise_language(step.get("programmingLanguage"))
    code_repo = step.get("codeRepository") or "Not specified"

    input_summary, input_samples = _summarise_io(inputs_detail, "Input parameters")
    output_summary, output_samples = _summarise_io(outputs_detail, "Output parameters")
    (
        linked_input_summary,
        linked_input_params,
        linked_input_files,
        linked_input_examples,
    ) = _summarise_linked(linked, "inputs")
    (
        linked_output_summary,
        linked_output_params,
        linked_output_files,
        linked_output_examples,
    ) = _summarise_linked(linked, "outputs")

    input_links = _links_from_details(inputs_detail)
    output_links = _links_from_details(outputs_detail)
    linked_input_links = _links_from_linked_entries(linked.get("inputs") if isinstance(linked, dict) else None)
    linked_output_links = _links_from_linked_entries(linked.get("outputs") if isinstance(linked, dict) else None)

    prompt_lines = [
        f"Step name: {step.get('name')}",
        f"Step identifier: {step.get('id')}",
        f"Workflow position: {step.get('position')}",
        f"Programming language: {language}",
        f"Code repository: {code_repo}",
        input_summary,
        output_summary,
    ]
    if input_links:
        prompt_lines.append("Input links: " + ", ".join(input_links[:5]))
    if output_links:
        prompt_lines.append("Output links: " + ", ".join(output_links[:5]))
    if linked_input_summary:
        prompt_lines.append(linked_input_summary)
    if linked_input_links:
        prompt_lines.append("Linked input artefacts: " + ", ".join(linked_input_links[:5]))
    if linked_output_summary:
        prompt_lines.append(linked_output_summary)
    if linked_output_links:
        prompt_lines.append("Linked output artefacts: " + ", ".join(linked_output_links[:5]))

    stats = {
        "input_summary": input_summary,
        "input_examples_text": ", ".join(input_samples),
        "output_summary": output_summary,
        "output_examples_text": ", ".join(output_samples),
        "linked_input_summary": linked_input_summary or "No linked input artefacts referenced.",
        "linked_input_examples_text": ", ".join(linked_input_examples),
        "linked_output_summary": linked_output_summary or "No linked output artefacts referenced.",
        "linked_output_examples_text": ", ".join(linked_output_examples),
        "input_parameter_count": len(step.get("input") or []),
        "output_parameter_count": len(step.get("output") or []),
        "linked_input_parameter_count": linked_input_params,
        "linked_input_file_count": linked_input_files,
        "linked_output_parameter_count": linked_output_params,
        "linked_output_file_count": linked_output_files,
        "input_links_text": ", ".join(input_links),
        "output_links_text": ", ".join(output_links),
        "linked_input_links_text": ", ".join(linked_input_links),
        "linked_output_links_text": ", ".join(linked_output_links),
    }

    notebook_summary = _build_notebook_summary(step.get("notebook_crate"))
    notebook_table = _build_notebook_table(notebook_summary)

    notebook_lines = []
    for cell in notebook_summary[:3]:
        label = cell.get("name") or f"Cell {cell.get('position')}"
        link = _make_markdown_link(label, cell.get("uri") or cell.get("path"))
        preview = cell.get("preview") or ""
        notebook_lines.append(f"{cell.get('position')}: {link} — {preview}")
    if notebook_lines:
        prompt_lines.append("Notebook cells: " + " | ".join(notebook_lines))

    lineage_targets = _build_lineage_targets(step, outputs_detail or [])
    for target in lineage_targets:
        prompt_lines.append("Output artefact: " + target["summary"])

    result = {
        "id": step["@id"],
        "types": list(step.get("@type", [])),
        "name": step.get("name"),
        "position": step["position"],
        "inputs": _normalize_ids(step.get("input", [])),
        "outputs": _normalize_ids(step.get("output", [])),
        "notebook": step["notebook"],
        "codeRepository": step.get("codeRepository"),
        "programmingLanguage": step.get("programmingLanguage"),
        "encodingFormat": step.get("encodingFormat"),
        "sha256": step.get("sha256"),
        "notebook_crate": _to_notebook_crate_model(step.get("notebook_crate")),
        "inputs_detail": inputs_detail,
        "outputs_detail": outputs_detail,
        "linked_files": linked,
        "raw": step,
        "language": language,
        "code_repository": code_repo,
        "stats": stats,
        "prompt_context": "\n".join(prompt_lines),
        "tables": {
            "metadata": _build_step_metadata_table(
                {
                    "id": step.get("@id"),
                    "position": step.get("position"),
                    "language": language,
                    "code_repository": code_repo,
                },
                stats,
            ),
        },
        "lineage_targets": lineage_targets,
        "notebook_summary": notebook_summary,
    }

    if notebook_table:
        result["tables"]["notebook_cells"] = notebook_table

    if input_links:
        result.setdefault("link_lists", {})["inputs"] = input_links
    if output_links:
        result.setdefault("link_lists", {})["outputs"] = output_links
    if linked_input_links:
        result.setdefault("link_lists", {})["linked_inputs"] = linked_input_links
    if linked_output_links:
        result.setdefault("link_lists", {})["linked_outputs"] = linked_output_links

    return result


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
