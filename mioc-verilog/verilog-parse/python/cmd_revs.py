# cmd_revs.py — aligned output + robust register
# === VNLT REV ===
# file: python/cmd_revs.py
# rev:  2025-10-03  r5  by:ediaz  tag:revs
# note: 'revs' command — scans for VNLT REV headers and prints "<relpath>  <rev-line>" aligned
# === /VNLT REV ===

from __future__ import annotations
import os
import re
from typing import List, Optional, Iterable, Tuple

COMMAND = "revs"
HELP = "revs — print '<path>  <rev-line>' for files containing a VNLT REV header"
DETAIL = """Usage:
  revs

Scans the current working directory for VNLT REV header blocks in common text/code
files and prints a sorted, aligned list of:
  <relative-path>  <rev: ...>

Recognized header forms:

Python / text (hash comments):
  # === VNLT REV ===
  # file: ...
  # rev:  ...
  # note: ...
  # === /VNLT REV ===

HTML (comment blocks):
  <!-- === VNLT REV === -->
  <!-- file: ... -->
  <!-- rev:  ... -->
  <!-- note: ... -->
  <!-- === /VNLT REV === -->
"""

EXTS = {".py", ".txt", ".md", ".html", ".htm"}

PY_BLOCK_RE = re.compile(
    r"(?ms)^#\s*===\s*VNLT\s+REV\s*===\s*$"
    r"(.*?)"
    r"^#\s*===\s*/VNLT\s+REV\s*===\s*$"
)
PY_REV_LINE_RE = re.compile(r"(?mi)^\s*#\s*rev:\s*(.*)\s*$")

HTML_BLOCK_RE = re.compile(
    r"(?ms)^\s*<!--\s*===\s*VNLT\s+REV\s*===\s*-->\s*$"
    r"(.*?)"
    r"^\s*<!--\s*===\s*/VNLT\s+REV\s*===\s*-->\s*$"
)
HTML_REV_LINE_RE = re.compile(r"(?mis)<!--\s*rev:\s*(.*?)\s*-->")

SKIP_DIRS = {".git", ".hg", ".svn", "__pycache__", "node_modules", "dist", "build", ".venv", "venv"}


def _iter_files(root: str) -> Iterable[str]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in EXTS:
                yield os.path.join(dirpath, fn)


def _read_text(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None


def _extract_rev(text: str) -> Optional[str]:
    m = PY_BLOCK_RE.search(text)
    if m:
        block = m.group(1)
        m2 = PY_REV_LINE_RE.search(block)
        if m2:
            return m2.group(1).strip()
    m = HTML_BLOCK_RE.search(text)
    if m:
        block = m.group(1)
        m2 = HTML_REV_LINE_RE.search(block)
        if m2:
            return m2.group(1).strip()
    # Fallback: a single-line "rev:" anywhere
    m = re.search(r"(?mi)^\s*(?:#|<!--)?\s*rev:\s*(.*?)(?:-->)?\s*$", text)
    if m:
        return m.group(1).strip()
    return None


def run(args: List[str], interp) -> dict:
    root = os.getcwd()
    pairs: List[Tuple[str, str]] = []

    for path in _iter_files(root):
        text = _read_text(path)
        if not text:
            continue
        rev = _extract_rev(text)
        if rev:
            rel = os.path.relpath(path, root)
            pairs.append((rel, rev))

    pairs.sort(key=lambda t: t[0].lower())
    if not pairs:
        return {"__raw": ""}

    width = max(len(rel) for rel, _ in pairs)
    lines = [f"{rel.ljust(width)}  {rev}" for (rel, rev) in pairs]
    return {"__raw": "\n".join(lines) + "\n"}


def register(registry) -> None:
    """
    Be robust to different registry APIs.
    Tries: register(name, func, help, detail) → add_command(...) → add(...).
    """
    add = getattr(registry, "register", None) or getattr(registry, "add_command", None) or getattr(registry, "add", None)
    if add is None:
        raise AttributeError("CommandRegistry has no 'register' or 'add_command' or 'add'")
    add(COMMAND, run, HELP, DETAIL)
