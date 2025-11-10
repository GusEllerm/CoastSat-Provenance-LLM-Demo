#!/usr/bin/env python3
# coding: utf-8

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

from .loader import (
    MAX_INLINE_BYTES,
    _build_example_index,
    _build_step,
    _clean_summary,
    _entity_path,
    _entity_summary,
    _load_crate_entities,
    _normalize_ids,
    _require_entity,
    _resolve_crate,
    _step_path,
    _summarise_notebook,
    extract_steps,
)
from .summaries import (
    build_io_overview as _build_io_overview,
    build_io_table as _build_io_table,
    build_lineage_targets as _build_lineage_targets,
    build_notebook_summary as _build_notebook_summary,
    build_notebook_table as _build_notebook_table,
    build_step_metadata_table as _build_step_metadata_table,
    links_from_details as _links_from_details,
    links_from_linked_entries as _links_from_linked_entries,
    make_markdown_link as _make_markdown_link,
    make_prompt_link as _make_prompt_link,
    normalise_language as _normalise_language,
    summarise_io as _summarise_io,
    summarise_linked as _summarise_linked,
)
from .prompts import (
    clean_prompt_value as _clean_prompt_value,
    param_brief as _param_brief,
    prepare_step_prompt_payloads as _prepare_step_prompt_payloads,
    summary_text as _summary_text,
)



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


def _step_view(step: dict) -> dict:
    inputs_detail = step.get("inputs_detail")
    outputs_detail = step.get("outputs_detail")
    linked = step.get("linked_files")

    language = _normalise_language(step.get("programmingLanguage"))
    code_repo = step.get("codeRepository") or None
    code_repo_display = code_repo or "Not specified"

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
        f"Code repository: {code_repo_display}",
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
        "input_examples": input_samples,
        "output_summary": output_summary,
        "output_examples_text": ", ".join(output_samples),
        "output_examples": output_samples,
        "linked_input_summary": linked_input_summary or "No linked input artefacts referenced.",
        "linked_input_examples_text": ", ".join(linked_input_examples),
        "linked_input_examples": linked_input_examples,
        "linked_output_summary": linked_output_summary or "No linked output artefacts referenced.",
        "linked_output_examples_text": ", ".join(linked_output_examples),
        "linked_output_examples": linked_output_examples,
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
        "input_links": input_links,
        "output_links": output_links,
        "linked_input_links": linked_input_links,
        "linked_output_links": linked_output_links,
    }

    notebook_summary = _build_notebook_summary(step.get("notebook_crate"))
    notebook_table = _build_notebook_table(notebook_summary)

    notebook_summary_text = ""
    if notebook_summary:
        summary_lines = []
        for cell in notebook_summary[:3]:
            label = cell.get("name") or f"Cell {cell.get('position')}"
            link = _make_markdown_link(label, cell.get("uri") or cell.get("path"))
            preview = cell.get("preview") or ""
            summary_lines.append(f"{cell.get('position')}: {link} — {preview}")
        notebook_summary_text = " | ".join(summary_lines)
        prompt_lines.append("Notebook cells: " + notebook_summary_text)

    inputs_overview = _build_io_overview(
        inputs_detail,
        linked.get("inputs") if isinstance(linked, dict) else None,
        notebook_summary,
    )
    outputs_overview = _build_io_overview(
        outputs_detail,
        linked.get("outputs") if isinstance(linked, dict) else None,
        notebook_summary,
    )

    lineage_targets = _build_lineage_targets(step, outputs_detail or [], language, code_repo)

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
        "inputs_overview": inputs_overview,
        "outputs_overview": outputs_overview,
        "linked_files": linked,
        "raw": step,
        "language": language,
        "code_repository": code_repo,
        "code_repository_display": code_repo_display,
        "stats": stats,
        "prompt_context": "\n".join(prompt_lines),
        "tables": {
            "metadata": _build_step_metadata_table(
                {
                    "id": step.get("@id"),
                    "position": step.get("position"),
                    "language": language,
                    "code_repository": code_repo_display,
                },
                stats,
            ),
        },
        "lineage_targets": lineage_targets,
        "notebook_summary": notebook_summary,
        "notebook_summary_text": notebook_summary_text,
    }

    inputs_table = _build_io_table(inputs_overview)
    if inputs_table:
        result["tables"]["inputs"] = inputs_table
    outputs_table = _build_io_table(outputs_overview)
    if outputs_table:
        result["tables"]["outputs"] = outputs_table

    if notebook_table:
        result["tables"]["notebook_cells"] = notebook_table
        result["notebook_cells"] = notebook_summary
    else:
        result["notebook_cells"] = []

    if input_links:
        result.setdefault("link_lists", {})["inputs"] = input_links
    if output_links:
        result.setdefault("link_lists", {})["outputs"] = output_links
    if linked_input_links:
        result.setdefault("link_lists", {})["linked_inputs"] = linked_input_links
    if linked_output_links:
        result.setdefault("link_lists", {})["linked_outputs"] = linked_output_links

    if "link_lists" not in result:
        result["link_lists"] = {}

    return result


def extract_step_dicts(
    crate_dir: str | Path | ROCrate = "interface.crate",
    interface_id: str = "E2.2-wms",
    site_id: Optional[str] = None,
) -> list[dict]:
    step_map = extract_steps(crate_dir, interface_id)
    steps = [_step_view(step) for step in step_map.values()]
    for sequence, step in enumerate(steps, start=1):
        _prepare_step_prompt_payloads(step, sequence, site_id)
    return steps


# Backwards compatibility alias
def extract_step_models(
    crate_dir: str | Path | ROCrate = "interface.crate",
    interface_id: str = "E2.2-wms",
    site_id: Optional[str] = None,
) -> list[dict]:
    return extract_step_dicts(crate_dir, interface_id, site_id)


def build_workflow_context(
    steps: list[dict[str, Any]],
    site_id: Optional[str] = None,
) -> dict[str, Any]:
    workflow_steps_summary: list[dict[str, Any]] = []
    workflow_outcomes: list[dict[str, Any]] = []

    for step_summary in steps:
        stats = step_summary.get("stats") or {}
        inputs = step_summary.get("inputs_overview") or []
        outputs = step_summary.get("outputs_overview") or []

        step_identity = {
            "name": step_summary.get("name"),
            "position": step_summary.get("position"),
            "language": step_summary.get("language"),
            "code_repository": step_summary.get("code_repository"),
        }
        if step_identity.get("code_repository") and step_identity.get("name"):
            step_identity["code_repository_markdown"] = (
                f"[{step_identity['name']}]({step_identity['code_repository']})"
            )
        else:
            step_identity["code_repository_markdown"] = None

        ordered_outputs: list[dict[str, Any]] = []
        for output in outputs:
            brief = _param_brief(output, site_id)
            ordered_outputs.append(brief)
            sample_link = brief["sample_example"][0] if brief["sample_example"] else None
            workflow_outcomes.append(
                {
                    "step_name": step_summary.get("name"),
                    "parameter": output.get("parameter"),
                    "name": output.get("name"),
                    "format": output.get("format"),
                    "description": output.get("description"),
                    "sample_link": sample_link,
                    "total_files": output.get("total_files"),
                    "transient_note": output.get("transient_note"),
                }
            )

        workflow_steps_summary.append(
            {
                "name": step_summary.get("name"),
                "position": step_summary.get("position"),
                "code_repository_markdown": step_identity.get("code_repository_markdown"),
                "language": step_summary.get("language"),
                "inputs_summary": _summary_text(stats, "input_summary"),
                "outputs_summary": _summary_text(stats, "output_summary"),
                "inputs": [_param_brief(entry, site_id) for entry in inputs[:3]],
                "outputs": ordered_outputs[:3],
            }
        )

    workflow_overview_input = {
        "site": site_id,
        "total_steps": len(steps),
        "steps": workflow_steps_summary,
    }

    workflow_diagram_input = {
        "steps": workflow_steps_summary,
        "step_order": [
            item.get("name")
            for item in sorted(
                workflow_steps_summary,
                key=lambda entry: entry.get("position", 0),
            )
        ],
    }

    workflow_outcomes_input = {
        "site": site_id,
        "outcomes": workflow_outcomes,
    }

    return {
        "overview": workflow_overview_input,
        "diagram": workflow_diagram_input,
        "outcomes": workflow_outcomes_input,
    }


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
