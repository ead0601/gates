# cmd_revs.py
# === VNLT REV ===
# file: python/cmd_revs.py
# rev:  2025-10-03  r2  by:ediaz  tag:revs
# note: 'revs' command — scans for VNLT REV headers and prints "<relpath>  <rev-line>"
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
files and prints a sorted list of:
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

# File extensions we scan
EXTS = {".py", ".txt", ".md", ".html", ".htm"}

# Regex for Python/text style block
PY_BLOCK_RE = re.compile(
    r"(?ms)^#\s*===\s*VNLT\s+REV\s*===\s*$"
    r"(.*?)"
    r"^#\s*===\s*/VNLT\s+REV\s*===\s*$"
)

PY_REV_LINE_RE = re.compile(r"(?mi)^\s*#\s*rev:\s*(.*)\s*$")

# Regex for HTML comment style block
HTML_BLOCK_RE = re.compile(
    r"(?ms)^\s*<!--\s*===\s*VNLT\s+REV\s*===\s*-->\s*$"
    r"(.*?)"
    r"^\s*<!--\s*===\s*/VNLT\s+REV\s*===\s*-->\s*$"
)

HTML_REV_LINE_RE = re.compile(r"(?mis)<!--\s*rev:\s*(.*?)\s*-->")

SKIP_DIRS = {".git", ".hg", ".svn", "__pycache__", "node_modules", "dist", "build", ".venv", "venv"}


def _iter_files(root: str) -> Iterable[str]:
    for dirpath, dirnames, filenames in os.walk(root):
        # prune
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
    # Try Python/text style
    m = PY_BLOCK_RE.search(text)
    if m:
        block = m.group(1)
        m2 = PY_REV_LINE_RE.search(block)
        if m2:
            return m2.group(1).strip()

    # Try HTML style
    m = HTML_BLOCK_RE.search(text)
    if m:
        block = m.group(1)
        m2 = HTML_REV_LINE_RE.search(block)
        if m2:
            return m2.group(1).strip()

    # Fallback: single-line "rev:" anywhere
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
    lines = [f"{rel}  {rev}" for (rel, rev) in pairs]
    out = ("\n".join(lines) + ("\n" if lines else ""))
    return {"__raw": out}


def register(registry) -> None:
    """
    Be robust to different registry APIs.
    Prefer registry.register(name, func, help, detail) if present,
    else try registry.add_command(name, func, help, detail).
    """
    add = getattr(registry, "register", None) or getattr(registry, "add_command", None)
    if add is None:
        raise AttributeError("CommandRegistry has no 'register' or 'add_command'")
    add(COMMAND, run, HELP, DETAIL)
