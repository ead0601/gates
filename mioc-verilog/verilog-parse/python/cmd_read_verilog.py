from pathlib import Path
from typing import List, Dict
from registry import CommandRegistry, REG
from core import Interpreter
from builders import build_celllib, build_netgraph

def _parse_manifest(path: Path) -> Dict[str, List[str] | str]:
    base = path.parent
    cfg: Dict[str, List[str] | str] = {"rtl": [], "components": [], "assigns": []}
    for ln, raw in enumerate(path.read_text(errors="ignore").splitlines(), start=1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if ":" not in s:
            raise ValueError(f"line {ln}: missing ':' — {raw}")
        key, val = s.split(":", 1)
        key = key.strip().lower()
        val = val.strip()
        if key in ("rtl","components","assigns"):
            p = (base / val).resolve()
            cfg[key].append(str(p))
        elif key in ("top","seq_cells"):
            cfg[key] = val
        else:
            pass
    return cfg

def _handler(args: List[str], interp: Interpreter):
    if not args or args[0] != "verilog" or len(args) < 2:
        return {"__raw": "Usage: read verilog <manifest.lst>\n"}
    manifest = Path(args[1]).resolve()
    if not manifest.exists():
        return {"__raw": f"[read] manifest not found: {manifest}\n"}

    try:
        cfg = _parse_manifest(manifest)
    except Exception as e:
        return {"__raw": f"[read] manifest error: {e}\n"}

    top = str(cfg.get("top") or "").strip()
    if not top:
        return {"__raw": "[read] manifest missing 'top:'\n"}
    rtl = cfg.get("rtl", [])  # type: ignore
    comps = cfg.get("components", [])  # type: ignore
    assigns = cfg.get("assigns", [])  # type: ignore
    seq = (cfg.get("seq_cells") or "").strip()
    seq_cells = [s.strip() for s in seq.split(",")] if seq else []

    missing = []
    for f in rtl + comps + assigns:
        if not Path(f).exists():
            missing.append(f)
    if missing:
        lines = ["[read] missing files:"] + [f"  - {m}" for m in missing]
        lines.append("Fix the paths in your manifest (paths are resolved relative to the manifest).")
        return {"__raw": "\n".join(lines) + "\n"}

    if not rtl:
        return {"__raw": "[read] manifest has no 'rtl:' entries\n"}
    if not comps:
        return {"__raw": "[read] manifest has no 'components:' entries\n"}

    try:
        celllib = build_celllib(rtl, seq_cells)
    except Exception as e:
        return {"__raw": f"[read] step1(build_celllib) failed: {e}\n"}

    try:
        netgraph = build_netgraph(celllib, comps, assigns, top)
    except Exception as e:
        return {"__raw": f"[read] step2(build_netgraph) failed: {e}\n"}

    interp.load_celllib_graph(celllib, netgraph)
    # Stash manifest info for 'list files'
    try:
        interp.manifest_info = {
            'rtl': rtl,
            'components': comps,
            'assigns': assigns,
            'top': top,
            'seq_cells': seq_cells,
        }
    except Exception:
        pass
    cells = len((celllib.get("cells") or {}))
    insts = len(netgraph.get("instances") or [])
    nets  = len(netgraph.get("nets") or {})
    tin   = len(netgraph.get("top",{}).get("inputs",[]))
    tout  = len(netgraph.get("top",{}).get("outputs",[]))
    return {"__raw": f"[read] top={top} cells={cells} instances={insts} nets={nets} top_in={tin} top_out={tout}\n"}

SUMMARY = "read verilog <manifest.lst> — build & load design (no extra files)"
DETAIL = """Usage:
  read verilog <manifest.lst>

Description:
  Integrates Step-1 and Step-2 in-process:
    - Parses RTL files to build the cell library (pin directions, sequential marks).
    - Parses components (structural netlist) and assigns to build the net graph.
    - Loads both into the active session (no intermediate files).

Manifest keys:
  top: <top_module_name>                 # required
  seq_cells: <sequential_cell_type>      # e.g., mioc_flop (comma-separated allowed)
  rtl: <path to RTL .v>                  # multiple lines allowed
  components: <path to structural .v>    # multiple lines allowed
  assigns:    <path to assigns .v>       # optional, multiple lines allowed
"""

def register(reg: CommandRegistry):
    reg.add_command("read", _handler, SUMMARY, DETAIL)

if REG:
    register(REG)
