#!/usr/bin/env python3
"""Replace TemplateDescribe prompt content with actual prompt transcripts.

This script scans rendered HTML files, extracts the full prompt text stored
on generator authors (in the `details` attribute), and replaces the
corresponding prompt-block content with a simple text code block containing
that transcript. It keeps the order of prompts, ensuring the `n`th prompt
block is paired with the `n`th generator transcript.
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path
from typing import List, Tuple

DETAILS_PATTERN = re.compile(
    r"details='Prompt sent to model:(.*?)'",
    re.DOTALL,
)
PROMPT_BLOCK_PATTERN = re.compile(
    r"(\s*<[^>]*InstructionBlock\.PromptBlock[^>]*>.*?)(?=<[^>]*InstructionBlock\.SuggestionBlock)",
    re.DOTALL,
)


def extract_prompts(source: str) -> List[str]:
    prompts: List[str] = []
    for match in DETAILS_PATTERN.finditer(source):
        prompt = html.unescape(match.group(1).strip())
        if prompt:
            prompts.append(prompt)
    return prompts


def extract_blocks(source: str) -> List[Tuple[str, Tuple[int, int]]]:
    blocks: List[Tuple[str, Tuple[int, int]]] = []
    for match in PROMPT_BLOCK_PATTERN.finditer(source):
        blocks.append((match.group(1), match.span(1)))
    return blocks


def make_code_block(prompt: str) -> str:
    escaped = html.escape(prompt, quote=True).replace("\n", "&#10;")
    return (
        "<stencila-code-block code='"
        + escaped
        + "' programming-language='text'></stencila-code-block>"
    )


def replace_content(source: str) -> Tuple[str, int]:
    prompts = extract_prompts(source)
    blocks = extract_blocks(source)

    if not prompts or not blocks:
        return source, 0

    count = min(len(prompts), len(blocks))
    if count == 0:
        return source, 0

    # Replace from the end to avoid messing up indices
    result = source
    for index in range(count - 1, -1, -1):
        _, span = blocks[index]
        prompt = prompts[index]
        replacement = make_code_block(prompt)
        start, end = span
        result = result[:start] + replacement + result[end:]

    return result, count


def process_file(path: Path, dry_run: bool = False) -> int:
    original = path.read_text(encoding="utf-8")
    modified, count = replace_content(original)
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
            action = "would update" if args.dry_run else "updated"
            print(f"{action} {count} prompt block(s) in {path}")
        else:
            print(f"No prompt blocks updated in {path}")

    if args.dry_run:
        print(f"Dry run complete. {total} prompt block(s) would be updated.")
    else:
        print(f"Processed {len(args.paths)} file(s); updated {total} prompt block(s).")


if __name__ == "__main__":
    main()
