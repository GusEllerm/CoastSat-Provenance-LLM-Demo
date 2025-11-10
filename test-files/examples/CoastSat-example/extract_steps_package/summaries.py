"""Summary and formatting helpers for CoastSat provenance data."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from textwrap import shorten
from typing import Any, Optional
from urllib.parse import urlparse

__all__ = [
    "make_markdown_link",
    "make_prompt_link",
    "limit_list",
    "links_from_details",
    "links_from_linked_entries",
    "normalise_language",
    "build_step_metadata_table",
    "build_notebook_summary",
    "build_notebook_table",
    "format_lineage_file",
    "build_lineage_targets",
    "format_samples",
    "summarise_io",
    "summarise_linked",
    "build_io_overview",
    "build_io_table",
]


def _to_uri(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    if urlparse(url).scheme in {"http", "https", "file"}:
        return url
    try:
        return Path(url).resolve().as_uri()
    except Exception:
        return url


def make_markdown_link(name: str | None, url: str | None) -> str:
    if not name:
        name = url or "(unknown)"
    uri = _to_uri(url)
    if uri:
        return f"[{name}]({uri})"
    return name or "(unknown)"


def make_prompt_link(name: str | None, url: str | None) -> str:
    if not name:
        name = url or "(unknown)"
    if url:
        parsed = urlparse(url)
        if parsed.scheme in {"http", "https"}:
            return f"[{name}]({url})"
    return name or "(unknown)"


def limit_list(values: list[str], limit: int, total_count: int | None = None) -> list[str]:
    if total_count is None:
        total_count = len(values)
    if limit <= 0 or len(values) <= limit:
        if total_count > len(values):
            values = values + [f"… (+{total_count - len(values)} more)"]
        return values
    trimmed = values[:limit]
    if total_count > limit:
        trimmed.append(f"… (+{total_count - limit} more)")
    return trimmed


def links_from_details(entries: list[dict[str, Any]] | None, limit: int = 5) -> list[str]:
    if not entries:
        return []
    links: list[str] = []
    seen: set[str] = set()
    total = 0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        url = entry.get("url") or entry.get("path")
        name = entry.get("name") or entry.get("id")
        total += 1
        link = make_markdown_link(name, url)
        if link in seen:
            continue
        seen.add(link)
        links.append(link)
    return limit_list(links, limit, total)


def links_from_linked_entries(entries: list[dict[str, Any]] | None, limit: int = 5) -> list[str]:
    if not entries:
        return []
    links: list[str] = []
    seen: set[str] = set()
    total_files = 0
    for entry in entries:
        files = entry.get("files") or []
        for file_entry in files:
            if not isinstance(file_entry, dict):
                continue
            total_files += 1
            url = file_entry.get("url") or file_entry.get("path")
            name = file_entry.get("name") or file_entry.get("id") or entry.get("parameter")
            link = make_markdown_link(name, url)
            if link in seen:
                continue
            seen.add(link)
            links.append(link)
    return limit_list(links, limit, total_files)


def normalise_language(language: Any) -> str:
    if isinstance(language, dict):
        return language.get("name") or language.get("@id") or language.get("value") or "Unknown"
    if isinstance(language, str):
        return language
    return "Unknown"


def build_step_metadata_table(step: dict[str, Any], stats: dict[str, Any]) -> dict[str, Any]:
    rows: OrderedDict[str, Any] = OrderedDict([
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

    def _fmt(value: Any) -> str:
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


def build_notebook_summary(notebook_crate: Optional[dict]) -> list[dict[str, Any]]:
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
        content = work.get("content")
        truncated = bool(work.get("content_truncated"))
        preview = ""
        if content is None and path:
            try:
                text = Path(path).read_text(encoding="utf-8", errors="ignore")
                content = text
            except Exception:
                content = None
        if isinstance(content, str) and content.strip():
            preview = shorten(content.strip(), width=200, placeholder="…")
        elif path:
            try:
                text = Path(path).read_text(encoding="utf-8", errors="ignore")
                preview = shorten(text.strip(), width=200, placeholder="…")
            except Exception:
                preview = ""
        entry["content"] = content
        entry["content_truncated"] = truncated
        entry["path"] = path
        entry["uri"] = _to_uri(path)
        entry["preview"] = preview
        summary.append(entry)
    return summary


def build_notebook_table(summary: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
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


def format_lineage_file(entry: dict[str, Any], default_label: str) -> dict[str, Any]:
    name = entry.get("name") or entry.get("id") or default_label
    web_url = entry.get("url")
    if not web_url:
        entry_id = entry.get("id")
        if isinstance(entry_id, str) and entry_id.startswith(("http://", "https://")):
            web_url = entry_id
    display_url = web_url or entry.get("path")
    link = make_markdown_link(name, display_url)
    prompt_link = make_prompt_link(name, web_url)
    return {
        "name": name,
        "link": link,
        "prompt_link": prompt_link,
        "path": entry.get("path"),
        "url": web_url,
        "encoding_format": entry.get("encodingFormat"),
        "content_size": entry.get("contentSize"),
        "sha256": entry.get("sha256"),
        "description": entry.get("description"),
    }


def build_lineage_targets(step: dict[str, Any], outputs_detail: list[dict[str, Any]], language: str, code_repo: Optional[str]) -> list[dict[str, Any]]:
    linked = step.get("linked_files") if isinstance(step.get("linked_files"), dict) else {}
    output_entries = linked.get("outputs") or []
    produced_by = {
        "name": step.get("name"),
        "id": step.get("@id"),
        "position": step.get("position"),
        "code_repository": code_repo,
        "language": language,
        "code_repository_markdown": make_markdown_link(step.get("name"), code_repo) if code_repo else None,
    }

    targets = []
    for entry in output_entries:
        files = entry.get("files") or []
        total_files = len(files)
        parameter_id = entry.get("parameter")
        detail = next((d for d in outputs_detail if d.get("id") == parameter_id), {})
        if total_files == 0 and not detail:
            continue

        context_lines = [
            f"Artefact parameter: {parameter_id}",
            f"Produced by workflow step {step.get('name')} ({step.get('@id')})",
            f"Total files in crate: {total_files}",
        ]

        metadata = {
            "name": detail.get("name"),
            "type": detail.get("type"),
            "encoding_format": detail.get("encodingFormat"),
            "description": detail.get("description"),
            "content_size": detail.get("contentSize"),
            "sha256": detail.get("sha256"),
            "link": make_markdown_link(detail.get("name"), detail.get("path") or detail.get("url")) if detail else None,
        }
        metadata = {key: value for key, value in metadata.items() if value}

        files_payload = []
        for file_info in files[:5]:
            if not isinstance(file_info, dict):
                continue
            files_payload.append(format_lineage_file(file_info, parameter_id))
        if files_payload:
            sample_files = [file_entry["link"] for file_entry in files_payload]
            context_lines.append("Example files: " + "; ".join(sample_files))

        remaining_files = max(total_files - len(files_payload), 0)

        targets.append(
            {
                "artefact": {
                    "parameter": parameter_id,
                    "summary": f"{parameter_id} ({total_files} files)",
                    "total_files": total_files,
                },
                "produced_by": {"step": produced_by},
                "metadata": metadata,
                "files": files_payload,
                "counts": {
                    "total_files": total_files,
                    "files_listed": len(files_payload),
                    "files_remaining": remaining_files,
                },
                "context_lines": context_lines,
            }
        )
        if len(targets) >= 2:
            break

    return targets


def format_samples(entries: Optional[list[Any]], limit: int = 3) -> list[str]:
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


def summarise_io(entries: Optional[list[Any]], label: str) -> tuple[str, list[str]]:
    entries = entries or []
    summary = f"{label} count: {len(entries)}"
    samples = format_samples(entries)
    if samples:
        summary += f"; examples: {', '.join(samples)}"
    return summary, samples


def summarise_linked(linked: Any, kind: str) -> tuple[str, int, int, list[str]]:
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


def build_io_overview(
    details: Optional[list[dict[str, Any]]],
    linked_entries: Optional[list[dict[str, Any]]],
    notebook_cells: Optional[list[dict[str, Any]]] = None,
) -> list[dict[str, Any]]:
    if not details:
        return []

    linked_map = {
        entry.get("parameter"): entry
        for entry in (linked_entries or [])
        if isinstance(entry, dict) and entry.get("parameter")
    }

    notebook_cells = notebook_cells or []
    overview: list[dict[str, Any]] = []
    for detail in details:
        if not isinstance(detail, dict):
            continue
        parameter_id = detail.get("id") or detail.get("@id") or "–"
        name = detail.get("name") or parameter_id or "(unnamed)"
        encoding_format = detail.get("encodingFormat") or "–"
        description = detail.get("description") or "–"

        web_url = detail.get("url")
        if not web_url:
            detail_id = detail.get("id") or detail.get("@id")
            if isinstance(detail_id, str) and detail_id.startswith(("http://", "https://")):
                web_url = detail_id
        source_url = web_url or detail.get("path")
        primary_link = make_markdown_link(name, source_url)
        prompt_link = make_prompt_link(name, web_url)

        linked_entry = linked_map.get(parameter_id) or {}
        files = linked_entry.get("files") or []
        sample_files = [
            format_lineage_file(file_info, parameter_id)
            for file_info in files[:5]
            if isinstance(file_info, dict)
        ]
        remaining_files = max(len(files) - len(sample_files), 0)

        prompt_example_links = [
            file_entry.get("prompt_link")
            for file_entry in sample_files
            if isinstance(file_entry.get("prompt_link"), str)
            and file_entry.get("prompt_link")
            and file_entry.get("prompt_link") != file_entry.get("name")
        ]

        if sample_files:
            file_links: list[str] = []
            for file_entry in sample_files:
                link_value = file_entry.get("link")
                if isinstance(link_value, str) and link_value:
                    file_links.append(link_value)
            files_annotation = "; ".join(file_links)
            if remaining_files:
                files_annotation += f"; … (+{remaining_files} more)"
            if files_annotation:
                files_annotation = "Examples: " + files_annotation
            else:
                files_annotation = f"{len(sample_files)} linked files." + (
                    f" (+{remaining_files} more)" if remaining_files else ""
                )
        else:
            files_annotation = "No linked files recorded."

        transient_note = None
        if len(files) == 0:
            transient_note = (
                "No linked files are referenced for this parameter; "
                "the crate may not capture intermediate artefacts."
            )
            files_annotation = "No linked files recorded (likely transient artefact)."

        cell_refs: list[str] = []
        search_terms = {parameter_id, name}
        for cell in notebook_cells:
            content = cell.get("content")
            if not isinstance(content, str) or not content:
                continue
            if any(term and term in content for term in search_terms):
                label = cell.get("name") or (
                    f"Code cell {cell.get('position')}" if cell.get("position") is not None else None
                )
                if label and label not in cell_refs:
                    cell_refs.append(label)

        overview.append(
            {
                "parameter": parameter_id,
                "name": name,
                "format": encoding_format,
                "description": description,
                "primary_link": primary_link,
                "prompt_link": prompt_link,
                "files_annotation": files_annotation,
                "total_files": len(files),
                "sample_files": sample_files,
                "prompt_example_links": prompt_example_links,
                "remaining_files": remaining_files,
                "transient_note": transient_note,
                "cell_refs": cell_refs,
            }
        )

    return overview


def build_io_table(entries: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not entries:
        return None
    columns = [
        {
            "type": "DatatableColumn",
            "name": "Parameter",
            "values": [entry.get("parameter") for entry in entries],
        },
        {
            "type": "DatatableColumn",
            "name": "Name",
            "values": [entry.get("name") for entry in entries],
        },
        {
            "type": "DatatableColumn",
            "name": "Format",
            "values": [entry.get("format") for entry in entries],
        },
        {
            "type": "DatatableColumn",
            "name": "Source",
            "values": [entry.get("primary_link") for entry in entries],
        },
        {
            "type": "DatatableColumn",
            "name": "Linked files",
            "values": [entry.get("files_annotation") for entry in entries],
        },
    ]
    return {"type": "Datatable", "columns": columns}
