"""Prompt payload preparation for CoastSat provenance data."""

from __future__ import annotations

from typing import Any, Optional

from .summaries import (
    build_io_overview,
    build_io_table,
    build_step_metadata_table,
    normalise_language,
    summarise_io,
    summarise_linked,
)

__all__ = [
    "clean_prompt_value",
    "prepare_step_prompt_payloads",
    "summary_text",
    "param_brief",
]


def clean_prompt_value(value: Any) -> Any:
    if value in (None, "", "–"):
        return None
    return value


def summary_text(stats: Optional[dict[str, Any]], key: str) -> str:
    if not stats:
        return ""
    return stats.get(key, "")


def param_brief(entry: dict[str, Any], site_filter: Optional[str] = None) -> dict[str, Any]:
    sample_links = entry.get("prompt_example_links") or entry.get("linked_examples") or []
    if site_filter:
        filtered_links = [
            link for link in sample_links if isinstance(link, str) and site_filter in link
        ]
        if filtered_links:
            sample_links = filtered_links
    sample_links = sample_links[:1]
    return {
        "parameter": entry.get("parameter"),
        "name": entry.get("name"),
        "format": entry.get("format"),
        "description": entry.get("description"),
        "source_link": entry.get("prompt_link"),
        "sample_example": sample_links,
        "total_files": entry.get("total_files"),
        "transient_note": entry.get("transient_note"),
    }


def prepare_step_prompt_payloads(
    step: dict[str, Any],
    sequence: int,
    site_id: Optional[str],
) -> None:
    identity = {
        "name": step.get("name"),
        "position": step.get("position"),
        "language": step.get("language"),
        "code_repository": step.get("code_repository"),
        "step_number": sequence,
    }

    code_repo_url = identity.get("code_repository")
    step_name = identity.get("name")
    if code_repo_url and step_name:
        identity["code_repository_markdown"] = f"[{step_name}]({code_repo_url})"
    else:
        identity["code_repository_markdown"] = None

    link_lists = step.get("link_lists") or {}
    stats = step.get("stats") or {}

    data_flows = {
        "inputs": {
            "count": stats.get("input_parameter_count"),
            "summary": stats.get("input_summary"),
            "examples": stats.get("input_examples"),
            "links": link_lists.get("inputs"),
        },
        "outputs": {
            "count": stats.get("output_parameter_count"),
            "summary": stats.get("output_summary"),
            "examples": stats.get("output_examples"),
            "links": link_lists.get("outputs"),
        },
    }

    linked_artefacts = {
        "inputs": {
            "summary": stats.get("linked_input_summary"),
            "examples": stats.get("linked_input_examples"),
            "links": stats.get("linked_input_links"),
            "parameters": stats.get("linked_input_parameter_count"),
            "file_count": stats.get("linked_input_file_count"),
        },
        "outputs": {
            "summary": stats.get("linked_output_summary"),
            "examples": stats.get("linked_output_examples"),
            "links": stats.get("linked_output_links"),
            "parameters": stats.get("linked_output_parameter_count"),
            "file_count": stats.get("linked_output_file_count"),
        },
    }

    notebook_cells_all = step.get("notebook_cells") or []
    notebook_cells_with_content = [cell for cell in notebook_cells_all if cell.get("content")]
    max_cells = 10
    cells_for_prompt: list[dict[str, Any]] = []
    for cell in notebook_cells_with_content[:max_cells]:
        cell_name = cell.get("name") or f"Cell {cell.get('position')}"
        cells_for_prompt.append(
            {
                "name": cell_name,
                "position": cell.get("position"),
                "path": cell.get("path"),
                "uri": cell.get("uri"),
                "content": cell.get("content"),
                "content_truncated": cell.get("content_truncated"),
            }
        )

    notebook_context = {
        "summary": step.get("notebook_summary_text"),
        "total_cells": len(notebook_cells_all),
        "cells_included": len(cells_for_prompt),
        "additional_cells": max(0, len(notebook_cells_with_content) - len(cells_for_prompt)),
        "cells": cells_for_prompt,
        "available_cell_names": [
            cell.get("name") or f"Cell {cell.get('position')}" for cell in notebook_cells_all
        ],
    }

    context_lines = [line for line in (step.get("prompt_context") or "").splitlines() if line]

    def _build_param_payload(entry: dict[str, Any], kind: str) -> dict[str, Any]:
        sample_prompt_links = [
            link
            for link in (entry.get("prompt_example_links") or [])
            if isinstance(link, str) and link and link != entry.get("name")
        ]
        if site_id:
            site_filtered = [link for link in sample_prompt_links if site_id in link]
            if site_filtered:
                sample_prompt_links = site_filtered
        total_files = entry.get("total_files") or 0
        primary_example_links = sample_prompt_links[:1]

        if total_files:
            linked_note = f"{total_files} linked file{'s' if total_files != 1 else ''} referenced in the crate"
            if primary_example_links:
                linked_note += f"; representative example: {primary_example_links[0]}"
            else:
                linked_note += " (no public URLs)."
        else:
            linked_note = "No linked files recorded."

        cell_refs = [ref for ref in (entry.get("cell_refs") or []) if ref]
        cell_refs_text = ", ".join(cell_refs)
        cell_refs_note = (
            f"Notebook cells: {cell_refs_text}" if cell_refs_text else "Notebook cells: not documented."
        )

        return {
            "step": identity,
            "parameter": entry.get("parameter"),
            "name": entry.get("name"),
            "format": clean_prompt_value(entry.get("format")),
            "description": clean_prompt_value(entry.get("description")),
            "source_link": entry.get("prompt_link"),
            "linked_examples": primary_example_links,
            "total_linked_files": total_files,
            "linked_files_note": linked_note,
            "transient_note": entry.get("transient_note"),
            "context_lines": context_lines,
            "cell_refs": cell_refs,
            "cell_refs_text": cell_refs_text,
            "cell_refs_note": cell_refs_note,
            "kind": kind,
        }

    inputs_prompt_payload = [
        _build_param_payload(entry, "input")
        for entry in (step.get("inputs_overview") or [])
    ]
    outputs_prompt_payload = [
        _build_param_payload(entry, "output")
        for entry in (step.get("outputs_overview") or [])
    ]

    step["_sequence"] = sequence
    step["identity"] = identity
    step["jupyter"] = bool(notebook_cells_with_content)
    step["data_flows"] = data_flows
    step["linked_artefacts"] = linked_artefacts
    step["notebook_context"] = notebook_context
    step["context_lines"] = context_lines
    step["inputs_prompt_payload"] = inputs_prompt_payload
    step["outputs_prompt_payload"] = outputs_prompt_payload
    step["step_title_input"] = identity
    step["step_objective_input"] = {
        "identity": identity,
        "data_flows": data_flows,
        "linked_artefacts": linked_artefacts,
        "notebook": {"summary": notebook_context.get("summary")},
        "context_lines": context_lines,
        "inputs": step.get("inputs_overview"),
        "outputs": step.get("outputs_overview"),
    }
    step["step_operations_input"] = {
        "identity": identity,
        "data_flows": data_flows,
        "linked_artefacts": linked_artefacts,
        "notebook": notebook_context,
        "context_lines": context_lines,
        "inputs": step.get("inputs_overview"),
        "outputs": step.get("outputs_overview"),
    }

