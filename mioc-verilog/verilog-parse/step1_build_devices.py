#!/usr/bin/env python3
"""
Step 1: Build device objects + cell library from RTL headers.

NEW: Supports a list file via --rtl-list that may contain comments and blanks.
      - Lines may contain paths or globs.
      - Comments starting with '#' or '//' are stripped (inline or whole line).
      - Blank lines are ignored.

Usage examples:
  python step1_build_devices.py \
      --rtl-list /mnt/data/verilog_rtl.lst \
      --out-devices ./devices \
      --out-celllib ./celllib.json \
      --seq-cells mioc_flop

  # You can still pass individual files/globs too:
  python step1_build_devices.py \
      --rtl "/mnt/data/mioc_*_rtl.v" \
      --out-devices ./devices \
      --out-celllib ./celllib.json

What it does:
  - Parses each *_rtl.v for `module <name> ... endmodule`
  - Extracts port directions (input/output) with resilient parsing
  - Classifies cells as 'seq' if name in --seq-cells OR contains 'flop' (case-insensitive), else 'comb'
  - Emits celllib.json
  - Emits one Python file per device type in out-devices/
"""

"""
python3 step1_build_devices.py --rtl-list "./verilog_rtl.lst"   --out-devices ./devices   --out-celllib ./celllib.json   --seq-cells mioc_flop
"""


import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set

MODULE_RE = re.compile(r'module\s+([A-Za-z_]\w*)\s*\(', re.M)
ENDMODULE_RE = re.compile(r'\bendmodule\b', re.M)
# Matches e.g. "input wire [3:0] a, b;" or "output logic z;"
DIR_DECL_RE = re.compile(
    r'(?P<dir>\binput\b|\boutput\b)\s*'
    r'(?:\bwire\b|\blogic\b|\breg\b|\bsigned\b|\btri\b|\btri0\b|\btri1\b|\bsupply0\b|\bsupply1\b|'
    r'\bwand\b|\bwor\b|\bbit\b|\bvar\b|\buwire\b|\btriand\b|\btrior\b|\btrireg\b|\bbyte\b|'
    r'\bshortint\b|\bint\b|\blongint\b|\btime\b|\bInteger\b|\breal\b|\brealtime\b|\bshortreal\b|'
    r'\(\*[^*]*\*\)\s*)*'  # allow attributes & types repeatedly
    r'(?:\[[^\]]+\]\s*)?'  # optional ranges
    r'(?P<names>[^;]+);',  # names until semicolon
    re.IGNORECASE | re.M
)

IDENT_RE = re.compile(r'[A-Za-z_]\w*$')

def strip_line_comments(text: str) -> str:
    # Remove // comments; keep block comments
    return re.sub(r'//.*', '', text)

def find_modules(text: str) -> List[Tuple[str, int, int]]:
    """Return list of (name, start_idx, end_idx) for each module block."""
    pos = 0
    mods = []
    while True:
        m = MODULE_RE.search(text, pos)
        if not m:
            break
        name = m.group(1)
        start = m.start()
        e = ENDMODULE_RE.search(text, m.end())
        if not e:
            raise ValueError(f"Could not find 'endmodule' for module {name}")
        end = e.end()
        mods.append((name, start, end))
        pos = end
    return mods

def parse_dir_ports(module_src: str) -> Tuple[List[str], List[str]]:
    """
    Return (inputs, outputs) discovered within the module.
    Accepts declarations anywhere between module ... endmodule.
    """
    txt = strip_line_comments(module_src)
    inputs: List[str] = []
    outputs: List[str] = []

    for md in DIR_DECL_RE.finditer(txt):
        direction = md.group('dir').lower()
        names_part = md.group('names')
        tokens = []
        for raw in names_part.split(','):
            name = raw.strip()
            # Drop any remaining ranges and array indices: foo[3:0] -> foo
            name = re.sub(r'\[[^\]]+\]', '', name).strip()
            # Keep the last identifier token
            parts = re.split(r'\s+', name)
            candidate = parts[-1] if parts else ''
            if candidate:
                tokens.append(candidate)

        # Unique within this declaration, keep order
        seen: Set[str] = set()
        clean_names: List[str] = []
        for t in tokens:
            if IDENT_RE.match(t) and t not in seen:
                seen.add(t)
                clean_names.append(t)

        if direction == 'input':
            inputs.extend(clean_names)
        else:
            outputs.extend(clean_names)

    def dedupe(seq: List[str]) -> List[str]:
        s: Set[str] = set()
        out: List[str] = []
        for x in seq:
            if x not in s:
                s.add(x)
                out.append(x)
        return out

    return dedupe(inputs), dedupe(outputs)

def classify_category(name: str, explicit_seq: Set[str]) -> str:
    lname = name.lower()
    if name in explicit_seq or 'flop' in lname:
        return 'seq'
    return 'comb'

def build_cell_entries(rtl_files: List[Path], explicit_seq: Set[str]) -> Dict[str, Dict]:
    cells: Dict[str, Dict] = {}
    for p in rtl_files:
        try:
            text = p.read_text(errors='ignore')
        except Exception as e:
            print(f"[WARN] Could not read {p}: {e}", file=sys.stderr)
            continue
        mods = find_modules(text)
        if not mods:
            print(f"[WARN] No module found in {p}", file=sys.stderr)
            continue
        for name, s, e in mods:
            body = text[s:e]
            ins, outs = parse_dir_ports(body)
            if not ins and not outs:
                print(f"[WARN] No ports found for module {name} in {p}", file=sys.stderr)
                continue
            cat = classify_category(name, explicit_seq)
            inter = set(ins) & set(outs)
            if inter:
                raise ValueError(f"Inputs/Outputs overlap in {name}: {sorted(inter)}")
            if not outs:
                print(f"[WARN] Module {name} has no outputs.", file=sys.stderr)
            cells[name] = {
                "category": cat,
                "inputs": ins,
                "outputs": outs,
                "attrs": {}
            }
    return cells

def write_celllib(celllib_path: Path, cells: Dict[str, Dict]) -> None:
    data = {"version": 1, "cells": dict(sorted(cells.items(), key=lambda kv: kv[0]))}
    celllib_path.write_text(json.dumps(data, indent=2))
    print(f"[OK] Wrote celllib: {celllib_path}")

TEMPLATE_DEVICE_PY = '''"""
Auto-generated device metadata for {name}.
"""
TYPE_NAME = "{name}"
INPUT_PINS = {inputs}
OUTPUT_PINS = {outputs}
IS_SEQUENTIAL = {is_seq}
ATTRS = {attrs}

class {class_name}:
    type_name = TYPE_NAME
    input_pins = tuple(INPUT_PINS)
    output_pins = tuple(OUTPUT_PINS)
    is_sequential = IS_SEQUENTIAL
    attrs = dict(ATTRS)
'''

def safe_class_name(name: str) -> str:
    # Convert to a valid Python class name, e.g., mioc_nand2 -> MiocNand2
    parts = re.split(r'[_\W]+', name)
    return ''.join(s.capitalize() for s in parts if s)

def write_device_files(devices_dir: Path, cells: Dict[str, Dict]) -> None:
    devices_dir.mkdir(parents=True, exist_ok=True)
    init_lines = []
    for name, meta in sorted(cells.items(), key=lambda kv: kv[0]):
        is_seq = (meta.get("category") == "seq")
        code = TEMPLATE_DEVICE_PY.format(
            name=name,
            inputs=json.dumps(meta.get("inputs", []), indent=2),
            outputs=json.dumps(meta.get("outputs", []), indent=2),
            is_seq="True" if is_seq else "False",
            attrs=json.dumps(meta.get("attrs", {}), indent=2),
            class_name=safe_class_name(name)
        )
        outp = devices_dir / f"{name}.py"
        outp.write_text(code)
        init_lines.append(f"from .{name} import {safe_class_name(name)}  # noqa")
        print(f"[OK] Wrote device file: {outp}")
    # __init__.py
    (devices_dir / "__init__.py").write_text("# Auto-generated device package\n" + "\n".join(init_lines) + "\n")
    print(f"[OK] Wrote {devices_dir/'__init__.py'}")

def expand_glob_or_path(token: str) -> List[Path]:
    """Expand a single token which may be a literal path or a glob."""
    token = token.strip()
    if not token:
        return []
    # On Windows, glob characters may be present in normal paths less frequently; we use glob if wildcard present
    if any(ch in token for ch in "*?[]"):
        return list(Path().glob(token))
    return [Path(token)]

def load_rtl_paths_from_list(list_path: Path) -> List[Path]:
    """
    Load a list of paths/globs from a text file, stripping comments and blanks.
    Supports inline and full-line comments starting with '#' or '//'.
    """
    if not list_path.exists():
        raise FileNotFoundError(f"RTL list file not found: {list_path}")
    paths: List[Path] = []
    for raw in list_path.read_text(errors='ignore').splitlines():
        line = raw.strip()
        if not line:
            continue
        # strip inline comments
        # find earliest occurrence of '#' or '//' and cut there
        cut_positions = []
        hidx = line.find('#')
        if hidx != -1:
            cut_positions.append(hidx)
        s2 = line.find('//')
        if s2 != -1:
            cut_positions.append(s2)
        if cut_positions:
            cut_at = min(cut_positions)
            line = line[:cut_at].strip()
            if not line:
                continue
        # allow quoted paths
        if (line.startswith('"') and line.endswith('"')) or (line.startswith("'") and line.endswith("'")):
            line = line[1:-1]
        # expand globs / normalize
        expanded = expand_glob_or_path(line)
        if not expanded:
            print(f"[WARN] No match for entry in list: {line}", file=sys.stderr)
        for p in expanded:
            if p.exists():
                paths.append(p)
            else:
                print(f"[WARN] Path not found: {p}", file=sys.stderr)
    # de-dup while preserving order
    seen: Set[Path] = set()
    uniq: List[Path] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq

def main():
    ap = argparse.ArgumentParser(description="Step 1: Build device objects and celllib.json from RTL headers.")
    src = ap.add_mutually_exclusive_group(required=False)
    src.add_argument("--rtl", nargs="+", help="Paths/globs to *_rtl.v files")
    src.add_argument("--rtl-list", help="Text file containing one path or glob per line (comments allowed)")
    ap.add_argument("--out-devices", required=True, help="Output directory for per-device Python files")
    ap.add_argument("--out-celllib", required=True, help="Output celllib.json path")
    ap.add_argument("--seq-cells", default="", help="Comma-separated list of sequential cell type names (optional)")
    args = ap.parse_args()

    rtl_files: List[Path] = []

    if args.rtl_list:
        rtl_files = load_rtl_paths_from_list(Path(args.rtl_list))
    if args.rtl:
        # also accept direct files/globs; combine with list entries if both provided
        for pat in args.rtl:
            expanded = expand_glob_or_path(pat)
            rtl_files.extend(expanded)

    # Filter to existing files and de-dup
    rtl_files = [p for p in rtl_files if p.exists()]
    seen: Set[Path] = set()
    uniq_files: List[Path] = []
    for p in rtl_files:
        if p.resolve() not in seen:
            seen.add(p.resolve())
            uniq_files.append(p)
    rtl_files = uniq_files

    if not rtl_files:
        print("[ERR] No RTL files found. Provide --rtl-list or --rtl.", file=sys.stderr)
        sys.exit(1)

    explicit_seq: Set[str] = set([s for s in (x.strip() for x in args.seq_cells.split(",")) if s])

    # Build cells
    cells = build_cell_entries(rtl_files, explicit_seq)
    if not cells:
        print("[ERR] No cells extracted.", file=sys.stderr)
        sys.exit(2)

    # Write outputs
    out_devices = Path(args.out_devices)
    out_celllib = Path(args.out_celllib)
    write_celllib(out_celllib, cells)
    write_device_files(out_devices, cells)
    print("[DONE] Step 1 complete.")

if __name__ == "__main__":
    main()
