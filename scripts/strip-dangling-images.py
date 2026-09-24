#!/usr/bin/env python3
"""Remove <img> tags in the built site whose target file does not exist.

Why this is needed: `datasummary_skim(output = "markdown")` asks modelsummary
for a Histogram column of inline sparklines. Current versions emit the <img>
tags but do not write the PNGs on the markdown output path, so those cells
would show a broken-image icon. Dropping the tag leaves an empty cell, which
is honest and unobtrusive.

The check is generic rather than special-cased, so it also catches any other
asset that goes missing between render and deploy.

Run from the repository root, after `quarto render`:

    python scripts/strip-dangling-images.py
"""
from __future__ import annotations

import os
import re
import sys
import urllib.parse

SITE = "_site"
IMG = re.compile(r'<img\b[^>]*?\bsrc\s*=\s*["\']([^"\']+)["\'][^>]*>', re.I)
EXTERNAL = re.compile(r"^(https?:|data:|//)", re.I)


def main() -> int:
    if not os.path.isdir(SITE):
        print(f"error: no {SITE}/ directory; run `quarto render` first", file=sys.stderr)
        return 1

    removed_total = 0
    pages_touched = 0

    for root, _dirs, files in os.walk(SITE):
        for fname in files:
            if not fname.endswith(".html"):
                continue
            path = os.path.join(root, fname)
            html = open(path, encoding="utf-8", errors="replace").read()

            removed: list[str] = []

            def drop(match: re.Match[str]) -> str:
                src = match.group(1).strip()
                if not src or EXTERNAL.match(src):
                    return match.group(0)
                target = urllib.parse.unquote(src.split("#")[0].split("?")[0])
                base = SITE if target.startswith("/") else root
                resolved = os.path.normpath(os.path.join(base, target.lstrip("/")))
                if os.path.exists(resolved):
                    return match.group(0)
                removed.append(src)
                return ""

            new_html = IMG.sub(drop, html)

            if removed:
                open(path, "w", encoding="utf-8", newline="").write(new_html)
                rel = os.path.relpath(path, SITE).replace(os.sep, "/")
                print(f"{rel}: dropped {len(removed)} dangling image(s)")
                removed_total += len(removed)
                pages_touched += 1

    if removed_total:
        print(f"\n{removed_total} dangling image reference(s) removed "
              f"across {pages_touched} page(s).")
    else:
        print("No dangling image references found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
