#!/usr/bin/env python3
"""Inject prompt transcripts into rendered HTML documents.

This script looks for generator authors with a `details` attribute starting
with "Prompt sent to model:" and inserts a visible note containing the
prompt text into the neighbouring content block. It can be run on one or
more HTML files and updates them in place.
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path
from typing import List, Tuple

MARKER = "Prompt sent to model:"
CONTENT_TAG = "<div slot=content>"
PROMPT_NOTE_PREFIX = "<stencila-note data-stencila-prompt=\"true\""


def extract_insert_positions(source: str) -> List[Tuple[int, str]]:
    """Find insertion points and associated prompt text.

    Returns a list of tuples containing the index in the original string where
    the note should be inserted and the raw prompt text for that location.
    """

    pattern = re.compile(r"details='" + re.escape(MARKER) + r"(.*?)'", re.DOTALL)
    positions: List[Tuple[int, str]] = []

    for match in pattern.finditer(source):
        raw_prompt = match.group(1)
        prompt = html.unescape(raw_prompt.strip())
        if not prompt:
            continue

        search_end = match.start()
        container_pos = source.rfind(CONTENT_TAG, 0, search_end)
        if container_pos == -1:
            continue

        insert_pos = container_pos + len(CONTENT_TAG)
        positions.append((insert_pos, prompt))

    return positions


def build_note(prompt: str) -> str:
    escaped = html.escape(prompt)
    note = (
        '\n<stencila-note data-stencila-prompt="true" note-type="info">'
        '<div slot="title"><stencila-text>Prompt sent to model</stencila-text></div>'
        '<div slot="content"><pre>'
        f"{escaped}"
        '</pre></div></stencila-note>\n'
    )
    return note


def inject_prompts(source: str) -> Tuple[str, int]:
    positions = extract_insert_positions(source)
    if not positions:
        return source, 0

    # Sort by insertion index so we can apply them sequentially
    positions.sort(key=lambda item: item[0])

    result = source
    offset = 0
    inserted = 0

    for insert_pos, prompt in positions:
        pos = insert_pos + offset
        # Skip if we've already added a note at this position
        if result.startswith(PROMPT_NOTE_PREFIX, pos):
            continue

        note = build_note(prompt)
        result = result[:pos] + note + result[pos:]
        offset += len(note)
        inserted += 1

    return result, inserted


def process_file(path: Path, dry_run: bool = False) -> int:
    original = path.read_text(encoding="utf-8")
    modified, count = inject_prompts(original)

    if count and not dry_run:
        path.write_text(modified, encoding="utf-8")

    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="HTML files to process")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing files")
    args = parser.parse_args()

    total = 0
    for name in args.paths:
        path = Path(name)
        if not path.exists():
            parser.error(f"File not found: {path}")
        count = process_file(path, dry_run=args.dry_run)
        total += count
        if count:
            action = "would insert" if args.dry_run else "inserted"
            print(f"{action} {count} prompt note(s) into {path}")
        else:
            print(f"No prompts found in {path}")

    if args.dry_run:
        print(f"Dry run complete. {total} prompt note(s) would be inserted.")
    else:
        print(f"Processed {len(args.paths)} file(s); inserted {total} prompt note(s).")


if __name__ == "__main__":
    main()
