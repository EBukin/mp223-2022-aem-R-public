#!/usr/bin/env python3
"""Rebuild the downloadable project bundles from the ae/ source folders.

The bundles committed in 2022 had drifted from the folders they were made from:
some carried megabytes of .Rproj.user session cache, ae03 shipped a stale
filename and omitted the solutions file, and ae03-data-wrangling-hw had no
bundle at all. Generating them from the folders keeps the two in step.

Run from the repository root:

    python scripts/build-bundles.py
"""
from __future__ import annotations

import os
import sys
import zipfile

AE_DIR = "ae"

# RStudio session state and OS cruft: never useful to a student, and it is what
# made the old bundles 100x larger than they needed to be.
EXCLUDE_DIRS = {
    ".Rproj.user", ".git", ".quarto", "renv", "__pycache__",
    # Written by tinytable (via modelsummary) at render time, not source.
    "tinytable_assets",
}
EXCLUDE_NAMES = {".Rhistory", ".RData", ".Ruserdata", ".DS_Store", "Thumbs.db"}
EXCLUDE_SUFFIXES = (".html", ".zip")
EXCLUDE_DIR_SUFFIXES = ("_files", "_cache")


def should_skip_dir(name: str) -> bool:
    return name in EXCLUDE_DIRS or name.endswith(EXCLUDE_DIR_SUFFIXES)


def should_skip_file(name: str) -> bool:
    return name in EXCLUDE_NAMES or name.endswith(EXCLUDE_SUFFIXES)


def build(folder: str) -> tuple[str, int, int]:
    """Zip ae/<folder> into ae/<folder>.zip, nested under <folder>/."""
    src = os.path.join(AE_DIR, folder)
    dest = os.path.join(AE_DIR, folder + ".zip")

    entries = 0
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(src):
            dirs[:] = sorted(d for d in dirs if not should_skip_dir(d))
            for fname in sorted(files):
                if should_skip_file(fname):
                    continue
                full = os.path.join(root, fname)
                # Nest everything under the project folder so unzipping
                # produces a directory, not a pile of loose files.
                rel = os.path.relpath(full, AE_DIR).replace(os.sep, "/")
                zf.write(full, rel)
                entries += 1

    return dest, entries, os.path.getsize(dest)


def main() -> int:
    if not os.path.isdir(AE_DIR):
        print(f"error: no {AE_DIR}/ directory here; run from the repo root", file=sys.stderr)
        return 1

    folders = sorted(
        d for d in os.listdir(AE_DIR)
        if os.path.isdir(os.path.join(AE_DIR, d)) and not should_skip_dir(d)
    )
    if not folders:
        print(f"error: no project folders found under {AE_DIR}/", file=sys.stderr)
        return 1

    for folder in folders:
        dest, entries, size = build(folder)
        print(f"{dest:<48} {entries:>3} files  {size/1024:>8.1f} KB")

    print(f"\n{len(folders)} bundles rebuilt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
