#!/usr/bin/env python3
"""
new-plan.py — Create a numbered planning document in ./llore/.

Finds the next free sequence number, writes a Markdown file with YAML
front-matter, and prints the resulting path.

Usage:
    uv run python scripts/new-plan.py "My Plan Title"
    uv run python scripts/new-plan.py "My Plan Title" --tags perf,sqlite,pipeline
    uv run python scripts/new-plan.py "My Plan Title" --status approved

Output:
    llore/003-my-plan-title.md
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path


def _slugify(title: str) -> str:
    """Convert title to a filesystem-safe slug."""
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def _next_number(llore_dir: Path) -> int:
    """Return the next sequential document number (1-based)."""
    existing = sorted(llore_dir.glob("[0-9][0-9][0-9]-*.md"))
    if not existing:
        return 1
    last = existing[-1].name[:3]
    return int(last) + 1


FRONT_MATTER = """\
---
id: "{num:03d}"
title: "{title}"
date: "{date}"
status: "{status}"
tags: [{tags}]
---

# {title}

## Context

<!-- Why is this change being made? What problem does it solve? -->

## Changes

<!-- What will be done? List files, functions, and specific edits. -->

## Verification

<!-- How to confirm the change worked (tests, commands, checks). -->
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a new llore planning document."
    )
    parser.add_argument("title", help="Plan title (used in front-matter and filename)")
    parser.add_argument(
        "--tags",
        default="",
        help="Comma-separated list of tags (e.g. perf,sqlite,pipeline)",
    )
    parser.add_argument(
        "--status",
        default="proposed",
        choices=["proposed", "approved", "implemented", "rejected"],
        help="Initial status (default: proposed)",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    llore_dir = project_root / "llore"
    llore_dir.mkdir(exist_ok=True)

    num = _next_number(llore_dir)
    slug = _slugify(args.title)
    filename = f"{num:03d}-{slug}.md"
    path = llore_dir / filename

    if path.exists():
        print(f"ERROR: {path} already exists.", file=sys.stderr)
        sys.exit(1)

    tags = ", ".join(t.strip() for t in args.tags.split(",") if t.strip())
    content = FRONT_MATTER.format(
        num=num,
        title=args.title,
        date=date.today().isoformat(),
        status=args.status,
        tags=tags,
    )

    path.write_text(content, encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
