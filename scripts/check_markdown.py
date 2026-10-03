#!/usr/bin/env python3
"""Check local Markdown links against the current repository worktree."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\[([^\]\n]*)\]\((<[^>\n]+>|[^)\n]+)\)")


def prose(text: str) -> str:
    lines = []
    fence = None
    for line in text.splitlines():
        match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence is not None:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence):
                fence = None
            continue
        if match:
            fence = match[1]
            continue
        lines.append(line)
    return "\n".join(lines)


def anchors(text: str) -> set[str]:
    text = prose(text)
    result = set(re.findall(r'(?:id|name)=["\']([^"\']+)["\']', text))
    for heading in re.findall(r"^ {0,3}#{1,6}\s+(.+?)(?:\s+#+)?$", text, re.M):
        heading = LINK.sub(r"\1", heading)
        slug = "".join(c for c in heading.lower() if c.isalnum() or c in "_- ")
        slug = slug.replace(" ", "-")
        unique, number = slug, 0
        while unique in result:
            number += 1
            unique = f"{slug}-{number}"
        result.add(unique)
    return result


def files(root: Path) -> list[Path]:
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "--", "*.md"],
        cwd=root, text=True,
    ).splitlines()
    return sorted({root / name for name in names if (root / name).is_file()})


def check(path: Path, root: Path | None = None) -> list[str]:
    errors = []
    for _, destination in LINK.findall(prose(path.read_text(encoding="utf-8"))):
        if destination.startswith("<"):
            destination = destination[1:-1]
        else:
            destination = re.split(r'\s+["\']', destination, maxsplit=1)[0]
        if re.match(r"[A-Za-z][\w+.-]*:", destination) or destination.startswith("//"):
            continue
        relative, _, anchor = destination.partition("#")
        target = path.parent / unquote(relative) if relative else path
        if root is not None and not target.resolve().is_relative_to(root.resolve()):
            errors.append(f"path outside repository; use a source URL: {destination}")
        elif not target.exists():
            errors.append(f"missing path: {destination}")
        elif anchor and target.suffix.lower() == ".md":
            if unquote(anchor) not in anchors(target.read_text(encoding="utf-8")):
                errors.append(f"missing heading: {destination}")
    return errors


def main() -> int:
    documents = files(ROOT)
    errors = [f"{path.relative_to(ROOT)}: {error}" for path in documents for error in check(path, ROOT)]
    if errors:
        print("Markdown links failed:\n" + "\n".join(errors))
        return 1
    print(f"Markdown links: PASS ({len(documents)} documents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
